# Note Values and Metric Placement

## Purpose

Read note values and their relationship to the meter.

## Use when

- identify note values and metric placement

## Do not use when

- when the timebase is unavailable or intentionally free

## Inputs

- meter, beat position, note values, or a rhythmic pattern
- a pulse or dance context when relevant

## Outputs

- a rhythmic interpretation
- candidate transformations that retain the source identity

## Procedure

1. Identify the beat unit.
2. Classify each onset by metric strength.
3. Mark rests and ties that alter the perceived duration.

## Hard constraints

- Do not equate written duration with perceived duration without evidence.
- Keep note-value arithmetic separate from articulation.

## Heuristics

- Use metric strength to explain accents and phrase placement.
- Show the calculation when a tuplet or tie matters.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- Misreading a tied duration as repeated attacks.
- Confusing a subdivision with a beat change.

## Examples

- A dotted rhythm across a barline.
- A triplet that preserves the underlying pulse.

## References

- Open Music Theory: note values and meter
- MIDI 1.0 timing concepts
