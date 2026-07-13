"""Feasibility × novelty × impact scoring.

The pool entry score determines pick order. The reference implementation
combines three sub-scores multiplicatively so that any one being near-zero
suppresses the overall score — an experiment that scores 9/10 on impact but
1/10 on feasibility should not run.

Production deployments weight the sub-scores by domain priority and apply
a recency-decay so that old high-scoring entries don't crowd out fresh
ideas; that policy layer is out of scope for the reference release.
"""
from __future__ import annotations

from .pool import PoolEntry


def score_entry(
    entry: PoolEntry,
    *,
    feasibility: float,
    novelty: float,
    impact: float,
    domain_bonus: float = 0.0,
) -> float:
    """Compute a composite score in [0, 10] for a pool entry.

    Args:
        entry: The entry being scored (mutated in place).
        feasibility: 0-10. How likely the experiment is to run cleanly given
                     current tooling, data availability, and compute budget.
        novelty: 0-10. How much new information a positive result provides
                 relative to what the corpus already contains.
        impact: 0-10. How much a positive result changes downstream behavior
                (other pool entries, partner-team priorities, code changes).
        domain_bonus: Additive bonus for entries in under-served domains.
                      Production weights this by the domain's pool-density gap.
    """
    if not all(0 <= v <= 10 for v in (feasibility, novelty, impact)):
        raise ValueError("sub-scores must be in [0, 10]")
    if domain_bonus < 0:
        raise ValueError("domain_bonus must be non-negative")
    # Geometric mean across the three sub-scores, scaled to [0, 10]
    geo_mean = (feasibility * novelty * impact) ** (1 / 3)
    score = min(10.0, geo_mean + domain_bonus)
    entry.score = round(score, 3)
    entry.meta.setdefault("scoring", {}).update(
        feasibility=feasibility,
        novelty=novelty,
        impact=impact,
        domain_bonus=domain_bonus,
    )
    return entry.score
