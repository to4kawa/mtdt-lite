# Wind Pairing

## Purpose

Pair wind parts for blend, balance, and articulation.

## Use when

- pair wind instruments by blend and register

## Do not use when

- when the score has no wind parts or range data

## Inputs

- instrument roster and roles
- register, texture, and balance constraints

## Outputs

- instrumentation and texture choices
- candidate part assignments

## Procedure

1. Compare ranges and timbral colors.
2. Assign functional roles.
3. Check entrances, releases, and dynamic balance.

## Hard constraints

- Do not treat timbre as a substitute for balance.
- Keep pairing compatible with declared technique.

## Heuristics

- Use mixed timbres for color, not to hide missing parts.
- Test pairs across the full dynamic range.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- A blend that disappears at soft dynamics.
- An exposed pairing that masks a principal line.

## Examples

- Flute and oboe color pairing around a clarinet line.
- Low brass support under a horn melody.

## References

- Orchestration texts: woodwind and brass pairing
- MIDI 1.0 instrument and channel conventions
