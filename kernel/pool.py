"""The weighted-pool idea queue.

The pool is the single shared data structure the flywheel rotates around.
Every flywheel stage produces pool entries (DESIGN reads them, ANALYZE
writes follow-ups, CRITIQUE re-weights existing entries, DEBUG writes
recovery entries). The pool holds an entry's full lifecycle: active →
designed → running → completed / failed → archived.

This reference implementation stores entries as YAML files in a directory
tree (`pool/active/`, `pool/completed/`, etc.) to match the production
deployments described in the paper. Swap `Pool` for a database-backed
implementation if you need transactional updates across many concurrent
agents.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class PoolEntry:
    """A single idea / experiment / recovery entry in the pool.

    Pool entries flow through bucket directories:
        active     — open and ready to be picked up
        designed   — DESIGN ran, config artifact attached
        running    — RUN dispatched (local or cloud)
        completed  — RUN finished with a result file
        critiqued  — CRITIQUE wrote a verdict
        archived   — terminal state
        failed     — terminal state with an `error` field
        blocked    — gated on an external dependency
        culled     — explicitly removed (e.g. duplicate, scope violation)

    Attributes:
        idea_id: Unique id, by convention `idea_<sequence>_<short_slug>`.
        title: Short human-readable summary.
        hypothesis: What the experiment is testing.
        evidence: Why the hypothesis is worth pursuing now.
        tractability: How the experiment is feasible with current tools.
        impact: What downstream change a positive result enables.
        domain: Which research domain (free-form tag for filtering).
        score: Composite feasibility × novelty × impact score (0-10).
        status: Current lifecycle bucket.
        created: ISO timestamp of pool entry creation.
        parents: Optional list of pool entry ids this one was derived from.
        meta: Free-form metadata bag (e.g. recovery context, critic verdict).
    """

    idea_id: str
    title: str
    hypothesis: str
    evidence: str = ""
    tractability: str = ""
    impact: str = ""
    domain: str = "general"
    score: float = 0.0
    status: str = "active"
    created: str = field(default_factory=lambda: dt.datetime.now(dt.UTC).isoformat())
    parents: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def design(self) -> "PoolEntry":
        """Run the DESIGN verb against this entry.

        In production this calls the producer LLM with a DESIGN persona to
        emit a runnable experiment config. The reference implementation
        annotates the entry and returns it unchanged so the kernel loop
        can proceed structurally.
        """
        self.status = "designed"
        self.meta.setdefault("design", {})["designed_at"] = dt.datetime.now(dt.UTC).isoformat()
        return self


class Pool:
    """Filesystem-backed pool of entries.

    Production deployments use a structured directory tree under `pool/` with
    one YAML per entry; the bucket is the parent directory name. This class
    provides the minimal CRUD surface the kernel needs.
    """

    BUCKETS = (
        "active",
        "designed",
        "running",
        "completed",
        "critiqued",
        "archived",
        "failed",
        "blocked",
        "culled",
    )

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        for bucket in self.BUCKETS:
            (self.root / bucket).mkdir(parents=True, exist_ok=True)

    def add(self, entry: PoolEntry) -> None:
        """Write a new entry to its current-status bucket."""
        path = self.root / entry.status / f"{entry.idea_id}.yaml"
        path.write_text(yaml.safe_dump(entry.__dict__, sort_keys=False))

    def next_active(self) -> PoolEntry | None:
        """Return the highest-scoring active entry, or None if pool is empty."""
        active_dir = self.root / "active"
        candidates = sorted(active_dir.glob("*.yaml"))
        if not candidates:
            return None
        best: PoolEntry | None = None
        for path in candidates:
            data = yaml.safe_load(path.read_text())
            entry = PoolEntry(**data)
            if best is None or entry.score > best.score:
                best = entry
        return best

    def archive(
        self,
        entry: PoolEntry,
        *,
        status: str = "archived",
        analysis: dict | None = None,
        verdict: dict | None = None,
        error: str | None = None,
    ) -> None:
        """Move an entry to a terminal bucket, optionally attaching findings."""
        old_path = self.root / entry.status / f"{entry.idea_id}.yaml"
        if old_path.exists():
            old_path.unlink()
        entry.status = status
        if analysis is not None:
            entry.meta["analysis"] = analysis
        if verdict is not None:
            entry.meta["critic_verdict"] = verdict
        if error is not None:
            entry.meta["error"] = error
        self.add(entry)
