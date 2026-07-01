"""Reverse Proxy implementation for API Gateway."""

import httpx
from fastapi import Request, Response, HTTPException
import structlog

logger = structlog.get_logger()

# Async HTTP Client session shared across requests
http_client = httpx.AsyncClient(limits=httpx.Limits(max_keepalive_connections=100, max_connections=500))

async def forward_request(request: Request, target_url: str) -> Response:
    """Forwards the incoming request to the target microservice."""
    
    url = f"{target_url}{request.url.path}?{request.url.query}" if request.url.query else f"{target_url}{request.url.path}"
    
    headers = dict(request.headers)
    # Remove host header to allow httpx to set it for the target
    headers.pop("host", None)
    
    # We might read the body here, but for streaming, we could pass it directly.
    # For simplicity in this example, we'll read it.
    body = await request.body()
    
    try:
        req = http_client.build_request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
        )
        
        response = await http_client.send(req, stream=True)
        
        # Read the content
        content = await response.aread()
        
        # Build FastAPI response
        return Response(
            content=content,
            status_code=response.status_code,
            headers={k: v for k, v in response.headers.items() if k.lower() not in ("content-length", "content-encoding", "transfer-encoding")},
        )
        
    except httpx.RequestError as e:
        logger.error("gateway_proxy_error", error=str(e), target=url)
        raise HTTPException(status_code=502, detail="Bad Gateway")
