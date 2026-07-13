# Evidence Index

Files in this directory are sanitized excerpts from the paper's evidence pipeline. They support the system-metrics claims in §3–§8 without exposing any partner-team scientific data or any pre-publication results from the production deployments.

## Sanitization policy

- The seven deployed instances are referred to by their public names where they exist (`aria`, `aria-se`, `aria-red`, `aria-pub`, `aria-forge`) and by anonymized labels for the enterprise instances (`enterprise pharma deployment A`, `enterprise pharma deployment B (oncology R&D context)`). The internal names of the enterprise instances are not in this release.
- Per-experiment scientific data (biomarker predictions, cohort labels, model checkpoints) is not in this release. The cross-platform age-regression result in §5.4 of the paper is supported by per-subject predictions that live in the partner-team's wave-1 SocialEyes manuscript pipeline; pointers below.
- The summary metrics (commit counts, verb distributions, session counts, artifact counts, cost figures) describe operational behavior of the system and are released here in full.

## What's in this directory

### `metrics.json` — Per-instance summary metrics

Headline operational numbers per instance: commit count, session count, active days, share-channel artifact counts, cloud spend. Source for the Table 3 row data in the paper.

### `verb_distribution.json` — Verb counts per instance

Top-N verb counts per instance, with the universal-5 vs extension verb split. Source for Figure 4 (verb compression by instance).

### `replay_ablations.json` — Counterfactual replay outputs

Replay-based ablations on the aria-se 50-day corpus:

- **A1 — No DEBUG verb.** Operator-load multiplier under the counterfactual where every DEBUG event becomes an operator-required intervention. Bounded floor: 5×–13× depending on per-event handling time assumption.
- **A2 — No cross-model critic.** Producer-side CRITIQUE commits removed; cross-agent influence chain traced to the actual git history (the `f49ddf5` SHA cited in earlier paper drafts does not exist; the real chain is `ecdbd8c` / `49186d2` / `6797bc6`).
- **A3 — No local-first filter.** Cost multiplier and yield-per-dollar degradation under the counterfactual where every pool entry dispatches directly to cloud.
- **S6 — DEBUG → recovery rate.** Of 321 DEBUG events in the 50-day window, 314 (97.8%) self-healed; median recovery latency 8.3 minutes. See `debug_recovery.csv` for the per-event data.
- **S4 — Operator-commit cadence.** Weekly autonomous-vs-operator commit counts; 287 of 296 operator commits in setup weeks 1-3, three consecutive zero-operator weeks W5-W7.

### `debug_recovery.csv` — Per-DEBUG-event recovery analysis

One row per DEBUG commit in the 50-day window. Columns: sha, timestamp, date, session_id, recovered (bool), recovery_latency_hours, next_autonomous_verb, operator_resolver_sha (if recovered=False), operator_resolver_subject. Source for the 97.8% self-heal-rate claim in §3.5 and Appendix E.4.

### `c1m2_age_bootstrap.json` — §5.4 paired-bootstrap + Steiger Z output

The full numerical output of the paired-bootstrap + Steiger Z + Fisher z analysis behind §5.4 of the paper. Single-platform MCCV reference r = 0.7709 ± 0.0378 (n = 2,120); cross-platform mean r = 0.594 from union-trained model on 309 paired subjects; within-cross-platform Steiger Z confirms no device-specific advantage (p > 0.5); Fisher z between single- and cross-platform shows significant gap (z = 5.53, p < 10⁻⁶).

## Reproducibility pointers

- **Replay scripts.** The replay-ablation code lives in a sibling private repository alongside the production aria-se corpus, because the replay reads the full commit-log + pool-YAML + share-artifact + cloud-run-log snapshot. The release here exposes the *outputs* of those scripts. If you want to re-run the replay against your own ARIA deployment, the algorithm is described in `docs/architecture.md` and implemented for the kernel in `kernel/`.

- **Cross-platform predictions.** The per-subject predictions behind `c1m2_age_bootstrap.json` come from the partner-team's wave-1 SocialEyes manuscript pipeline (sprint3 MCCV runs + sprint4 cross-device-union experiments). They will be released alongside the wave-1 manuscript and are not in this repo.

- **Cost data.** The cloud-runs log (900 dispatches, 147 completions, $86.92 total) is summarized in `metrics.json`. The per-dispatch detail is in the production corpus.

## Citing the evidence

If you cite specific numbers from this directory in academic work, please cite the paper (see `../CITATION.cff`) and reference the JSON file by name. Example:

> Self-healing analysis from the deployed aria-se instance shows 314 of 321 DEBUG events recovered without operator intervention (`evidence/debug_recovery.csv`, computed by the replay procedure in Appendix E.4 of Johnson & Bedworth 2026).
