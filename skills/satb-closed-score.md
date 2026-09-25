# SATB Closed Score

## Purpose

Lay out a readable SATB closed score.

## Use when

- notate a SATB closed score

## Do not use when

- when the user needs a single condensed piano reduction instead of four independent parts

## Inputs

- musical content and notation context
- instrument transposition or layout requirements

## Outputs

- engraving decisions
- a readable notation or part plan

## Procedure

1. Assign voices to consistent ranges and directions.
2. Choose clefs and vertical spacing.
3. Verify every voice remains identifiable at each event.

## Hard constraints

- Do not hide voice crossing by reordering notes silently.
- Keep stems and beams readable at small sizes.

## Heuristics

- Use clef changes only when they improve the part.
- Align vertical events without erasing rhythmic differences.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- A soprano and tenor hidden on the same ledger region.
- A staff layout that makes eighth notes ambiguous.

## Examples

- A four-staff closed score with a cadence.
- A layout using a tenor clef to reduce ledger lines.

## References

- MusicXML notation: score-partwise
- Open Music Theory: four-part reading
