"""Custom Prometheus metrics for RAG orchestration."""
from prometheus_client import Histogram, Counter

# Histogram for RAG stage latencies with buckets tuned around 5s SLO
rag_stage_seconds = Histogram(
    "rag_stage_seconds",
    "Time spent in each RAG pipeline stage",
    labelnames=["stage"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
)

# Counter for resolve outcomes
rag_resolve_total = Counter(
    "rag_resolve_total",
    "Total number of RAG resolve attempts by outcome",
    labelnames=["outcome"],
)
