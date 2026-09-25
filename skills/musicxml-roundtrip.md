# MusicXML Roundtrip

## Purpose

Check whether a MusicXML exchange preserves musical and layout intent.

## Use when

- validate a MusicXML roundtrip

## Do not use when

- when the source or target is an undocumented proprietary binary

## Inputs

- a validated musical source
- a target interchange or delivery format

## Outputs

- an export plan or validated interchange artifact

## Procedure

1. Record the source and target versions.
2. Compare parts, voices, ties, directions, and transposition.
3. Classify each difference as harmless, lossy, or blocking.

## Hard constraints

- Do not call a roundtrip lossless without comparing musical events.
- Keep layout-only differences separate from sounding differences.

## Heuristics

- Prefer canonical comparison over file byte comparison.
- Report a compact delta before proposing conversion changes.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- Dropping a direction or lyric syllable.
- Changing an instrument octave during export.

## Examples

- A score with tied notes and transposing parts.
- A layout-only change that leaves the sound equivalent.

## References

- W3C MusicXML specification: score-partwise
- MusicXML documentation: interchange best practices
