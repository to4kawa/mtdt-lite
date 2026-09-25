# Phrase Arc

## Purpose

Locate phrase tension, release, and cadence by time.

## Use when

- analyze phrase arc and cadence placement

## Do not use when

- when no phrase boundary or temporal context is available

## Inputs

- a motive, phrase, or melodic contour
- a stylistic and tonal context

## Outputs

- contour observations
- candidate developments or phrase plans

## Procedure

1. Segment the line at plausible boundaries.
2. Mark tension and release landmarks.
3. Relate the arc to harmonic and rhythmic evidence.

## Hard constraints

- Do not call every high note a climax.
- Keep phrase analysis distinct from formal-section analysis.

## Heuristics

- Use cadence and breath as strong phrase evidence.
- Prefer a small number of defensible landmarks.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- Over-segmenting a single long phrase.
- Ignoring a cadence that contradicts the assumed arc.

## Examples

- An eight-bar phrase with a late cadence.
- A sub-phrase ending on a weaker harmony.

## References

- Open Music Theory: phrases and form
- Caplin, Classical Form (library reference)
