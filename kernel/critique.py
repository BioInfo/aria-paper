"""The CRITIQUE verb — cross-model adversarial review.

The architectural commitment in the paper (§3.3) is that the critic runs a
*different* model family from the producer. The deployed system used Kimi K2
as producer and GLM-5 as critic; the cross-family setup generated FLAG or
WARNING on 85% of completed experiments (164 of 193 in the sample, 90.6% if
you exclude INFO from the denominator). Same-family critique would have
produced higher PASS rates by training-data correlation.

The critic emits one of four verdicts:
    PASS    — no issues found; result is usable
    WARNING — usable with caveats (calibration, scope, missing controls)
    FLAG    — usable only after fix; a follow-up pool entry is suggested
    INFO    — meta-observation about the system, not the result itself

Production critiques are written to `share/from_critic/<verdict>_*.yaml` so
the producer can pick them up on the next iteration. The reference impl
returns a verdict dict directly.
"""
from __future__ import annotations

from typing import Any, Protocol


class CriticClient(Protocol):
    """A cross-model LLM client that returns a verdict for an analysis."""

    def verdict(self, analysis: dict[str, Any]) -> dict[str, Any]: ...


def critique_result(
    analysis: dict[str, Any],
    *,
    client: CriticClient | None = None,
) -> dict[str, Any]:
    """Adversarially review an analysis dict and return a verdict.

    Returns:
        A dict with at minimum {"verdict": str, "rationale": str}. Production
        critic clients also emit `suggested_followups: list[PoolEntry]` and
        `confidence_score: float`.
    """
    if client is None:
        # Reference noop verdict — production critics are wired to a real LLM
        return {
            "verdict": "PASS" if analysis.get("status") == "completed" else "INFO",
            "rationale": "Reference critic returns PASS for completed runs and INFO otherwise.",
            "confidence_score": 0.0,
        }
    return client.verdict(analysis)
