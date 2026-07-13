<div align="center">

<img src="assets/banner.png" alt="ARIA — Sustained Autonomous Research Agents in Biomedicine" width="100%">

<br/>

# ARIA

**A multi-agent research flywheel for multi-month autonomous scientific discovery.**

Paper companion code for the bioRxiv preprint:
*"Sustained Autonomous Research Agents in Biomedicine: ARIA, an 18-Week Multi-Domain Deployment, and a Cross-Platform Retinal Biomarker Result"*
(Johnson & Bedworth, 2026).

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=flat-square)](LICENSE)
[![bioRxiv](https://img.shields.io/badge/bioRxiv-PENDING-b31b1b.svg?style=flat-square)](https://www.biorxiv.org)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code_style-ruff-000.svg?style=flat-square)](https://github.com/astral-sh/ruff)
[![CITATION.cff](https://img.shields.io/badge/cite_this-CITATION.cff-blueviolet.svg?style=flat-square)](CITATION.cff)
[![Status: reference implementation](https://img.shields.io/badge/status-reference_implementation-orange.svg?style=flat-square)](#scope)

</div>

---

## What is ARIA?

ARIA is a flywheel architecture for running autonomous LLM-driven research agents over weeks and months, not minutes and hours. It combines:

- **A six-stage verb kernel** — `DESIGN → RUN → ANALYZE → CRITIQUE → DEBUG → PROMOTE` — that every agent instance shares.
- **A weighted-pool idea queue** scored by `feasibility × novelty × impact`, with steering hooks for human-injected priorities.
- **An adversarial cross-model critique layer** (a different model family from the producer) that runs autonomously against producer output and writes findings back into the pool.
- **A hybrid local-then-cloud compute path** that screens ideas on a small local GPU before dispatching survivors to preemptible cloud GPUs.
- **A `DEBUG`-driven self-healing path** that classifies execution failures, writes recovery pool entries, and lets the next iteration absorb the failure without operator intervention.

Across an 18-week operational deployment of seven instances over four scientific domains, the deployed system produced 19,364 commits, roughly 17,800 autonomous sessions, and 1,028 inter-agent artifacts. The longest instance operated continuously for 50 days and **self-healed 97.8% of its own operational failures (median recovery 8.3 minutes)** without operator intervention. The full quantitative case is in the paper; the highlights are in [`evidence/`](evidence/).

## Why is this interesting?

Most long-horizon autonomous-agent benchmarks measure capability at fixed task-completion. ARIA targets a different question: **what does it take for a research agent to keep running on its own for months?** The answer in this paper is structural — a verb kernel small enough to be universal, an adversarial critique loop that another model runs without supervision, a self-healing path that absorbs the long tail of operational failures, and a cost model that lets a small lab afford to keep the lights on.

The architecture is reproducible on a small-lab budget. Total cloud compute spend across the 50-day case study was $86.92.

## Scope

This repository is a **reference implementation** of the kernel framework. It is the minimum surface area required to read the paper, reproduce the architectural claims at a structural level, and build your own ARIA-shaped agent on top of it.

It is intentionally not:
- a turn-key deployable research system,
- the production code that ran the case studies in the paper (those live in private repos),
- a benchmark harness or evaluation framework.

If you are looking for the paper's evidence tables, the replay-based ablations, and the sanitized verb/timeline metrics, see [`evidence/`](evidence/).

## Repository layout

```
aria-paper/
├── README.md                    you are here
├── LICENSE                      Apache 2.0
├── CITATION.cff                 cite-this metadata
├── CHANGELOG.md                 versioned release notes
├── CONTRIBUTING.md              issue + PR guidance
├── pyproject.toml               uv-managed Python project
├── assets/
│   └── banner.png               README hero image
├── docs/
│   ├── architecture.md          system architecture + six-stage flywheel
│   ├── ipc-protocol.md          share/ directory protocol between agents
│   └── verb-kernel.md           the universal-5 verb kernel + extensions
├── kernel/
│   ├── __init__.py              package entrypoint
│   ├── pool.py                  weighted-pool idea queue
│   ├── score.py                 feasibility × novelty × impact scoring
│   ├── execute.py               local-then-cloud dispatch
│   ├── analyze.py               result ingestion + insight generation
│   ├── critique.py              cross-model adversarial critique
│   ├── self_heal.py             DEBUG verb → recovery pool entry
│   └── verbs.py                 universal-5 + extension verb registry
├── personas/
│   └── aria-template.md         sanitized agent prompt template
├── tools/
│   └── aria-status.py           sanitized status skill (CLI)
├── evidence/
│   ├── README.md                index of paper evidence files
│   ├── metrics.json             per-instance summary metrics (sanitized)
│   ├── verb_distribution.json   verb counts per instance
│   ├── replay_ablations.json    counterfactual replay outputs
│   └── debug_recovery.csv       per-DEBUG-event recovery analysis
└── examples/
    └── README.md                quickstart pointers
```

## Quickstart

```bash
# Clone
git clone https://github.com/BioInfo/aria-paper.git
cd aria-paper

# Set up Python environment (uses uv — fast, reproducible)
uv venv && source .venv/bin/activate
uv pip install -e .

# Inspect the kernel
python -c "from kernel import Pool, run_loop; help(run_loop)"

# Check the evidence index
ls evidence/

# Read the architecture doc
${PAGER:-less} docs/architecture.md
```

The kernel modules are structured around the six flywheel stages and import each other through the verb registry in [`kernel/verbs.py`](kernel/verbs.py). Read [`docs/architecture.md`](docs/architecture.md) for the conceptual model before reading the code.

## Reproducing paper results

The exact numbers in the paper are tied to production corpora that live in private repositories (sanitization is described in [`evidence/README.md`](evidence/README.md)). The release here exposes:

- **Per-instance summary metrics** for the seven deployed agent instances (commit counts, verb distributions, session counts, artifact counts).
- **Replay-based counterfactual ablations** — what the deployment would have looked like without DEBUG, without cross-model critique, or without the local-first compute filter. Run on the sanitized corpora via the replay script in [`kernel/`](kernel/).
- **DEBUG recovery analysis** — the per-event paired data behind the 97.8% self-heal-rate claim in §3.5 of the paper.

The single largest scientific result in the paper (the cross-platform age-regression generalization claim in §5.4) uses per-subject prediction data from the partner-team research pipeline and is reproducible from the wave-1 SocialEyes manuscript artifacts; pointers in [`evidence/README.md`](evidence/README.md).

## Citing this work

If you reference ARIA in academic work, please use the BibTeX in [`CITATION.cff`](CITATION.cff). A short form:

```
Johnson, J. H., & Bedworth, N. (2026).
Sustained Autonomous Research Agents in Biomedicine: ARIA, an 18-Week Multi-Domain Deployment, and a Cross-Platform Retinal Biomarker Result.
bioRxiv preprint.
```

## Contributing

Issues and pull requests are welcome. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) first; in particular, contributions that depend on private production data cannot be accepted without first being sanitized through the same pipeline described in [`evidence/README.md`](evidence/README.md).

## License

[Apache License 2.0](LICENSE) — see the file for full terms. Permissive enough for both academic and commercial use; you keep your modifications, we keep the warranty disclaimer.

## Acknowledgments

The architecture was designed and operated by the authors as a personal research practice; production deployments of the kernel against medical-imaging and pharmaceutical-research workloads are described in the paper at a system-metrics level.

---

<div align="center">
<sub>Built on Claude Code, Kimi K2, GLM-5, and a handful of preemptible RTX 3090s. Apache 2.0. ✦</sub>
</div>
