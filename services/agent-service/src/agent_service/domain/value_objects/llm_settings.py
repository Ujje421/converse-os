"""LLM Settings Value Object."""

from pydantic import BaseModel, Field


class LLMSettings(BaseModel):
    """Value object for LLM generation parameters."""
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)
    top_k: int = Field(default=40, ge=1)
    max_tokens: int = Field(default=2048, ge=1)
