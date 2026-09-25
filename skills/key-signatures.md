# Key Signatures

## Purpose

Identify key signatures and relate them to musical evidence.

## Use when

- identify key signatures and relative keys

## Do not use when

- when the tonality is deliberately modal or disputed

## Inputs

- pitch, interval, key, or meter context
- a notation or audio-derived description when available

## Outputs

- normalized musical vocabulary
- a concise explanation of relationships

## Procedure

1. Read the signature.
2. Compare major and minor evidence.
3. Separate key indication from local modulation.

## Hard constraints

- Do not call a key certain from the signature alone.
- Keep relative and parallel relationships distinct.

## Heuristics

- Use cadential and melodic evidence to confirm a tonal center.
- Mark ambiguous or modal passages explicitly.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- Assuming every signature implies the same tonal behavior.
- Ignoring a temporary modulation.

## Examples

- A signature with a deceptive cadence.
- A passage that shifts between relative keys.

## References

- Open Music Theory: key and scale relationships
- Music notation fundamentals: key signatures
