"""The DEBUG verb — self-healing failure recovery.

The architectural claim in the paper (§3.5, §6.3, Appendix E.4): a loop that
needs a human to fix every error stops after a week; a loop that recovers
from its own errors runs for months. DEBUG classifies failure modes (preempt,
dependency drift, malformed YAML, training NaN, OOM, degenerate target) and
writes a recovery pool entry describing what to try next.

The deployed system emitted 321 DEBUG verb commits over 50 days. **314 of
them (97.8%) self-healed** — the next non-DEBUG autonomous commit appeared
strictly before any operator commit. The seven that required operator
intervention all clustered in weeks 2-3 and triggered structural code
changes that closed underlying architectural gaps; from week 4 onward the
self-heal rate was 100% across 206 events and 28 days. Median recovery
latency was 8.3 minutes (p95 = 24.6 minutes).

See `evidence/debug_recovery.csv` for the per-event paired data.
"""
from __future__ import annotations

import datetime as dt
import uuid

from .pool import PoolEntry


# Heuristic error-classification table. Production deployments extend this
# with domain-specific failure modes (OOM, NaN-loss, data-loader hang, etc).
FAILURE_CLASSIFIERS: dict[str, str] = {
    "preempted": "preempt",
    "preemption": "preempt",
    "out of memory": "oom",
    "cuda out of memory": "oom",
    "nan": "nan_loss",
    "yaml": "malformed_pool_entry",
    "module not found": "dependency_drift",
    "permission denied": "io_failure",
    "no such file": "io_failure",
    "timeout": "timeout",
    "connection reset": "network",
}


def classify(error: str | None) -> str:
    """Classify an error message into a known failure mode (or 'unknown')."""
    if not error:
        return "unknown"
    err_lower = error.lower()
    for needle, label in FAILURE_CLASSIFIERS.items():
        if needle in err_lower:
            return label
    return "unknown"


def recovery_entry(failed_entry: PoolEntry, error: Exception | str) -> PoolEntry:
    """Build a recovery PoolEntry to follow a failed run.

    The recovery entry inherits the failed entry's domain and parent chain,
    annotates the failure mode, and proposes a concrete next step (the
    production deployments use an LLM to generate the recovery hypothesis;
    the reference implementation emits a structural placeholder).
    """
    err_str = str(error)
    failure_mode = classify(err_str)
    return PoolEntry(
        idea_id=f"recovery_{failed_entry.idea_id}_{uuid.uuid4().hex[:6]}",
        title=f"Recovery from {failed_entry.idea_id}: {failure_mode}",
        hypothesis=(
            f"Re-attempt {failed_entry.idea_id} with adjustment for "
            f"failure mode '{failure_mode}'."
        ),
        evidence=f"Parent entry failed with: {err_str[:200]}",
        domain=failed_entry.domain,
        score=failed_entry.score,  # inherit so the recovery doesn't drop in priority
        status="active",
        parents=[failed_entry.idea_id, *failed_entry.parents],
        meta={
            "recovery_of": failed_entry.idea_id,
            "failure_mode": failure_mode,
            "raw_error": err_str,
            "created": dt.datetime.now(dt.UTC).isoformat(),
        },
    )


def handle_failure(failed_entry: PoolEntry, exc: Exception) -> PoolEntry:
    """Convenience wrapper: classify + build recovery entry from an exception."""
    return recovery_entry(failed_entry, exc)
