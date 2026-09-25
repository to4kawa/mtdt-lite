# Clefs and Transposing Instruments

## Purpose

Translate sounding pitch and register into correct notation.

## Use when

- notate clefs and transposing instruments

## Do not use when

- when the instrument is defined as a non-transposing sound or the key is unknown

## Inputs

- musical content and notation context
- instrument transposition or layout requirements

## Outputs

- engraving decisions
- a readable notation or part plan

## Procedure

1. Identify sounding and written pitch.
2. Choose the clef for readable range.
3. Verify key signature and octave transposition.

## Hard constraints

- Never label written pitch as sounding pitch without stating the transposition.
- Check octave displacement separately from key transposition.

## Heuristics

- Prefer a clef that minimizes ledger lines while preserving context.
- Record the instrument transposition explicitly in metadata.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- Applying a B-flat transposition to a C instrument.
- Confusing octave displacement with a key change.

## Examples

- A horn part written in F with correct sounding pitch.
- A treble-to-bass clef change for a low part.

## References

- MusicXML notation: clef and transpose elements
- MIDI 1.0 instrument and channel conventions
