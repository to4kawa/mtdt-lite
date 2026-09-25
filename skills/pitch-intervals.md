# Pitch Intervals

## Purpose

Measure and interpret intervals between notes or chord tones.

## Use when

- analyze pitch intervals

## Do not use when

- when only a chord label is available

## Inputs

- pitch, interval, key, or meter context
- a notation or audio-derived description when available

## Outputs

- normalized musical vocabulary
- a concise explanation of relationships

## Procedure

1. Normalize both pitches.
2. Calculate the simple or compound interval.
3. Relate the interval to contour, harmony, or tuning context.

## Hard constraints

- Keep interval class and spelled interval distinct.
- Do not infer a function without harmonic or melodic context.

## Heuristics

- Use enharmonic spelling to explain function when useful.
- Report compound intervals transparently.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- Counting semitones while ignoring spelling.
- Calling every third consonant regardless of context.

## Examples

- A minor third above C.
- A compound sixth spanning an octave.

## References

- Open Music Theory: intervals
- Music theory fundamentals: interval quality and size
