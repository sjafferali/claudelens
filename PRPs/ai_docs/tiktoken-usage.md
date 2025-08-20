# Tiktoken Usage Guide for Token Counting

## Model Encodings and Performance Optimization

Tiktoken is OpenAI's fast BPE tokenizer for counting tokens accurately before API calls.

## Installation

```bash
pip install tiktoken
```

## Model Encodings Reference

### Current Model Encodings (2024-2025)

```python
MODEL_ENCODINGS = {
    # GPT-4 models
    "gpt-4": "cl100k_base",
    "gpt-4-32k": "cl100k_base",
    "gpt-4-turbo": "cl100k_base",
    "gpt-4-turbo-preview": "cl100k_base",

    # GPT-3.5 models
    "gpt-3.5-turbo": "cl100k_base",
    "gpt-3.5-turbo-16k": "cl100k_base",

    # Text embedding models
    "text-embedding-ada-002": "cl100k_base",
    "text-embedding-3-small": "cl100k_base",
    "text-embedding-3-large": "cl100k_base",
}

MODEL_TOKEN_LIMITS = {
    "gpt-4": 8192,
    "gpt-4-32k": 32768,
    "gpt-4-turbo": 128000,
    "gpt-3.5-turbo": 4096,
    "gpt-3.5-turbo-16k": 16384,
}
```

## Basic Token Counting

```python
import tiktoken

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens for a given text and model"""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base for unknown models
        encoding = tiktoken.get_encoding("cl100k_base")

    return len(encoding.encode(text))

# Example usage
text = "Hello, how are you today?"
token_count = count_tokens(text, "gpt-4")
print(f"Token count: {token_count}")
```

## Counting Tokens in Chat Messages

```python
def count_message_tokens(messages: list, model: str = "gpt-4") -> int:
    """
    Count tokens in chat completion messages.
    Based on OpenAI's official guidance.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    # Token counts for message formatting
    if model in ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]:
        tokens_per_message = 3  # <|start|>{role}\n{content}<|end|>\n
        tokens_per_name = 1     # If name field is present
    else:
        tokens_per_message = 3
        tokens_per_name = 1

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(str(value)))
            if key == "name":
                num_tokens += tokens_per_name

    num_tokens += 3  # Every reply is primed with <|start|>assistant<|message|>
    return num_tokens

# Example usage
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Write a haiku about coding."}
]
token_count = count_message_tokens(messages, "gpt-4")
print(f"Total tokens: {token_count}")
```

## Performance Optimization Strategies

### 1. Encoding Caching

```python
from functools import lru_cache
import tiktoken

class TokenCounter:
    """Optimized token counter with encoding cache"""

    def __init__(self):
        self._encodings = {}

    def get_encoding(self, model: str):
        """Get cached encoding for model"""
        if model not in self._encodings:
            try:
                self._encodings[model] = tiktoken.encoding_for_model(model)
            except KeyError:
                self._encodings[model] = tiktoken.get_encoding("cl100k_base")
        return self._encodings[model]

    @lru_cache(maxsize=1000)
    def count_cached(self, text: str, model: str = "gpt-4") -> int:
        """Count tokens with LRU cache for repeated texts"""
        encoding = self.get_encoding(model)
        return len(encoding.encode(text))

# Global instance for reuse
token_counter = TokenCounter()
```

### 2. Batch Processing

```python
import asyncio
from typing import List, Tuple

async def count_tokens_batch(
    texts: List[str],
    model: str = "gpt-4"
) -> List[int]:
    """Count tokens for multiple texts efficiently"""
    encoding = tiktoken.encoding_for_model(model)

    async def count_single(text: str) -> int:
        return len(encoding.encode(text))

    # Process in parallel for large batches
    tasks = [count_single(text) for text in texts]
    return await asyncio.gather(*tasks)

# Example usage
texts = ["Hello world", "How are you?", "This is a test"]
counts = await count_tokens_batch(texts)
```

### 3. Approximate Token Counting (Fast)

```python
def estimate_tokens(text: str) -> int:
    """
    Fast approximate token count.
    Rule of thumb: ~4 characters per token for English text.
    Use only when exact count isn't critical.
    """
    # More accurate approximation based on empirical data
    word_count = len(text.split())
    char_count = len(text)

    # Average: 1.3 tokens per word, 4 chars per token
    token_estimate = max(word_count * 1.3, char_count / 4)

    return int(token_estimate * 1.1)  # Add 10% buffer

# Example usage
text = "This is a quick estimation"
approx = estimate_tokens(text)
exact = count_tokens(text)
print(f"Approximate: {approx}, Exact: {exact}")
```

## Token Limit Validation

