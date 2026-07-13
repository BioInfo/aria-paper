# ARIA Architecture

This document is a self-contained companion to §3 of the paper. It describes the six flywheel stages, the universal-5 verb kernel, the weighted-pool data structure, the cross-agent IPC protocol, and the self-healing path.

## 1. The Flywheel

ARIA's central abstraction is a six-stage loop that every agent instance runs continuously:

```
       ┌─────────┐
       │ DESIGN  │
       └────┬────┘
            ▼
       ┌─────────┐         ┌──────────┐
       │   RUN   │────────►│  DEBUG   │ (on failure)
       └────┬────┘         └────┬─────┘
            ▼                   │
       ┌─────────┐              │
       │ ANALYZE │              │
       └────┬────┘              │
            ▼                   │
       ┌─────────┐              │
       │CRITIQUE │              │
       └────┬────┘              │
            ▼                   │
       ┌─────────┐              │
       │ PROMOTE │◄─────────────┘  (recovery entries land back in pool)
       └────┬────┘
            ▼
        (next iteration)
```

Each stage is the responsibility of one verb in the universal-5 kernel. The loop is closed: PROMOTE writes back to the pool that DESIGN reads from, and DEBUG-emitted recovery entries are normal pool entries that the next iteration will pick up.

## 2. The Universal-5 Verb Kernel

Five verbs appear in every ARIA instance that wrote autonomous commits:

| Verb     | Stage     | Responsibility |
|----------|-----------|----------------|
| DESIGN   | design    | Shape a runnable experiment from a pool entry. |
| RUN      | run       | Execute. Local screening first, then cloud if it passes. |
| ANALYZE  | analyze   | Inspect the result and extract structured insight. |
| CRITIQUE | critique  | Adversarial cross-model review. Emits PASS/WARNING/FLAG/INFO. |
| DEBUG    | self_heal | Classify a failure and write a recovery entry. |

These are the irreducible verbs of a research loop. Instances may register additional verbs (SCOUT, SURVEY, HYPOTHESIZE, SYNTHESIZE, BRIEF, ADVISE, etc.) for their domain. The paper reports verb-cardinality compression as a maturity signal: research labs explore (25 verbs); research factories specialize (13–14 verbs).

See [`kernel/verbs.py`](../kernel/verbs.py) for the registry implementation.

## 3. The Pool

The pool is the single shared data structure the flywheel rotates around. It holds an entry's full lifecycle: `active → designed → running → completed → critiqued → archived` (or `failed`, `blocked`, `culled`).

Pool entries are scored by a composite of feasibility × novelty × impact. The score determines pick order. Production scoring uses domain bonuses for under-served research areas and a recency decay to prevent old high-scoring entries from crowding out fresh ideas.

Pool entries flow between agents through a filesystem mirror (`pool/<bucket>/<idea_id>.yaml`); the same directory tree is what the cross-agent IPC protocol (§4) shares.

See [`kernel/pool.py`](../kernel/pool.py) for the reference implementation.

## 4. Cross-Agent IPC

Multiple ARIA instances communicate by **writing to and reading from each other's shared `share/` directories**. The deployed system used Syncthing to mirror a `share/` tree between agent hosts; any filesystem-sync mechanism (NFS, rsync, S3 + lifecycle rules, an object-storage SDK) will work.

Channels in the producer's `share/` directory:

```
share/
├── from_critic/      ← critic agent writes adversarial verdicts here
├── from_publisher/   ← publisher agent writes tier-2 manuscript drafts here
├── from_human/       ← principal architect forwards ideas / references / corrections
└── to_critic/        ← producer writes completed experiments here for critic pickup
```

The IPC protocol is intentionally schemaless at the directory level — every channel is a directory of YAML files keyed by timestamp + content hash. Agents poll on a configurable interval (the deployed system used 30-minute polls for low-volume channels and 5-minute polls for high-volume ones).

See [`docs/ipc-protocol.md`](ipc-protocol.md) for the schemas of each channel.

## 5. Hybrid Compute

The RUN verb dispatches in two stages:

