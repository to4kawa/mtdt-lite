# Secondary Dominants

## Purpose

Add a tonicizing dominant without losing the governing key.

## Use when

- apply secondary dominants with correct resolution

## Do not use when

- when modulation must remain strictly diatonic

## Inputs

- chord tones or a harmonic progression
- key, meter, and phrase context

## Outputs

- Roman-numeral or function analysis
- candidate chord and cadence choices

## Procedure

1. Identify the temporary function.
2. Check spelling and resolution.
3. Confirm the return or continuation of the main key.

## Hard constraints

- Do not apply a secondary dominant without a resolution.
- Keep the local tonicization distinct from a full modulation.

## Heuristics

- Use chromatic voice leading to make the tonicization clear.
- Choose the least disruptive enharmonic spelling.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- Labeling every chromatic chord as a secondary dominant.
- Leaving the temporary dominant unresolved.

## Examples

- V/V resolving to V in a major key.
- A brief applied dominant before a continuation.

## References

- Open Music Theory: tonicization
- Kostka, Tonal Harmony (library reference)
