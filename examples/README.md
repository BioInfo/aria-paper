# Examples

This directory holds runnable examples that exercise the kernel. The reference release ships with **structural** examples — they show how to wire your own runners and LLM clients into the kernel without requiring any specific cloud account, model provider, or scientific dataset.

## 0. Hello flywheel

The smallest possible loop. Creates a pool, scores one entry, runs one full flywheel cycle with the reference (noop) backends:

```python
from kernel import Pool, PoolEntry, run_loop, score_entry

pool = Pool("/tmp/aria-hello/pool")
entry = PoolEntry(
    idea_id="idea_001_hello",
    title="Verify the kernel runs end-to-end",
    hypothesis="A noop run completes a full flywheel cycle without raising.",
    domain="meta",
)
score_entry(entry, feasibility=10, novelty=2, impact=2)
pool.add(entry)

run_loop(pool, max_iterations=1)
```

After the loop runs, look in `/tmp/aria-hello/pool/archived/` for the completed entry with its analysis and verdict.

## 1. Wire your own runner

The kernel ships with Protocol stubs (`LocalRunner`, `CloudRunner`, `CriticClient`). Implement them against your backend:

```python
from kernel.execute import LocalRunner, CloudRunner, RunResult, dispatch
from kernel.pool import PoolEntry

class MyLocalScreen:
    def run(self, entry: PoolEntry) -> RunResult:
        # Call your local training template here, return a RunResult
        ...

class MyCloudRunner:
    def run(self, entry: PoolEntry) -> RunResult:
        # Submit to your preemptible-GPU backend, return a RunResult
        ...

result = dispatch(some_entry, local=MyLocalScreen(), cloud=MyCloudRunner())
```

## 2. Plug in a cross-model critic

The architectural commitment is that the critic runs a *different* model family from the producer. Implement the `CriticClient` Protocol with your LLM SDK of choice:

```python
from kernel.critique import CriticClient, critique_result

class MyCritic:
    def verdict(self, analysis: dict) -> dict:
        # Call your critic LLM (different family from your producer) here
        return {"verdict": "WARNING", "rationale": "...", "confidence_score": 0.78}

verdict = critique_result(analysis_dict, client=MyCritic())
```

## 3. Inspect a running instance

Use the `tools/aria-status.py` skill to read the current state of an ARIA instance:

```bash
python tools/aria-status.py --root /path/to/your/instance --n 100
```

It reports pool buckets, recent verb distribution, self-heal rate over the last N commits, critique queue depth, and the last successful cloud run timestamp. Designed for the human-on-the-loop monitoring role (paper §6.1).

## 4. Reproduce the replay-based ablations

The replay procedure (paper Appendix E) operates on a snapshot of a deployed instance's commit log, pool YAML files, share artifacts, and cloud-run log. The algorithm is described in `docs/architecture.md` and is implemented for the reference kernel in `kernel/`; the production replay scripts live in a sibling private repository because they read the full corpus snapshot.

To replay against your own deployment, the inputs you need are:

- `commits.jsonl` — git log dump with verb-tagged subjects
- `pool/<bucket>/*.yaml` — pool state at end of window
- `share/from_*/*.yaml` — IPC artifacts
- `state/cloud_runs_log.csv` — cloud dispatch + completion records

Pre-built replay outputs from the case-study deployment are in [`evidence/replay_ablations.json`](../evidence/replay_ablations.json) and [`evidence/debug_recovery.csv`](../evidence/debug_recovery.csv).

## What's intentionally not here

- A production-grade LLM dispatcher (use your provider's SDK).
- A production cloud-runner (use your preemptible-GPU provider's API).
- A scientific-domain training template (these are domain-specific by construction).

If you build one of these and want to point at it from this repo, open a PR — see [`CONTRIBUTING.md`](../CONTRIBUTING.md).
