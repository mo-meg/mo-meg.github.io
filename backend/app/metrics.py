"""Prometheus metrics (exposed at /metrics)."""

from prometheus_client import Counter, Histogram

CHAT_REQUESTS = Counter("chat_requests_total", "Chat requests by outcome", ["outcome"])
RATE_LIMITED = Counter("chat_rate_limited_total", "Requests rejected by rate limiting", ["scope"])
TOKENS = Counter("gemini_tokens_total", "Gemini tokens consumed", ["kind"])
RETRIEVAL_SECONDS = Histogram("retrieval_seconds", "Retrieval latency (embedding + search)")
GENERATION_SECONDS = Histogram(
    "generation_seconds", "Generation latency (full stream)", buckets=(0.5, 1, 2, 4, 8, 16, 32, 64)
)
RETRIEVED_CHUNKS = Histogram("retrieved_chunks", "Chunks passed to the model", buckets=(0, 1, 2, 3, 4, 6, 8, 12))
