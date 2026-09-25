# MIDI Export Basics

## Purpose

Prepare a musical source for a deliberate MIDI export.

## Use when

- export a score to MIDI

## Do not use when

- when the score depends on unpitched visual notation with no MIDI interpretation

## Inputs

- a validated musical source
- a target interchange or delivery format

## Outputs

- an export plan or validated interchange artifact

## Procedure

1. Confirm pitch, duration, tempo, and channel intent.
2. Resolve ties, repeats, and unpitched material.
3. Run a playback and event audit before delivery.

## Hard constraints

- Do not claim that MIDI preserves notation, layout, or expression.
- Keep channel and program decisions explicit.

## Heuristics

- Export the smallest arrangement that answers the delivery need.
- Use a roundtrip or event diff when fidelity matters.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- Dropping a repeat or misreading a tie.
- Treating MIDI as a print-score interchange format.

## Examples

- A four-part score exported as four channels.
- A repeat structure checked after export.

## References

- MIDI 1.0 Detailed Specification
- MIDI Association: MIDI device and file concepts
