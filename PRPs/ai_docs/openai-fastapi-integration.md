# OpenAI + FastAPI Production Integration Guide

## Async Patterns and Error Handling

This guide provides production-ready patterns for integrating OpenAI with FastAPI, focusing on async operations, error handling, and best practices.

## Core Integration Pattern

### 1. Client Initialization

```python
from openai import AsyncOpenAI
from typing import Optional
import os

class OpenAIService:
    """Service class for OpenAI operations with proper lifecycle management"""

    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None

    async def get_client(self) -> AsyncOpenAI:
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            api_key = os.getenv("CLAUDELENS_OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not configured")
            self._client = AsyncOpenAI(api_key=api_key)
        return self._client

    async def close(self):
        """Cleanup client resources"""
        if self._client:
            await self._client.close()
            self._client = None
```

### 2. FastAPI Dependency Injection

```python
from fastapi import Depends, FastAPI
from contextlib import asynccontextmanager

# Global service instance
openai_service = OpenAIService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    yield
    # Cleanup on shutdown
    await openai_service.close()

app = FastAPI(lifespan=lifespan)

# Dependency for routes
async def get_openai_service() -> OpenAIService:
    return openai_service
```

### 3. Error Handling Patterns

```python
from fastapi import HTTPException
from openai import (
    APIError,
    APIConnectionError,
    RateLimitError,
    APITimeoutError,
    AuthenticationError
)
import logging

logger = logging.getLogger(__name__)

async def safe_openai_call(service: OpenAIService, **kwargs):
    """Wrapper for OpenAI API calls with comprehensive error handling"""
    try:
        client = await service.get_client()
        response = await client.chat.completions.create(**kwargs)
        return response

    except AuthenticationError as e:
        logger.error(f"OpenAI authentication failed: {e}")
        raise HTTPException(
            status_code=401,
            detail="AI service authentication failed. Please check configuration."
        )

    except RateLimitError as e:
        logger.warning(f"OpenAI rate limit hit: {e}")
        # Extract retry-after from headers if available
        retry_after = getattr(e, 'retry_after', 60)
        raise HTTPException(
            status_code=429,
            detail=f"AI service rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )

    except APITimeoutError as e:
        logger.error(f"OpenAI timeout: {e}")
        raise HTTPException(
            status_code=504,
            detail="AI service timeout. Please try again with a shorter request."
        )

    except APIConnectionError as e:
        logger.error(f"OpenAI connection error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to AI service. Please try again later."
        )

    except APIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"AI service error: {str(e)}"
        )

    except Exception as e:
        logger.exception(f"Unexpected error in OpenAI call: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )
```

### 4. Streaming Response Pattern

```python
from fastapi import StreamingResponse
from typing import AsyncGenerator
import json

async def stream_openai_response(
    service: OpenAIService,
    messages: list,
    model: str = "gpt-4"
) -> AsyncGenerator[str, None]:
    """Stream OpenAI responses using Server-Sent Events format"""
    try:
        client = await service.get_client()
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=0.7
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                # Format as Server-Sent Event
                data = {
                    "content": chunk.choices[0].delta.content,
                    "type": "content"
                }
                yield f"data: {json.dumps(data)}\n\n"

        # Send completion event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        error_data = {"type": "error", "message": str(e)}
        yield f"data: {json.dumps(error_data)}\n\n"

@app.post("/generate-stream")
async def generate_stream(
    request: GenerateRequest,
    service: OpenAIService = Depends(get_openai_service)
):
    """Endpoint for streaming AI responses"""
    return StreamingResponse(
        stream_openai_response(service, request.messages),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
```

### 5. Retry Logic with Tenacity

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_log,
    after_log
)
import logging

logger = logging.getLogger(__name__)

class OpenAIServiceWithRetry(OpenAIService):
    """Enhanced service with automatic retry logic"""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((APIConnectionError, APITimeoutError)),
        before=before_log(logger, logging.DEBUG),
        after=after_log(logger, logging.DEBUG)
    )
    async def generate_with_retry(self, **kwargs):
        """Generate completion with automatic retry on transient errors"""
        client = await self.get_client()
        return await client.chat.completions.create(**kwargs)
