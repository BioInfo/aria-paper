"""The universal-5 verb kernel + extension registry.

Every ARIA agent instance shares five core verbs that map one-to-one onto
flywheel stages:

    DESIGN     — shape an experiment from a pool entry
    RUN        — execute the experiment (local or cloud)
    ANALYZE    — inspect the result and extract structured insight
    CRITIQUE   — adversarially review the result (cross-model)
    DEBUG      — classify a failure and write a recovery entry

Instances may register additional verbs (e.g. SCOUT, SURVEY, HYPOTHESIZE,
SYNTHESIZE, BRIEF, ADVISE) for their domain. The paper reports verb-cardinality
compression as a maturity signal: the original `aria` instance ran 25 verbs;
enterprise-domain instances converged on 13–14.

The verb registry is the single source of truth for which verbs are valid
in a given instance's commit messages and pool entries.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Verb:
    """A verb in the ARIA kernel.

    Attributes:
        name: Uppercase identifier (e.g. "DESIGN"). Appears in commit
              subject lines as `[DESIGN]` and in pool-entry status fields.
        stage: Which flywheel stage this verb belongs to. The universal-5
               verbs map one-to-one; extension verbs may map to any stage
               or have stage="extension".
        description: One-line human description for `aria status --verbs`.
    """

    name: str
    stage: str
    description: str


VERB_KERNEL: dict[str, Verb] = {
    "DESIGN": Verb(
        "DESIGN",
        "design",
        "Shape an experiment from a pool entry. Outputs a runnable config.",
    ),
    "RUN": Verb(
        "RUN",
        "run",
        "Execute the experiment. Local screening first, then cloud if it passes.",
    ),
    "ANALYZE": Verb(
        "ANALYZE",
        "analyze",
        "Inspect the result and extract structured insight back into the corpus.",
    ),
    "CRITIQUE": Verb(
        "CRITIQUE",
        "critique",
        "Adversarial cross-model review. Writes a verdict into share/from_critic/.",
    ),
    "DEBUG": Verb(
        "DEBUG",
        "self_heal",
        "Classify a failure and write a recovery pool entry. Self-healing path.",
    ),
}


_EXTENSION_VERBS: dict[str, Verb] = {}


def register_verb(verb: Verb) -> None:
    """Register an extension verb for the current instance.

    Extension verbs do not replace the universal-5; they augment them. The
    paper reports that aria-se converged on 24 verbs (5 core + 19 extensions),
    while the enterprise deployments compressed to 13–14 verbs total.

    Raises:
        ValueError: if the verb name shadows a kernel verb.
    """
    if verb.name in VERB_KERNEL:
        raise ValueError(
            f"{verb.name} is a kernel verb; extensions cannot shadow the universal-5."
        )
    _EXTENSION_VERBS[verb.name] = verb


def all_verbs() -> dict[str, Verb]:
    """Return the union of kernel + extension verbs."""
    return {**VERB_KERNEL, **_EXTENSION_VERBS}


def lookup(name: str) -> Verb | None:
    """Resolve a verb name (case-insensitive) to its Verb record."""
    return all_verbs().get(name.upper())
