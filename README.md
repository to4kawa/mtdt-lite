# mtdt-lite

An inspectable **skill shelf** for score (music-notation) work with LLMs.

The idea: when an LLM makes score-related decisions, keep the reasoning split into
two layers — **inspectable skill cards** (what to consider, when, and the hard
constraints) and **deterministic engine operations / validators** (the mechanical
checks). The LLM is confined to the artistic-choice layer; it does not get to
declare a check "passed" that no engine ran.

This repo currently spans **Phase 1 (P1)** — the skill shelf: 36 cards across
11 categories, a machine-readable index, a read-only integrity checker, and a
selection fixture — and **Phase 2 (P2)** — the deterministic engine: a strictly
validated JSON score model, a 3-op registry, 3 mechanical validators, and a
stdlib-only CLI — and **Phase 3 (P3, v0.3.0)** — the first end-to-end slice:
a discrete chord plan plus a deterministic backtracking voicer fill SATB inner
voices (`voice-fill`), judged by 5 validators including `parallel-perfect` and
`voice-crossing`; 3 cards are `validated`, 33 stay `draft` / advisory.

## Layout

```
check_shelf.py                 # P1 read-only integrity checker (stdlib only, frozen contract)
mtdt.py                        # CLI: select / validate / normalize / ops / validators / voice-fill
update_index.py                # sanctioned index writer (validates candidate before writing)
engine/                        # score model, op registry (registry.json), mechanical validators, SATB voicer
skills/index.json              # machine-readable card index (id/category/mode/examples/effects/not_when)
skills/<id>.md                 # one card per file: Purpose / Use when / Procedure / Hard constraints / ...
tests/                         # unittest suites (P1 shelf + P2 engine) + selection + score fixtures
docs/                          # drafts, specs, P1/P2 reports
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

## Engine CLI (P2)

```bash
python3 mtdt.py select "analyze pitch intervals" [--mode analyze] [--category foundations] [--format text|json]
python3 mtdt.py validate tests/fixtures/scores/good-chorale.json   # findings JSON on stdout; exit 3 on severity=error
python3 mtdt.py normalize tests/fixtures/scores/good-chorale.json  # canonical score JSON (idempotent)
python3 mtdt.py ops score-load tests/fixtures/scores/good-chorale.json
python3 mtdt.py validators                                        # registry metadata JSON
```

## Engine slice (P3)

```bash
python3 mtdt.py voice-fill tests/fixtures/scores/satb-skeleton.json tests/fixtures/plans/satb-chord-plan.json
# fills alto/tenor rests from the discrete chord plan (I vi IV V); emits {score, findings}; exit 3 on severity=error
python3 mtdt.py ops voice-fill tests/fixtures/scores/satb-skeleton.json --plan tests/fixtures/plans/satb-chord-plan.json
```

Exit codes: `0` ok, `1` usage/internal, `2` file/schema/registry violation,
`3` error-severity findings. Validators are mechanical only — `measure-fill`,
`voice-range`, `note-overlap`, `parallel-perfect` (similar-motion consecutive
perfect 5ths/octaves/unisons; contrary/oblique stay legal), `voice-crossing`
(strict adjacent-voice order; unisons legal). A part with no declared range
yields a visible `info` finding, never a silent pass. `select` runs the full
shelf check first (same contract as `--selection-fixture`).

## Updating the index (never hand-edit `skills/index.json`)

```bash
python3 update_index.py --card <id> --add-op score-load           # dry-run: validates, writes nothing
python3 update_index.py --card <id> --add-op score-load --apply   # validated write (canonical bytes)
python3 update_index.py --rehash --apply                          # recompute hashes after body edits
```

Every candidate is validated against the shelf contract before any write.
`--implementation implemented` is refused for ids absent from the engine
registry (typo guard), and `--status validated` is refused unless every
declared op/validator of the card is implemented — the file stays
byte-identical on refusal. `stable` is not offered (a later phase).

## Constraints (important)

- **33 cards are `draft` / advisory; 3 are `validated`.** Each unwired card's
  *Validation status* says its check is unimplemented — do **not** report such
  a result as "validated". Wired cards name their op/validator and version.
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
