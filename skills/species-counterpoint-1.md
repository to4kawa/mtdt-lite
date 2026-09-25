# First Species Counterpoint

## Purpose

Generate a first-species line against a fixed cantus.

## Use when

- write first species counterpoint above a cantus

## Do not use when

- when free chord texture is desired

## Inputs

- two or more independent voices
- a fixed cantus or melodic line when applicable

## Outputs

- candidate voice lines or voice-leading decisions
- a list of independence risks

## Procedure

1. Map cantus rhythm and metric positions.
2. Choose one consonant interval at each attack.
3. Prefer stepwise motion and a clear final cadence.

## Hard constraints

- Use one note against each cantus note in the species definition.
- Resolve dissonance according to the stated species convention.

## Heuristics

- Favor a varied contour over repeated neighboring steps.
- Use cadential adjustment only after the main pattern is sound.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- Creating parallel perfect intervals.
- Treating a passing dissonance as stable.

## Examples

- A consonant upper line over a stepwise bass.
- A cadence with a controlled imperfect interval.

## References

- Fux, Gradus ad Parnassum (public-domain edition)
- Open Music Theory: species counterpoint
