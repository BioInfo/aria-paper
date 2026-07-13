# Cross-Agent IPC Protocol

ARIA instances communicate through a shared `share/` directory tree. The deployed system used Syncthing to mirror the directory between agent hosts; any filesystem-sync mechanism works (rsync, NFS, S3 + lifecycle rules, an object-store SDK with polling).

## Top-level layout (producer's perspective)

```
share/
├── from_critic/      ← critic agent writes adversarial verdicts here
├── from_publisher/   ← publisher agent writes tier-2 manuscript drafts here
├── from_human/       ← principal architect forwards ideas / references / corrections
└── to_critic/        ← producer writes completed experiments here for critic pickup
```

Each channel is a directory of YAML files keyed by timestamp + content hash. Files are written atomically (write-to-tempfile, rename-into-place) so a partial write does not poison a poll.

## Channel schemas

### `from_critic/critique_<timestamp>_<hash>.yaml`

```yaml
critique_id: critique_20260221_153044_a3f8c1
experiment_id: exp_660_icare_quality_generalization
producer_instance: aria-se
critic_instance: aria-red
critic_model: glm-5
verdict: WARNING        # PASS | WARNING | FLAG | INFO
confidence_score: 0.78
rationale: |
  Subject-level pooling preserves rank ordering but predicted-std-to-target-std
  ratio is 0.097, indicating estimation collapse. Result is usable for
  population-level stratification but unreliable for individual point estimates.
suggested_followups:
  - title: "Test calibration with isotonic regression on validation fold"
    domain: multi_platform
    feasibility: 9
    novelty: 4
    impact: 6
flagged_metrics:
  predicted_std_to_target_std: 0.097
  expected_r2_from_r: 0.569
  observed_r2: 0.087
```

### `from_publisher/tier2/<experiment_id>/<section>.md`

The publisher writes structured manuscript-draft sections (abstract, methods, results, discussion, figure_specs, novelty_and_venues, finding.json) into a per-experiment directory. Producer agents read this when they need to cite a completed experiment in a follow-up pool entry.

### `from_human/<channel>_<timestamp>.yaml`

The human-injected channel is the simplest. It accepts any of:

- A new pool entry (`type: pool_entry`) — the producer's intake routine ingests it into `pool/active/`.
- A reference (`type: reference`) — a URL + summary that the next HYPOTHESIZE pass should consider.
- A correction (`type: correction`) — an explicit override on a recent producer commit (e.g. "the AUC in `exp_337` was reported at 0.748 but should be 0.751"). Production corrections are rare but high-signal.

### `to_critic/result_<experiment_id>_<timestamp>.yaml`

The producer writes a structured pointer when an experiment completes:

```yaml
producer_instance: aria-se
experiment_id: exp_660_icare_quality_generalization
completed_at: 2026-03-05T11:26:41.549421+00:00
result_paths:
  metrics: corpus/insights/multi_platform/exp_660_summary.md
  predictions: execution/completed/exp_660/test_predictions.csv
  config: execution/completed/exp_660/config.yaml
result_summary:
  biomarker: Age 2025
  subject_correlation: 0.6677
  n_subjects: 309
red_verdict_hint: null   # producer's self-assessment, optional
```

The critic polls `to_critic/`, dispatches against the result, and writes back into the producer's `from_critic/`.

## Polling cadence

The deployed system uses different polls per channel:

- `from_critic/` — 30 minutes (low volume, latency-tolerant)
- `from_publisher/` — 30 minutes
- `from_human/` — 5 minutes (operator may want fast turnaround)
- `to_critic/` (critic polling producer) — 5 minutes (fast pickup of completed results)

## Honest mechanism note

In the deployed system, the publisher's `from_publisher/` content was **forwarded into the producer's session-level guidance by the principal architect** rather than being auto-consumed by the producer's prompt builder. A fully-automated consumption path was scoped but not implemented during the operational window; closing it is future work (§9.1 of the paper).