```python
class TokenValidator:
    """Validate requests against model token limits"""

    def __init__(self, model: str = "gpt-4"):
        self.model = model
        self.encoding = tiktoken.encoding_for_model(model)
        self.max_tokens = MODEL_TOKEN_LIMITS.get(model, 4096)

    def validate_request(
        self,
        messages: list,
        max_completion_tokens: int = 500
    ) -> dict:
        """
        Validate if request fits within token limits.
        Returns validation result with details.
        """
        prompt_tokens = count_message_tokens(messages, self.model)
        total_possible = prompt_tokens + max_completion_tokens

        is_valid = total_possible <= self.max_tokens
        available_for_completion = self.max_tokens - prompt_tokens

        return {
            "is_valid": is_valid,
            "prompt_tokens": prompt_tokens,
            "max_completion_tokens": min(max_completion_tokens, available_for_completion),
            "total_tokens": total_possible,
            "model_limit": self.max_tokens,
            "available_tokens": available_for_completion,
            "error": None if is_valid else f"Exceeds limit by {total_possible - self.max_tokens} tokens"
        }

# Example usage
validator = TokenValidator("gpt-4")
messages = [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Write a story."}
]
result = validator.validate_request(messages, max_completion_tokens=1000)
print(result)
```

## Truncation Strategies

```python
def truncate_to_token_limit(
    text: str,
    max_tokens: int,
    model: str = "gpt-4",
    strategy: str = "end"  # "end", "start", or "middle"
) -> str:
    """
    Truncate text to fit within token limit.
    """
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)

    if len(tokens) <= max_tokens:
        return text

    if strategy == "start":
        # Keep the beginning
        truncated_tokens = tokens[:max_tokens]
    elif strategy == "middle":
        # Remove from middle
        keep_start = max_tokens // 2
        keep_end = max_tokens - keep_start
        truncated_tokens = tokens[:keep_start] + tokens[-keep_end:]
    else:  # "end"
        # Keep the end
        truncated_tokens = tokens[-max_tokens:]

    return encoding.decode(truncated_tokens)

# Example usage
long_text = "This is a very long text " * 100
truncated = truncate_to_token_limit(long_text, 50, strategy="middle")
```

## Streaming Token Counter

```python
class StreamingTokenCounter:
    """Count tokens in streaming responses"""

    def __init__(self, model: str = "gpt-4"):
        self.encoding = tiktoken.encoding_for_model(model)
        self.total_tokens = 0
        self.buffer = ""

    def add_chunk(self, chunk: str) -> int:
        """Add a chunk and return tokens in this chunk"""
        chunk_tokens = len(self.encoding.encode(chunk))
        self.total_tokens += chunk_tokens
        self.buffer += chunk
        return chunk_tokens

    def get_total(self) -> int:
        """Get total tokens counted so far"""
        return self.total_tokens

    def reset(self):
        """Reset counter for new stream"""
        self.total_tokens = 0
        self.buffer = ""

# Example usage with streaming
counter = StreamingTokenCounter("gpt-4")
for chunk in ["Hello", " world", ", how", " are", " you?"]:
    tokens = counter.add_chunk(chunk)
    print(f"Chunk tokens: {tokens}, Total: {counter.get_total()}")
```

## Cost Calculation

```python
def calculate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model: str = "gpt-4"
) -> float:
    """Calculate cost based on token usage"""

    # Pricing per 1K tokens (update as needed)
    PRICING = {
        "gpt-4": {
            "prompt": 0.03,
            "completion": 0.06
        },
        "gpt-4-turbo": {
            "prompt": 0.01,
            "completion": 0.03
        },
        "gpt-3.5-turbo": {
            "prompt": 0.0015,
            "completion": 0.002
        }
    }

    model_pricing = PRICING.get(model, PRICING["gpt-3.5-turbo"])

    prompt_cost = (prompt_tokens / 1000) * model_pricing["prompt"]
    completion_cost = (completion_tokens / 1000) * model_pricing["completion"]

    return round(prompt_cost + completion_cost, 4)

# Example usage
cost = calculate_cost(
    prompt_tokens=500,
    completion_tokens=150,
    model="gpt-4"
)
print(f"Estimated cost: ${cost}")
```

## Performance Tips

1. **Cache encodings**: Don't recreate encoding objects repeatedly
2. **Use batch processing**: Process multiple texts together when possible
3. **Approximate when appropriate**: Use estimation for non-critical counts
4. **Pre-validate lengths**: Check obvious cases before expensive token counting
5. **Stream processing**: Count tokens incrementally for streaming responses

## Common Pitfalls

1. **Different models use different encodings**: Always use the correct model name
2. **Special tokens add overhead**: Account for message formatting tokens
3. **Unicode handling**: Some characters use multiple tokens
4. **Token != word**: One word can be multiple tokens
5. **Model limits include both prompt and completion**: Reserve space for response