```

### 6. Token Counting and Validation

```python
import tiktoken
from typing import List, Dict

class TokenManager:
    """Manage token counting and limits"""

    def __init__(self, model: str = "gpt-4"):
        self.model = model
        self.encoding = tiktoken.encoding_for_model(model)
        self.max_tokens = self._get_model_limits()

    def _get_model_limits(self) -> Dict[str, int]:
        """Get token limits for different models"""
        limits = {
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384
        }
        return limits.get(self.model, 4096)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))

    def count_messages_tokens(self, messages: List[Dict]) -> int:
        """Count tokens in messages format"""
        total = 0
        for message in messages:
            total += 4  # Message overhead
            for key, value in message.items():
                total += self.count_tokens(str(value))
        total += 2  # Reply overhead
        return total

    def validate_request(self, messages: List[Dict], max_completion: int = 1000) -> bool:
        """Validate if request fits within token limits"""
        prompt_tokens = self.count_messages_tokens(messages)
        total_tokens = prompt_tokens + max_completion

        if total_tokens > self.max_tokens:
            raise ValueError(
                f"Request exceeds token limit: {total_tokens} > {self.max_tokens}"
            )
        return True
```

### 7. Cost Tracking

```python
from decimal import Decimal
from datetime import datetime

class CostTracker:
    """Track OpenAI API usage costs"""

    # Pricing per 1K tokens (as of 2024)
    PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.001, "output": 0.002}
    }

    async def calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> Decimal:
        """Calculate cost for API call"""
        pricing = self.PRICING.get(model, self.PRICING["gpt-3.5-turbo"])

        input_cost = Decimal(prompt_tokens) / 1000 * Decimal(pricing["input"])
        output_cost = Decimal(completion_tokens) / 1000 * Decimal(pricing["output"])

        return input_cost + output_cost

    async def log_usage(
        self,
        db,
        user_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: Decimal
    ):
        """Log usage to database"""
        await db.ai_usage_logs.insert_one({
            "user_id": user_id,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost": float(cost),
            "timestamp": datetime.utcnow()
        })
```

### 8. Complete FastAPI Endpoint Example

```python
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=5000)
    max_tokens: int = Field(default=500, ge=1, le=2000)
    temperature: float = Field(default=0.7, ge=0, le=2)

class GenerateResponse(BaseModel):
    content: str
    tokens_used: int
    cost: float

@app.post("/generate", response_model=GenerateResponse)
async def generate(
    request: GenerateRequest,
    service: OpenAIService = Depends(get_openai_service),
    db=Depends(get_database)
):
    """Generate AI response with full error handling and cost tracking"""

    # Initialize helpers
    token_manager = TokenManager("gpt-4")
    cost_tracker = CostTracker()

    # Prepare messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": request.prompt}
    ]

    # Validate token limits
    try:
        token_manager.validate_request(messages, request.max_tokens)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Make API call with error handling
    response = await safe_openai_call(
        service,
        model="gpt-4",
        messages=messages,
        max_tokens=request.max_tokens,
        temperature=request.temperature
    )

    # Calculate cost
    cost = await cost_tracker.calculate_cost(
        "gpt-4",
        response.usage.prompt_tokens,
        response.usage.completion_tokens
    )

    # Log usage
    await cost_tracker.log_usage(
        db,
        user_id="current_user_id",  # Get from auth
        model="gpt-4",
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        cost=cost
    )

    return GenerateResponse(
        content=response.choices[0].message.content,
        tokens_used=response.usage.total_tokens,
        cost=float(cost)
    )
```

## Best Practices Summary

1. **Always use AsyncOpenAI** for FastAPI integration
2. **Implement comprehensive error handling** for all API failure modes
3. **Count tokens before API calls** to prevent errors and control costs
4. **Use dependency injection** for service management
5. **Implement retry logic** for transient failures
6. **Track costs and usage** for monitoring and billing
7. **Stream responses** for better UX on long generations
8. **Clean up resources** in application shutdown
9. **Validate all inputs** before sending to OpenAI
10. **Log all API interactions** for debugging and auditing
