# Voice Leading Rules

## Purpose

Check smooth and intelligible motion between voices.

## Use when

- check voice leading between chord tones

## Do not use when

- when only a single melodic line exists

## Inputs

- two or more independent voices
- a fixed cantus or melodic line when applicable

## Outputs

- candidate voice lines or voice-leading decisions
- a list of independence risks

## Procedure

1. Track each voice between sonorities.
2. Classify motion, interval, and crossing.
3. Report the highest-risk transition first.

## Hard constraints

- Do not treat all contrary motion as automatically correct.
- Keep voice crossing separate from spacing.

## Heuristics

- Prefer common tones and small steps when function permits.
- Explain exceptions rather than silently normalizing them.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- Losing track of a voice through a rest.
- Confusing a chord inversion with voice crossing.

## Examples

- A four-part cadence with contrary outer voices.
- A texture with a brief crossing in an inner voice.

## References

- Open Music Theory: voice leading
- Fux, Gradus ad Parnassum (public-domain edition)
