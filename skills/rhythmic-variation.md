# Rhythmic Variation

## Purpose

Transform a rhythmic identity without replacing its contour.

## Use when

- vary a rhythm while preserving its identity

## Do not use when

- when the source rhythm is too short to identify a pattern

## Inputs

- meter, beat position, note values, or a rhythmic pattern
- a pulse or dance context when relevant

## Outputs

- a rhythmic interpretation
- candidate transformations that retain the source identity

## Procedure

1. Extract the essential onset pattern.
2. Choose one controlled variable to alter.
3. Compare the variant with the source at matched phrase positions.

## Hard constraints

- Do not change duration and accent independently without stating why.
- Keep the meter reference constant.

## Heuristics

- Use displacement, subdivision, or omission as separate tools.
- Preserve one recognizable anchor per phrase.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- Turning a rhythm into an unrelated groove.
- Claiming identity when only tempo changed.

## Examples

- A dotted pattern rephrased in syncopated subdivisions.
- A repeated cell with a changed final accent.

## References

- Open Music Theory: rhythmic variation
- MIDI 1.0 timing concepts
