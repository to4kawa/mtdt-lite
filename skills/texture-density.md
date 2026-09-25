# Texture Density

## Purpose

Check whether texture supports the musical hierarchy.

## Use when

- check orchestration texture density

## Do not use when

- when only a reduction or sketch is available and instrumentation is unknown

## Inputs

- instrument roster and roles
- register, texture, and balance constraints

## Outputs

- instrumentation and texture choices
- candidate part assignments

## Procedure

1. Identify principal and supporting layers.
2. Measure active layers by time span.
3. Identify moments where density hides the intended line.

## Hard constraints

- Do not treat more active parts as automatically better.
- Keep density and balance as separate findings.

## Heuristics

- Use register, articulation, and duration to estimate weight.
- Reduce density before adding another layer.

## Validation status

P1 has no implemented engine validator for this card. Treat every result as advisory until P2 provides named operations and validators; do not describe an unimplemented check as performed.

## Failure modes

- A melody buried under sustained inner parts.
- Counting parts without checking their roles.

## Examples

- A dense tutti followed by a transparent solo response.
- A three-layer texture with a clear principal line.

## References

- Orchestration texts: texture and balance
- MIDI 1.0 instrument and channel conventions
