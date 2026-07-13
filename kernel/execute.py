"""The RUN verb — hybrid local-then-cloud dispatcher.

The paper's §3.4 describes the cost rationale: screen ideas on a small local
GPU (DGX Spark in the operational deployment), and only promote survivors to
preemptible cloud GPUs (vast.ai RTX 3090/4090). The local screen filtered
~76% of pool entries before they hit cloud compute; the realistic-MID
counterfactual without the filter costs ~4× more for the same signal yield
(see `evidence/replay_ablations.json`).

The reference implementation exposes a Protocol so you can plug in any local
runner and any cloud provider. Production deployments wire this to:
    - local: a subprocess call into a domain-specific training template
    - cloud: a preemptible-instance API (vast.ai, RunPod, Lambda, etc.)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from .pool import PoolEntry


@dataclass
class RunResult:
    """Structured output of a single experiment run."""

    entry_id: str
    where: str  # "local" or "cloud"
    status: str  # "completed", "failed", "cancelled", "needs_rerun"
    duration_min: float
    cost_usd: float
    artifacts: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class LocalRunner(Protocol):
    """A local-screening backend. Returns quickly and cheaply."""

    def run(self, entry: PoolEntry) -> RunResult: ...


class CloudRunner(Protocol):
    """A cloud-dispatch backend. Preemptible. May fail or be cancelled."""

    def run(self, entry: PoolEntry) -> RunResult: ...


def passes_local_screen(result: RunResult) -> bool:
    """Decide whether a local-screening result is promising enough for cloud.

    The production heuristic is: completed without OOM/NaN/dead-loss within a
    short quick-validation budget AND the result file has non-zero variance
    on the target. This reference version is a structural placeholder.
    """
    return result.status == "completed" and result.duration_min > 0


def dispatch(
    entry: PoolEntry,
    *,
    local: LocalRunner | None = None,
    cloud: CloudRunner | None = None,
) -> RunResult:
    """Run an entry through the hybrid local-then-cloud path.

    1. If a local runner is supplied, screen there first.
    2. If the screen passes (or no local runner is supplied), dispatch to
       cloud.
    3. If neither runner is supplied, return a `noop` placeholder so the
       kernel loop can run structurally without any backend wired up.
    """
    if local is not None:
        local_result = local.run(entry)
        if not passes_local_screen(local_result):
            return local_result  # blocked by local screen
    if cloud is not None:
        return cloud.run(entry)
    return RunResult(
        entry_id=entry.idea_id,
        where="noop",
        status="completed",
        duration_min=0.0,
        cost_usd=0.0,
        artifacts={"note": "no runner wired; reference-loop noop"},
    )
