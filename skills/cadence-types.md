# Cadence Types

## Purpose

Select a cadence that matches phrase function and register.

## Use when

- choose a cadence for a harmonic phrase

## Do not use when

- do not use the cadence checker

## Inputs

- chord tones or a harmonic progression
- key, meter, and phrase context

## Outputs

- Roman-numeral or function analysis
- candidate chord and cadence choices

## Procedure

1. State the local key and phrase goal.
2. Compare authentic, half, plagal, and deceptive options.
3. Check outer-voice arrival and inner-voice resolution.

## Hard constraints

- Do not choose a cadence by label alone.
- Keep a deceptive cadence distinct from a failed cadence.

## Heuristics

- Prefer the cadence with the clearest bass and soprano arrival.
- Use color only after the primary function is clear.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- Calling a half cadence authentic because both end on V.
- Forcing a perfect authentic cadence onto a non cadential phrase.

## Examples

- A soprano arrival on a V-I authentic cadence.
- A deceptive V-vi ending in a folk-like phrase.

## References

- Open Music Theory: cadences
- Kostka, Tonal Harmony (library reference)