1. **Local screen.** A short quick-validation pass on a small local GPU. The screening template is domain-specific; for the medical-imaging case study it was a ConvNeXt-Tiny single-epoch fit on a 5% data subsample. The screen catches obviously-broken configs (data loader returns empty, target collapses to constant, NaN loss in the first hundred steps) before they consume cloud compute.

2. **Cloud dispatch.** Survivors of the local screen go to preemptible cloud GPUs (the deployment used vast.ai RTX 3090/4090 instances at $0.04-$0.10/hour). The dispatcher tolerates a high preemption rate; the case-study deployment ran 900 cloud dispatches against 213 unique experiments (4.23 retries per promoted experiment on average) and achieved a 16.3% completion rate.

The economic rationale (§7.1 of the paper): preemptible cloud at high attrition is cheaper per completed experiment than guaranteed cloud at higher hourly rates, *if* a local screen pre-filters obviously-broken configs. Without the local screen, the same workload costs ~4× more for the same signal yield (replay-based ablation A3, see `evidence/replay_ablations.json`).

## 6. Self-Healing (DEBUG)

DEBUG is what makes multi-month operation possible. The verb:

1. **Classifies** the failure into a known mode (preempt, OOM, NaN loss, dependency drift, malformed YAML, network error, timeout, unknown).
2. **Writes a recovery pool entry** that inherits the failed entry's domain and parent chain, annotates the failure mode, and proposes a concrete next step.
3. **Returns control to the loop**, which picks the recovery entry on its next iteration.

The deployed system emitted 321 DEBUG verb commits over 50 days. **314 of them (97.8%) self-healed** before any operator commit. Median recovery latency was 8.3 minutes. The seven that required operator intervention all clustered in weeks 2-3 and triggered structural code changes that closed underlying architectural gaps; from week 4 onward the self-heal rate was 100% across 206 events and 28 days.

The architectural reading: DEBUG is what shifts the operator's role from "fix every error" to "occasionally close a structural gap that DEBUG correctly surfaced as unrecoverable."

See [`kernel/self_heal.py`](../kernel/self_heal.py) for the reference implementation and [`evidence/debug_recovery.csv`](../evidence/debug_recovery.csv) for the per-event data.

## 7. Cross-Model Critique

The critic agent runs a **different model family** from the producer. This is a deliberate architectural choice, not a budget compromise: same-family critique produces higher PASS rates by training-data correlation, which defeats the purpose. The deployed system paired Kimi K2 producer with GLM-5 critic.

The critic emits one of four verdicts:

- **PASS** — no issues found; result is usable.
- **WARNING** — usable with caveats (calibration, scope, missing controls).
- **FLAG** — usable only after fix; a follow-up pool entry is suggested.
- **INFO** — meta-observation about the system, not the result itself.

Verdicts flow to the producer through the IPC channel `share/from_critic/`. The producer's next iteration picks up verdicts as pool inputs, weighting FLAG and WARNING higher than PASS for follow-up scoring.

The deployed system's critic emitted 234 artifacts over the 5-week active window; **85% of the 193-critique sample returned FLAG or WARNING** (90.6% if you restrict the denominator to quality verdicts and exclude INFO). The cross-family setup is what generated the producer-side code change that the paper treats as the strongest cross-agent influence event (the `ecdbd8c`/`49186d2`/`6797bc6` integration chain).

See [`kernel/critique.py`](../kernel/critique.py).

## 8. The Two Intentional Human Roles

The architecture has two intentional places for a human:

- **Human on the loop (monitoring).** Light-touch flywheel health checks through command-line status skills like [`tools/aria-status.py`](../tools/aria-status.py). Pool sizes, recent commit verbs, last successful cloud run, critique queue depth. Operational work, measured in minutes per check-in. Fades as the loop matures.
- **Human in the loop (steering).** Feeding ideas, references, and forwarded artifacts into the same weighted pool that holds auto-generated entries. The pool entry is the only interface; once a human-injected entry lands in the pool it is indistinguishable from an auto-generated one.

The paper reports operator-commit cadence dropping from 287 commits in setup weeks 1-3 to 4 commits across mature weeks 4-7 (three consecutive zero-operator weeks against 5,196 autonomous commits), confirming that both roles can scale down without scaling out the system.
