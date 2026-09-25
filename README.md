# mtdt-lite

An inspectable **skill shelf** for score (music-notation) work with LLMs.

The idea: when an LLM makes score-related decisions, keep the reasoning split into
two layers — **inspectable skill cards** (what to consider, when, and the hard
constraints) and **deterministic engine operations / validators** (the mechanical
checks). The LLM is confined to the artistic-choice layer; it does not get to
declare a check "passed" that no engine ran.

This repo is **Phase 1 (P1)**: the skill shelf only. 36 cards across 11
categories, a machine-readable index, a read-only integrity checker, and a
selection fixture. The scoring engine, operation registry, and real validators
come in later phases — until then every card is `advisory`.

## Layout

```
check_shelf.py                 # read-only integrity checker (stdlib only)
skills/index.json              # machine-readable card index (id/category/mode/examples/effects/not_when)
skills/<id>.md                 # one card per file: Purpose / Use when / Procedure / Hard constraints / ...
tests/                         # unittest suite + selection fixture
docs/                          # design draft, spec, test spec, P1 report (from the originating repo)
```

## Using the shelf (read-only, in a prompt)

1. Read `skills/index.json` — 36 cards with id, category, mode, trigger-equivalent
   (`examples`/`effects`), and `not_when`.
2. Pick 1–3 cards that fit the task (use `not_when` to exclude).
3. Read the chosen `skills/<id>.md` and follow its Purpose / Use when / Procedure /
   Hard constraints / Failure modes.

Example: to analyze phrase tension and closure → pick `phrase-arc`, follow its
Procedure (boundary split → mark tension points → check against harmony/rhythm).

## Integrity check (only when editing files)

```bash
python3 check_shelf.py --root skills --check
python3 check_shelf.py --root skills --selection-fixture tests/fixtures/selection_cases.json
python3 -m unittest discover -s tests -p "test_*.py"
```

`exit 0` = OK. Exit codes `1/2/3/4/5` = ID mismatch / missing section / hash
mismatch / fixture violation / import violation. Stdlib only — no network, no
credentials, no build step.

## Constraints (important)

- **P1 cards are all `draft` / advisory.** Each card's *Validation status* says the
  engine validator is unimplemented — do **not** report a result as "validated".
- `composes_with` lets related cards be read together (e.g. `phrase-arc` +
  `texture-density`).
- 11 categories: foundations / harmony / counterpoint / melody / rhythm / form /
  orchestration / notation / playability / text_setting / production_export.

## Origin & clean-room note

Inspired **only** by the public description of Jeffrey Emanuel's `mtdt` (a Rust CLI
with 300+ skills; enumerate legal candidates, let the LLM make the artistic choice;
inspectable rather than black-box). The real `mtdt` is closed/commercial — this
project has **no access** to it and copies **none** of its skill text. Only the
concepts (shelf / selection / inspectability) are reconstructed clean-room.

## License

[CC0 1.0](LICENSE) — public domain dedication. Copy, modify, redistribute freely.
