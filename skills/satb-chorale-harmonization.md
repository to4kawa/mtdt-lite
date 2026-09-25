# SATB Chorale Harmonization

## Purpose

Create a four-part harmonization while keeping the outer voices coherent.

## Use when

- harmonize a soprano and bass as SATB

## Do not use when

- when the texture is monophonic or the form has no harmonic role

## Inputs

- chord tones or a harmonic progression
- key, meter, and phrase context

## Outputs

- Roman-numeral or function analysis
- candidate chord and cadence choices

## Procedure

1. Analyze the given soprano and bass.
2. Choose a functional progression.
3. Fill inner voices with smooth, complete chords and valid resolutions.

## Hard constraints

- Preserve the supplied outer voices unless a change is explicitly requested.
- Check every vertical sonority and transition.

## Heuristics

- Use common tones to reduce inner-voice motion.
- Make cadence choices audible in the outer voices.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- Adding an inner voice that destroys the phrase rhythm.
- Doubling a tendency tone without a declared exception.

## Examples

- A soprano-bass pair harmonized in four parts.
- A cadence with a controlled inner-voice resolution.

## References

- Open Music Theory: four-part writing
- Fux, Gradus ad Parnassum (public-domain edition)
