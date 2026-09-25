# Beaming and Dynamics Conventions

## Purpose

Apply consistent beaming and dynamic notation without changing musical intent.

## Use when

- apply beaming and dynamic conventions

## Do not use when

- when the source has no rhythmic or dynamic evidence at all

## Inputs

- musical content and notation context
- instrument transposition or layout requirements

## Outputs

- engraving decisions
- a readable notation or part plan

## Procedure

1. Group notes by metric and phrase hierarchy.
2. Place dynamics at musically meaningful points.
3. Check hairpins, accents, and text directions for collisions.

## Hard constraints

- Do not beam across a metric boundary without a clear editorial reason.
- Keep dynamic marks attached to the intended voice or event.

## Heuristics

- Use phrase motion to guide hairpin placement.
- Prefer fewer, clearer marks over redundant notation.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- Beaming that hides the beat.
- A dynamic mark attached to the wrong staff.

## Examples

- A phrase-shaped beam group in 4/4.
- A crescendo aligned with a rising melodic line.

## References

- MusicXML notation: beams and directions
- Open Music Theory: metric grouping
