# Melisma versus Syllabic Setting

## Purpose

Compare syllabic clarity with melismatic expressive options.

## Use when

- choose melisma or syllabic setting

## Do not use when

- when the text has no stable language or syllable boundaries

## Inputs

- lyrics or syllables
- melodic rhythm, accents, and language context

## Outputs

- syllable-to-note alignment
- candidate underlay and melisma choices

## Procedure

1. Identify word and phrase boundaries.
2. Compare rhythmic alignment and emphasis.
3. Recommend one setting and state the tradeoff.

## Hard constraints

- Do not maximize melisma without a textual or musical reason.
- Keep pronunciation requirements visible.

## Heuristics

- Use syllabic setting for intelligibility-critical text.
- Use a short melisma to emphasize a stable vowel or phrase.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- A word stretched over a long phrase without a clear vowel.
- One-note-per-syllable setting that obscures a natural accent.

## Examples

- A sustained final vowel at a cadence.
- A clear syllabic setting for a text-heavy verse.

## References

- MusicXML lyrics and syllabic elements
- Open Music Theory: text and melody
