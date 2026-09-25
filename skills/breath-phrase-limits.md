# Breath and Phrase Limits

## Purpose

Check breath, endurance, and phrase feasibility for wind or voice parts.

## Use when

- check wind breathing and phrase feasibility

## Do not use when

- when the part is an unpitched sound-effect sketch

## Inputs

- an instrument-specific part
- range, technique, endurance, and phrasing constraints

## Outputs

- feasibility findings
- candidate simplifications or redirections

## Procedure

1. Map phrase lengths to available breath.
2. Check high-register and dynamic demands.
3. Propose a respire, redistribution, or phrasing adjustment.

## Hard constraints

- Do not treat a written phrase as feasible without duration evidence.
- Keep musical phrasing and breathing choices linked.

## Heuristics

- Use phrase boundaries as the first place to test breathing.
- Prefer a musically meaningful respire over a mechanical split.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- A long phrase with no feasible breath point.
- A high-register crescendo that exceeds endurance.

## Examples

- A wind phrase respired at a cadence.
- A voice line adjusted at a textual boundary.

## References

- Orchestration texts: wind and voice technique
- Open Music Theory: phrasing
