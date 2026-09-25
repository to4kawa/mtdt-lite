# Parallel Motion Avoidance

## Purpose

Find parallel perfect intervals and related independence failures.

## Use when

- detect parallel fifths and parallel octaves

## Do not use when

- when checking horizontal melodic intervals only

## Inputs

- two or more independent voices
- a fixed cantus or melodic line when applicable

## Outputs

- candidate voice lines or voice-leading decisions
- a list of independence risks

## Procedure

1. Pair voices across adjacent sonorities.
2. Check interval class and motion direction.
3. Report pairs with the exact time span.

## Hard constraints

- Do not call contrary similar perfect motion parallel.
- Include the voice-pair evidence in every finding.

## Heuristics

- Inspect all pairs, not only soprano and bass.
- Check ornamental reductions only when the score permits them.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- Skipping a pair because one note is an ornament.
- Confusing parallel fifths with a single perfect fifth.

## Examples

- Two voices moving from a fifth to another fifth.
- A contrary-motion perfect interval that remains legal.

## References

- Open Music Theory: contrapuntal motion
- Fux, Gradus ad Parnassum (public-domain edition)
