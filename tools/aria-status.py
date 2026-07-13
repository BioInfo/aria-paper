#!/usr/bin/env python3
"""aria-status — read-only health check for an ARIA instance.

Sanitized from the deployed `tools/aria-status.py` skill. Reports:
    - Pool size by bucket
    - Recent commit verbs (last N commits)
    - Last successful cloud run timestamp
    - Critique queue depth (unread share/from_critic/ entries)
    - Self-heal rate over the recent window

Used by the human operator on the "monitoring" loop. The deployed cadence
is roughly daily in weeks 1-2 of a fresh instance and weekly thereafter
once self-healing has absorbed the failure modes (see paper §6.3).

Usage:
    aria-status                  # current instance, last 50 commits
    aria-status --instance se    # specific instance under ./instances/
    aria-status --n 200          # last 200 commits
    aria-status --json           # machine-readable output
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

VERB_RE = re.compile(r"\[([A-Z][A-Z_]+)\]")


def pool_stats(root: Path) -> dict[str, int]:
    pool_dir = root / "pool"
    if not pool_dir.exists():
        return {}
    return {
        bucket.name: sum(1 for _ in bucket.glob("*.yaml"))
        for bucket in pool_dir.iterdir()
        if bucket.is_dir() and not bucket.name.startswith(".")
    }


def recent_verbs(root: Path, n: int) -> Counter[str]:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "log", f"-n{n}", "--pretty=%s"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Counter()
    counts: Counter[str] = Counter()
    for line in out.splitlines():
        m = VERB_RE.search(line)
        if m:
            counts[m.group(1)] += 1
    return counts


def self_heal_rate(root: Path, n: int) -> tuple[int, int, float]:
    """Compute (debug_events, self_healed, rate) over the last n commits.

    A DEBUG is considered self-healed if the next non-DEBUG commit in the
    log is autonomous (subject contains '(autonomous)' or 'auto-commit' or
    'session-NNNN'). This is the same heuristic the paper's Appendix E.4
    replay analysis uses.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "log", f"-n{n}", "--pretty=%H %s"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 0, 0, 0.0
    commits = [line.split(" ", 1) for line in out.splitlines() if line.strip()]
    debug_total = 0
    healed = 0
    for i, (_, subj) in enumerate(commits):
        if "[DEBUG]" not in subj:
            continue
        debug_total += 1
        # Look at the previous (= more recent in git log) commit; if autonomous, healed
        if i == 0:
            continue
        prev_subj = commits[i - 1][1]
        is_auto = (
            "(autonomous)" in prev_subj
            or "auto-commit" in prev_subj
            or re.search(r"session-\d+", prev_subj, re.IGNORECASE)
        ) and "[DEBUG]" not in prev_subj
        if is_auto:
            healed += 1
    rate = (healed / debug_total) if debug_total else 0.0
    return debug_total, healed, rate


def critique_queue_depth(root: Path) -> int:
    share = root / "share" / "from_critic"
    if not share.exists():
        return 0
    return sum(1 for _ in share.rglob("*.yaml"))


def last_cloud_run(root: Path) -> str | None:
    log = root / "state" / "cloud_runs_log.csv"
    if not log.exists():
        return None
    try:
        lines = log.read_text().splitlines()
    except OSError:
        return None
    if len(lines) < 2:
        return None
    # First column is timestamp by convention
    return lines[-1].split(",")[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="ARIA instance status")
    parser.add_argument(
        "--root", default=".", help="Path to the ARIA instance root (default: cwd)"
    )
    parser.add_argument(
        "--n", type=int, default=50, help="Commits to scan for verbs + self-heal (default: 50)"
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    pool = pool_stats(root)
    verbs = recent_verbs(root, args.n)
    debug_total, healed, rate = self_heal_rate(root, args.n)
    queue = critique_queue_depth(root)
    last_cloud = last_cloud_run(root)

    report = {
        "instance_root": str(root),
        "pool": pool,
        "verbs_last_n": dict(verbs.most_common()),
        "n_commits_scanned": args.n,
        "debug_events": debug_total,
        "self_healed": healed,
        "self_heal_rate": round(rate, 4),
        "critique_queue_depth": queue,
        "last_cloud_run_at": last_cloud,
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(f"ARIA status — {root}")
    print(f"Pool buckets: {pool or '(no pool/ dir found)'}")
    print(f"Verbs (last {args.n} commits): {dict(verbs.most_common(10))}")
    print(
        f"Self-heal: {healed}/{debug_total} DEBUG events recovered "
        f"({rate*100:.1f}%)"
    )
    print(f"Critique queue depth: {queue}")
    print(f"Last cloud run at: {last_cloud or '(none)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
