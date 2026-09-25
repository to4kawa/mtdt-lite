# Pitch Spelling and Scales

## Purpose

Identify pitch names, enharmonic alternatives, and scale membership.

## Use when

- spell pitches and identify scales

## Do not use when

- when enharmonic spelling is already fixed by a source

## Inputs

- pitch, interval, key, or meter context
- a notation or audio-derived description when available

## Outputs

- normalized musical vocabulary
- a concise explanation of relationships

## Procedure

1. Normalize the pitch collection into a named set.
2. Compare spelling choices against the harmonic context.
3. State scale membership and any ambiguity.

## Hard constraints

- Do not silently rewrite an author-specified spelling.
- Keep enharmonic explanations separate from sounding pitch.

## Heuristics

- Prefer the spelling that best explains function and voice leading.
- Call out a true enharmonic ambiguity rather than forcing certainty.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- Confusing a chromatic inflection with a scale-degree change.
- Ignoring the key or meter that changes the best label.

## Examples

- C major versus A minor pitch collections.
- A diminished-seventh spelling in a functional cadence.

## References

- Open Music Theory: pitch spelling and scale vocabulary
- Music notation fundamentals: pitch and scale reference
