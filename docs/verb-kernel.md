# The Verb Kernel

This document is the reference for which verbs are valid in an ARIA instance and how to extend them.

## Universal-5 (kernel verbs)

Every ARIA instance ships with these five verbs. They cannot be shadowed by extensions.

| Verb     | Stage     | Use in commit subjects                       |
|----------|-----------|----------------------------------------------|
| DESIGN   | design    | `[DESIGN] <experiment_name> from idea_<id>`  |
| RUN      | run       | `[RUN] <experiment_name> local validation`   |
| ANALYZE  | analyze   | `[ANALYZE] <experiment_name> result summary` |
| CRITIQUE | critique  | `[CRITIQUE] <experiment_name> verdict <V>`   |
| DEBUG    | self_heal | `[DEBUG] <experiment_name> recovery for <mode>` |

Commit subjects use `[VERB]` brackets so the verb is greppable from the git log. Production deployments emit one verb per commit; multi-verb operations are split into multiple commits so the verb-distribution analysis can rely on it.

## Extension verbs

Instances register additional verbs for their domain. Extensions augment the universal-5 — they do not replace it. A few canonical extension verbs from the deployed instances:

| Verb        | Stage        | Used in                       |
|-------------|--------------|-------------------------------|
| SCOUT       | extension    | Competitive intelligence / market scan |
| SURVEY      | extension    | Literature survey before HYPOTHESIZE |
| HYPOTHESIZE | extension    | Idea generation before DESIGN |
| SYNTHESIZE  | extension    | Cross-experiment pattern extraction |
| BRIEF       | extension    | Weekly summary for the operator |
| ADVISE      | extension    | Recommendation surfaces to partner teams |
| PROMOTE     | extension    | Tier-2 manuscript draft from a completed result |
| CONSOLIDATE | extension    | Pool cleanup / dedup pass |
| CULL        | extension    | Explicit removal of stale / out-of-scope entries |

The paper reports that:
- The original `aria` ran 25 distinct verbs (heavy exploration mode).
- `aria-se` (medical imaging) converged on 24 verbs.
- The two enterprise pharma deployments compressed to 13–14 verbs each.

Verb compression is a maturity signal: as an instance's research mission sharpens, it drops verbs it isn't using (REFINE, INCORPORATE, MATURE) and concentrates time on execution.

## Registering an extension verb

```python
from kernel.verbs import Verb, register_verb

register_verb(Verb(
    name="HYPOTHESIZE",
    stage="extension",
    description="Generate candidate pool entries from open literature.",
))
```

Registration raises `ValueError` if the name shadows a kernel verb. The verb name appears in:

- Commit subjects (`[HYPOTHESIZE]`)
- Pool entry `status` fields
- `aria status --verbs` output
- The verb-distribution analysis in `evidence/verb_distribution.json`

## Verb composition rules

A few conventions production deployments follow:

- **One verb per commit subject.** Don't combine `[DESIGN+RUN]` — split into two commits. This is what makes the verb-distribution analysis tractable.
- **DEBUG is terminal.** A DEBUG commit closes a session. The recovery entry it writes will be picked up by the next session.
- **PROMOTE is producer-side.** A producer commits `[PROMOTE]` when a completed result is promoted to a tier-2 manuscript draft.
- **CRITIQUE is critic-side.** The producer never emits `[CRITIQUE]` — that comes from the cross-model critic agent.
