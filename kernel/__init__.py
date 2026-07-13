"""ARIA — Sustained Autonomous Research Agents in Biomedicine.

Reference implementation of the kernel framework described in the paper:
    "Sustained Autonomous Research Agents in Biomedicine: ARIA, an 18-Week
    Multi-Domain Deployment, and a Cross-Platform Retinal Biomarker Result" (Johnson & Bedworth, 2026).

This package is the minimum surface area for the architectural claims:
    - A six-stage flywheel (DESIGN → RUN → ANALYZE → CRITIQUE → DEBUG → PROMOTE)
    - A weighted-pool idea queue with feasibility × novelty × impact scoring
    - A cross-model adversarial critique layer
    - A DEBUG-driven self-healing recovery path
    - A hybrid local-then-cloud compute dispatcher

The modules are intentionally structural rather than production-ready: each
exposes the verb's responsibilities, the shared data shapes, and the
extension points that the production agent instances implement. Plug in
your own LLM client, your own pool storage, and your own compute backend.

See `docs/architecture.md` for the conceptual model and `docs/verb-kernel.md`
for the universal-5 verb registry.
"""
from __future__ import annotations

from .pool import Pool, PoolEntry
from .verbs import VERB_KERNEL, Verb, register_verb
from .score import score_entry
from .execute import dispatch
from .analyze import analyze_result
from .critique import critique_result
from .self_heal import handle_failure, recovery_entry

__all__ = [
    "Pool",
    "PoolEntry",
    "VERB_KERNEL",
    "Verb",
    "register_verb",
    "score_entry",
    "dispatch",
    "analyze_result",
    "critique_result",
    "handle_failure",
    "recovery_entry",
    "run_loop",
]

__version__ = "0.1.0"


def run_loop(pool: Pool, *, max_iterations: int | None = None) -> None:
    """Execute the ARIA flywheel against a pool until exhaustion or limit.

    The loop is intentionally simple and synchronous in this reference
    implementation. Production deployments swap in async dispatch, parallel
    cloud workers, and persistent session state — see the paper §3 for the
    architectural choices.

    Each iteration runs one full flywheel cycle:
        1. Pop the highest-scoring active pool entry (PROMOTE).
        2. Design the experiment (DESIGN).
        3. Execute (RUN) — local screening first, then cloud if it passes.
        4. Analyze the result (ANALYZE).
        5. Critique adversarially with a cross-model judge (CRITIQUE).
        6. On failure at any stage: classify, write a recovery entry, and
           continue without operator intervention (DEBUG / self-heal).

    Args:
        pool: A `Pool` instance holding the idea queue. The pool must be
              non-empty at start; it may grow during iteration via
              recovery entries and follow-up suggestions.
        max_iterations: Stop after this many loop iterations. None means run
              until the pool is exhausted (no active entries remain).
    """
    iteration = 0
    while True:
        if max_iterations is not None and iteration >= max_iterations:
            return
        entry = pool.next_active()
        if entry is None:
            return
        try:
            designed = entry.design()
            result = dispatch(designed)
            analysis = analyze_result(result)
            verdict = critique_result(analysis)
            pool.archive(entry, analysis=analysis, verdict=verdict)
        except Exception as exc:  # noqa: BLE001 - self-heal swallows by design
            recovery = recovery_entry(entry, exc)
            pool.add(recovery)
            pool.archive(entry, status="failed", error=str(exc))
        iteration += 1
