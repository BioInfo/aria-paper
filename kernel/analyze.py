"""The ANALYZE verb — turn a result into a structured insight.

ANALYZE reads a RunResult, inspects the artifacts, computes the metrics that
matter for the experiment's target, and writes back into the corpus as an
insight markdown file plus structured fields on the pool entry. The
production deployments emit:
    - corpus/insights/<domain>/<entry_id>_summary.md
    - corpus/research_registry.json (a flat index for grep + LLM context)

This reference implementation exposes the structural shape.
"""
from __future__ import annotations

from typing import Any

from .execute import RunResult


def analyze_result(result: RunResult) -> dict[str, Any]:
    """Extract metrics + structured fields from a run result.

    Returns:
        A dict the kernel attaches to the pool entry's `meta["analysis"]`.
        Keys are intentionally generic so a domain-specific subclass can
        extend (e.g. add `pearson_r`, `mae`, `auc` for biomarker regression).
    """
    return {
        "where": result.where,
        "status": result.status,
        "duration_min": result.duration_min,
        "cost_usd": result.cost_usd,
        "has_artifacts": bool(result.artifacts),
        "error": result.error,
    }
