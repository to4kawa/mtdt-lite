# Syllable Underlay Basics

## Purpose

Align syllables to notes while preserving text integrity.

## Use when

- align syllables to notes

## Do not use when

- when lyrics are absent or the text is deliberately abstract

## Inputs

- lyrics or syllables
- melodic rhythm, accents, and language context

## Outputs

- syllable-to-note alignment
- candidate underlay and melisma choices

## Procedure

1. Mark syllable stress and note timing.
2. Choose syllable boundaries that fit the language.
3. Check that every text unit is assigned exactly once.

## Hard constraints

- Do not split a word across an arbitrary beat without a reason.
- Keep unstressed syllables from obscuring the metric pulse.

## Heuristics

- Use natural stress and phrase boundaries as anchors.
- Prefer clear placement over one-to-one symmetry.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- A syllable assigned to a rest.
- A melisma that hides the word boundary.

## Examples

- A word split across a phrase boundary.
- A sustained vowel assigned to a melisma.

## References

- MusicXML lyrics and syllabic elements
- Open Music Theory: text and melody
