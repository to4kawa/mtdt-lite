# String Double Stops

## Purpose

Check whether string double stops are playable and idiomatic.

## Use when

- check string double stops and positions

## Do not use when

- when a part is a non-notational sketch with no string assignment

## Inputs

- an instrument-specific part
- range, technique, endurance, and phrasing constraints

## Outputs

- feasibility findings
- candidate simplifications or redirections

## Procedure

1. Assign the implied string pair.
2. Check position and bow feasibility.
3. Suggest a divisi or revoicing alternative.

## Hard constraints

- Do not assume a playable pair for every written interval.
- Keep technical substitutions explicit.

## Heuristics

- Prefer open strings or a practical position when idiomatic.
- Test the transition from the preceding note.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- A double stop that requires an impossible position shift.
- A written interval that sounds clearer as divisi.

## Examples

- A playable open-string double stop.
- A divisi alternative for a stretched position.

## References

- Orchestration texts: string technique
- MIDI 1.0 instrument and channel conventions
