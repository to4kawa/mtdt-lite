# report-p3: SATB vertical slice (v0.3.0)

## What changed

- P3 is the first end-to-end slice: a 4-bar SATB skeleton (soprano+bass fixed,
  alto/tenor whole-note rests) plus a discrete chord plan feeds the deterministic
  backtracking voicer (`engine/voicer.py`), which writes alto/tenor notes; 5
  mechanical validators judge the result; `mtdt.py voice-fill` emits
  `{score, findings}` with the P2 exit-code contract (0/1/2/3).
- Two new validators: `parallel-perfect` (similar-motion consecutive perfect
  fifths/octaves/unisons, pair evidence in message, `part: null`) and
  `voice-crossing` (strict adjacent-voice order at every sounding time, unisons
  legal, `part: null`). Finding 5-key shape frozen — the P2 suite passes with
  unmodified expectations (lock tests rewritten, not weakened).
- First card wiring: `parallel-motion-avoidance` → `parallel-perfect`,
  `voice-leading-rules` → `voice-crossing`, `satb-chorale-harmonization` →
  op `voice-fill`; all three `status: validated`. The other 33 cards are
  byte-identical (`draft`, empty ops/validators — asserted by test).
- P1 lock relaxed by P3 spec authorization (the handoff P2 recorded):
  `check_shelf.validate_record` allows `validated` iff every declared
  op/validator is `implemented` (metadata side only; the checker stays
  stdlib-only with no engine import), allows `implemented` in cards,
  `stable` stays forbidden. `update_index.py` gained `--status draft|validated`
  and refuses `--implementation implemented` for ids absent from the engine
  registry (typo guard).
- Tests: `tests/test_slice.py` (21 spec cases: plan schema, RAT voicing,
  adversarial fixtures, lifecycle + code linkage, CLI smoke, updater guards),
  `tests/test_slice_live.py` (skip-guarded bridge smoke, `RUN_LIVE_LLM=1`).
  Suite: 89 tests, all green (1 skip = live smoke without the env flag).

## Why

- P0 decision 10 defined P3 as the SATB slice with >=3 validators.
- Architecture A (discrete chord plan from the LLM + deterministic voicer) was
  chosen per the Perplexity consult 2026-09-25 (operator-delegated decision):
  it is the only option honoring P0 principle 5 (the LLM never emits raw note
  streams as an accepted result). B violates the principle; C shows no E2E.
  Adopted mitigations: chord-factor domains with stepwise priority, outer-voice
  chord-tone compatibility as the revise trigger, fail-early pair checks.
- Skeleton uses all-null rests instead of empty event arrays because
  `score.py` rejects empty `events` — zero schema churn, P2 untouched.
- Perplexity's "runtime imports only validated cards" was declined with reason:
  no engine consumer reads card bodies, so there is no import site; the
  mechanical linkage test (`test_validated_items_link_to_code`) plus the
  reject-invalid-scores integration test cover the intent.

## Verification

- RAT (pre-registered in draft-p3, implementation run after): voicer on
  `satb-skeleton.json` + `satb-chord-plan.json` (I vi IV V) returned exactly
  alto `[G3, A3, A3, B3]`, tenor `[C3, C3, C3, G3]`; `validate` exit 0,
  findings `[]`. PASS, no fallback needed. (The trace, not luck: lowest-first
  candidates with stepwise priority deterministically produce this voicing;
  the slot-4 backtrack off the tenor-bass fifth is exercised.)
- Adversarial: `satb-parallel.json` → exactly 1 `parallel-perfect` error
  (measure 2, soprano+alto fifths), `satb-crossing.json` → exactly 1
  `voice-crossing` error (measure 1), `satb-contrary.json` → exit 0 clean
  (contrary-motion fifths stay legal per the card's Hard constraints).
- P2 RAT table verified silent under the 2 new validators by hand-trace before
  coding (good-chorale boundaries never repeat class 0/7 in similar motion;
  single-part fixtures cannot trigger pair validators); suite confirms.
- CLI smoke (all exit codes observed): voice-fill good 0 / bad plan 2 /
  pitched alto 1 / out-file byte-equal (parsed) / ops without --plan 2 /
  ops with --plan 0 / validate parallel 3 / validate contrary 0 /
  validators lists 5 / update_index typo-guard 2 with bytes unchanged.
- Live demo (manual, 1 call, zero Go): `perplexity/default` was unreachable
  (lane ready=0, tab closed — a human step), so the demo ran on the ready
  `venice` lane (`kimi-k2-5`). It returned first-try clean plan JSON
  (I vi IV V); `parse_plan` + `fill_voices` reproduced the RAT voicing;
  `validate` errors `[]`. No revise round was needed (loop bound untested
  live; the incompatible-plan path is unit-tested via VoicerError).
- Gates: full suite exit 0; YAML parse + BOM/LF checks on docs and fixtures;
  `git diff --check`; `check_shelf --check` exit 0; push `main` ok.

## Residual risks

1. The voicer is a first-implementation backtracker: completeness holds only
   inside its rule set (full-measure events, major keys, complete chords,
   leading-tone cap). Odd skeletons fail loudly (VoicerError → exit 1), which
   is correct but means the revise loop's re-plan quality depends on the LLM.
2. Live revise loop exercised once, zero revise rounds. The skip-guarded test
   pins the shape, not the loop bound.
3. `update_index --apply` writes before its post-check (pre-existing P2
   behavior); dry-run-first remains the discipline.
4. Minor keys, spacing validator, notation rendering stay out (spec scope_out).

## Deviations

- One: skeleton representation changed from "empty alto/tenor" (draft wording)
  to all-null rests after `score.py` L159 (`events` must be non-empty) forbade
  it. Spec updated before implementation; no schema change resulted.
- One: no AST allowlist change was needed (`itertools` was pre-authorized in
  the draft but unused; production imports unchanged).
- One: `update_index --status` added (the sanctioned-writer rule forbade
  hand-editing the status flip). Covered by 3 new guard tests.
- Consult transport note: the design consult ran on `perplexity/default`
  (HTTP 200); an early HTTP 400 was my own malformed JSON (bare newline in a
  string), not a lane fault. The live slice demo fell back to the venice lane
  because the perplexity tab was closed mid-session.

## Handoff to P4

- Next slice candidates: minor-key chord math, spacing validator, or the
  bounded controller/worker loop with a live planner (the loop bound and the
  incompatible-plan revise path are the untested live parts).
- `stable` status is still unoffered; opening it needs a P4+ spec change.
- Live lane of record for planner smoke stays `perplexity/default`
  (skip-guarded test); venice was a same-shape substitute for the manual demo.
