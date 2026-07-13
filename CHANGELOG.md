# Changelog

All notable changes to this project will be documented here. Format roughly follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning roughly follows [SemVer](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-05-16

### Added

- Initial public release of the ARIA paper companion repository.
- README with banner, badges, scope statement, and repository layout map.
- Apache 2.0 LICENSE.
- `CITATION.cff` with preprint + software metadata.
- `pyproject.toml` configured for `uv` install (kernel package + analysis extras).
- `kernel/` reference implementation:
  - `pool.py` — filesystem-backed weighted-pool idea queue with full lifecycle bucket model.
  - `verbs.py` — universal-5 verb kernel (DESIGN, RUN, ANALYZE, CRITIQUE, DEBUG) + extension registry.
  - `score.py` — feasibility × novelty × impact composite scoring.
  - `execute.py` — hybrid local-then-cloud dispatcher with Protocol-based backend pluggability.
  - `analyze.py` — structural result-to-insight extraction.
  - `critique.py` — cross-model adversarial critique with CriticClient Protocol.
  - `self_heal.py` — DEBUG verb with failure classification + recovery pool entry generation.
  - `__init__.py` — `run_loop()` entrypoint exposing the full flywheel cycle.
- `docs/` companion documentation:
  - `architecture.md` — six-stage flywheel + universal-5 verb kernel + hybrid compute + self-healing.
  - `verb-kernel.md` — verb registry reference + extension verb registration.
  - `ipc-protocol.md` — share/ directory protocol + per-channel YAML schemas.
- `personas/aria-template.md` — sanitized instance-persona template.
- `tools/aria-status.py` — read-only health-check skill (pool buckets, recent verbs, self-heal rate, critique queue depth, last cloud run).
- `evidence/` paper-evidence excerpts:
  - `metrics.json` — per-instance summary metrics (7 instances, 19,364 commits, $86.92 cloud spend).
  - `verb_distribution.json` — verb-cardinality and per-verb counts (Figure 4 source).
  - `replay_ablations.json` — counterfactual replay outputs (A1/A2/A3/S6/S4).
  - `debug_recovery.csv` — per-DEBUG-event recovery analysis (321 rows, 97.8% self-heal rate).
  - `c1m2_age_bootstrap.json` — §5.4 paired-bootstrap + Steiger Z output.
- `examples/README.md` — quickstart pointers for the reference loop and backend wiring.
- `CONTRIBUTING.md` — PR + issue guidance with explicit scope.
- `.gitignore` — Python + uv + macOS standards.
- `assets/banner.png` — Gemini-generated hero banner in the paper's navy/teal/orange palette.

### Notes

- The release is a **reference implementation** of the kernel framework. Production deployments of ARIA against medical-imaging and pharmaceutical-research workloads are described in the paper at a system-metrics level; the production code lives in private repositories.
- Enterprise-instance internal names are anonymized to "deployment A" and "deployment B" per repository policy. System-level operational metrics are released in full.
- The cross-platform age-regression result behind §5.4 of the paper is supported by per-subject predictions that live in the partner-team's wave-1 SocialEyes manuscript pipeline; pointers in `evidence/README.md`.

[0.1.0]: https://github.com/BioInfo/aria-paper/releases/tag/v0.1.0
