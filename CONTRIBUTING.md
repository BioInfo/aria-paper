# Contributing

Thanks for considering a contribution. This is a paper-companion repository, so the contribution surface is narrower than a typical OSS project. Read the scope notes below before you spend time on a PR.

## What contributions are welcome

- **Bug fixes** in `kernel/` modules (broken imports, type errors, edge cases).
- **Documentation clarifications** — typos, broken links, sections that don't match the paper.
- **Reference-implementation extensions** that demonstrate ARIA against a new domain (a self-contained working example under `examples/` with its own README).
- **Replay-procedure improvements** — if you re-run the ablations on your own ARIA deployment and discover the algorithm needs to handle a case it currently misses, that's a useful PR.
- **Backend adapters** — concrete `LocalRunner`, `CloudRunner`, `CriticClient` implementations against specific providers, contributed as plug-in subpackages.

## What's out of scope here

- **Changes to paper claims.** This repo is the paper's companion code, not the paper itself. If you believe a claim in the paper is incorrect, please open a GitHub Issue with the specific quote and the evidence, and the authors will respond before any code change lands.
- **Pull requests that depend on private partner-team data.** Sanitization happens at the publication boundary. PRs that include raw production data, internal codenames, or pre-publication scientific results will be closed without review.
- **Fork-and-forget rewrites.** If you want to build a substantially different agent architecture, the Apache 2.0 license lets you do that in your own repo without needing to upstream the changes.

## Development setup

```bash
git clone https://github.com/BioInfo/aria-paper.git
cd aria-paper
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Lint + format
ruff check kernel/ tools/ examples/
ruff format kernel/ tools/ examples/

# Tests (when added)
pytest
```

## PR checklist

Before submitting a PR, please:

1. **Run `ruff check`** — the repo enforces ruff defaults plus a 100-character line length.
2. **Add or update a test** if you're changing kernel behavior.
3. **Update the relevant doc** if you're changing an interface (README for surface-level changes, `docs/architecture.md` for kernel-shape changes).
4. **Keep the commit history clean** — squash work-in-progress commits before pushing.
5. **Reference the paper section** in the PR description if your change is paper-relevant (e.g. "implements §3.5 self-healing for OOM detection").

## Issue templates

Open an issue if you:

- Find a discrepancy between the paper and the code.
- Hit a bug when running the kernel.
- Want to propose a new feature larger than a few hundred lines (we'd rather discuss the shape before you write the code).

## Code of conduct

Be kind. Engage with substance. Assume the other person is acting in good faith. If a thread heats up, take it offline.

## License of contributions

By submitting a PR you agree that your contribution is licensed under the same [Apache License 2.0](LICENSE) as the rest of the repository. No CLA required.
