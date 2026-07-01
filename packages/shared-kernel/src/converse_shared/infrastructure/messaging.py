"""Kafka messaging infrastructure — producer, consumer, and topic management."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any, Callable, Coroutine

import structlog
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError

logger = structlog.get_logger()


class KafkaMessage:
    """Structured Kafka message with metadata."""

    def __init__(
        self,
        topic: str,
        key: str | None = None,
        value: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        partition: int | None = None,
    ) -> None:
        self.topic = topic
        self.key = key
        self.value = value or {}
        self.headers = headers or {}
        self.partition = partition

        # Add standard metadata
        if "message_id" not in self.value:
            self.value["message_id"] = str(uuid.uuid4())
        if "timestamp" not in self.value:
            self.value["timestamp"] = datetime.now(UTC).isoformat()

    def serialize_value(self) -> bytes:
        """Serialize value to JSON bytes."""
        return json.dumps(self.value, default=str).encode("utf-8")

    def serialize_key(self) -> bytes | None:
        """Serialize key to bytes."""
        if self.key is None:
            return None
        return self.key.encode("utf-8")

    def serialize_headers(self) -> list[tuple[str, bytes]]:
        """Serialize headers for Kafka."""
        return [(k, v.encode("utf-8")) for k, v in self.headers.items()]


class KafkaProducerManager:
    """Managed Kafka producer with structured logging and error handling.

    Usage:
        producer = KafkaProducerManager(bootstrap_servers="localhost:9092")
        await producer.initialize()
        await producer.send(KafkaMessage(topic="events", value={"type": "user.created"}))
        await producer.close()
    """

    def __init__(
        self,
        bootstrap_servers: str,
        client_id: str = "converse-producer",
        acks: str = "all",
        retries: int = 3,
        compression_type: str = "gzip",
        max_request_size: int = 1_048_576,  # 1MB
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._client_id = client_id
        self._acks = acks
        self._retries = retries
        self._compression_type = compression_type
        self._max_request_size = max_request_size
        self._producer: AIOKafkaProducer | None = None

    async def initialize(self) -> None:
        """Start the Kafka producer."""
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._bootstrap_servers,
            client_id=self._client_id,
            acks=self._acks,
            compression_type=self._compression_type,
            max_request_size=self._max_request_size,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )
        await self._producer.start()
        logger.info("kafka_producer_initialized", servers=self._bootstrap_servers)

    async def close(self) -> None:
        """Stop the Kafka producer and flush pending messages."""
        if self._producer:
            await self._producer.stop()
            logger.info("kafka_producer_closed")

    async def send(self, message: KafkaMessage) -> None:
        """Send a message to a Kafka topic.

        Args:
            message: The KafkaMessage to send.

        Raises:
            RuntimeError: If the producer is not initialized.
            KafkaError: If the message could not be sent.
        """
        if self._producer is None:
            raise RuntimeError("KafkaProducerManager not initialized.")

        try:
            await self._producer.send_and_wait(
                topic=message.topic,
                key=message.key,
                value=message.value,
                headers=message.serialize_headers() if message.headers else None,
                partition=message.partition,
            )
            logger.debug(
                "kafka_message_sent",
                topic=message.topic,
                key=message.key,
                message_id=message.value.get("message_id"),
            )
        except KafkaError as e:
            logger.error(
                "kafka_send_failed",
                topic=message.topic,
                error=str(e),
            )
            raise

    async def send_batch(self, messages: list[KafkaMessage]) -> None:
        """Send multiple messages as a batch."""
        for message in messages:
            await self.send(message)

    async def health_check(self) -> bool:
        """Check if the Kafka producer is connected."""
        if self._producer is None:
            return False
        try:
            await self._producer.partitions_for("__health_check")
            return True
        except Exception:
            return False


MessageHandler = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


class KafkaConsumerManager:
    """Managed Kafka consumer with message deserialization and error handling.

    Usage:
        consumer = KafkaConsumerManager(
            bootstrap_servers="localhost:9092",
            group_id="auth-service",
            topics=["user.events"],
        )
        consumer.register_handler("user.created", handle_user_created)
        await consumer.start()
    """

    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        topics: list[str],
        auto_offset_reset: str = "earliest",
        enable_auto_commit: bool = False,
        max_poll_records: int = 100,
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._group_id = group_id
        self._topics = topics
        self._auto_offset_reset = auto_offset_reset
        self._enable_auto_commit = enable_auto_commit
        self._max_poll_records = max_poll_records
        self._consumer: AIOKafkaConsumer | None = None
        self._handlers: dict[str, MessageHandler] = {}
        self._running = False

    def register_handler(self, event_type: str, handler: MessageHandler) -> None:
        """Register a handler for a specific event type."""
        self._handlers[event_type] = handler
        logger.debug("kafka_handler_registered", event_type=event_type)

    async def start(self) -> None:
        """Start consuming messages."""
        self._consumer = AIOKafkaConsumer(
            *self._topics,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            auto_offset_reset=self._auto_offset_reset,
            enable_auto_commit=self._enable_auto_commit,
            max_poll_records=self._max_poll_records,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            key_deserializer=lambda k: k.decode("utf-8") if k else None,
        )
        await self._consumer.start()
        self._running = True
        logger.info(
            "kafka_consumer_started",
            topics=self._topics,
            group_id=self._group_id,
        )

    async def stop(self) -> None:
        """Stop consuming messages."""
        self._running = False
        if self._consumer:
            await self._consumer.stop()
            logger.info("kafka_consumer_stopped")

    async def consume(self) -> None:
        """Main consume loop — processes messages and dispatches to handlers."""
        if self._consumer is None:
            raise RuntimeError("Consumer not started.")

        try:
            async for msg in self._consumer:
                try:
                    value = msg.value
                    event_type = value.get("event_type", value.get("type", "unknown"))

                    handler = self._handlers.get(event_type)
                    if handler:
                        await handler(value)
                        logger.debug(
                            "kafka_message_processed",
                            topic=msg.topic,
                            event_type=event_type,
                            partition=msg.partition,
                            offset=msg.offset,
                        )
                    else:
                        logger.warning(
                            "kafka_no_handler",
                            topic=msg.topic,
                            event_type=event_type,
                        )

                    # Manual commit after processing
                    if not self._enable_auto_commit:
                        await self._consumer.commit()

                except Exception as e:
                    logger.error(
                        "kafka_message_processing_error",
                        topic=msg.topic,
                        error=str(e),
                        offset=msg.offset,
                    )
                    # TODO: Send to dead-letter queue
        except Exception as e:
            logger.error("kafka_consume_loop_error", error=str(e))
            raise


# Standard topic names
class Topics:
    """Centralized topic name definitions."""

    USER_EVENTS = "converse.user.events"
    AUTH_EVENTS = "converse.auth.events"
    ORG_EVENTS = "converse.org.events"
    AGENT_EVENTS = "converse.agent.events"
    CONVERSATION_EVENTS = "converse.conversation.events"
    WORKFLOW_EVENTS = "converse.workflow.events"
    WEBHOOK_EVENTS = "converse.webhook.events"
    KNOWLEDGE_EVENTS = "converse.knowledge.events"
    LLM_EVENTS = "converse.llm.events"
    AUDIT_EVENTS = "converse.audit.events"
    BILLING_EVENTS = "converse.billing.events"
    NOTIFICATION_EVENTS = "converse.notification.events"
    ANALYTICS_EVENTS = "converse.analytics.events"
