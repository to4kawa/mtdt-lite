# AGENTS.md - mtdt-lite workflow

## Overview

An inspectable skill shelf for score (music-notation) work with LLMs.
P1 = the shelf (36 cards, index, checker). P2 = score JSON model, op
registry, mechanical validators, CLI. Every change flows through:

**Design document → Specification → Implementation → Test → Report → Commit**

## Workflow phases (files)

1. **Design**: `docs/draft-<phase>.md` — goal, users, constraints, inputs/outputs,
   done criteria, RAT-first experiment, unknowns. No implementation detail.
2. **Specification**: `docs/spec-<phase>.yaml` + `docs/spec-<phase>.test.yaml`
   — acceptance criteria must not be vague. Spec is required BEFORE code.
3. **Implementation**: `mtdt.py`, `update_index.py`, `engine/`, `check_shelf.py`.
4. **Test**: `tests/` (unittest + fixtures). Gate = the three commands below,
   all exit 0.
5. **Report**: `docs/report-<phase>.md` — what changed → why → how verified →
   residual risks. Append, never rewrite unrelated reports.
6. **Commit**: stage only intended files (`git status --short` first), then run
   the gate. `git diff --check` must pass.

Phase is "done" only when its gate passes. Skip a phase only with the reason
written in the report.

## Environment (Windows, PowerShell)

- `chcp 65001` and `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`
  before running commands that print non-ASCII.
- **ALL text files: UTF-8 without BOM, LF line endings.**
- **NEVER** use PowerShell `Out-File` / `>` redirection for file content (BOM
  or CP932 corruption). Create files with the Write tool or
  `[IO.File]::WriteAllText($path, $content, [Text.UTF8Encoding]::new($false))`.
- **NEVER** nest double quotes inside a double-quoted `pwsh -Command "..."`.
  For anything complex: write a temp `.ps1` and run `pwsh -File`, or use the
  Write tool. `tests/` may use `subprocess` in Python instead.
- Never write a literal secret into any file in this repo. This repo needs no
  credentials at all.

## Command gate (run before every commit)

```powershell
python3 check_shelf.py --root skills --check
python3 check_shelf.py --root skills --selection-fixture tests/fixtures/selection_cases.json
python3 -m unittest discover -s tests -p "test_*.py"
git diff --check
```

All four must pass. `check_shelf.py` exit codes: 0 ok, 1 usage, 2 schema/file,
3 hash drift, 4 count/dependency/selection, 5 banned production import/call.

## Index rules (CRITICAL)

- `skills/index.json` is canonical, hash-pinned (`body_sha256`,
  `catalog_sha256`). A single wrong byte fails `--check` with exit 3.
- **Never hand-edit `skills/index.json`.** Metadata changes to card `ops` /
  `validators` go through `update_index.py` (`--rehash`, `--add-op`,
  `--remove-op`, `--add-validator`, `--remove-validator`). It validates the
  candidate index against the shelf contract and refuses to write anything
  that would fail `check_shelf.py`.
- Card `status` stays `draft` and card `ops`/`validators` implementation stays
  `unimplemented`/`advisory` until P3 relaxes the shelf contract (see
  `docs/spec.yaml` p1 locks). The registry may be implemented while cards are
  unwired; wiring is P3.

## Hard rules

- **stdlib only**: `mtdt.py`, `update_index.py`, `engine/*`, `check_shelf.py`
  import nothing outside the stdlib allowlist declared in
  `docs/spec-p2.yaml`. No network, no LLM, no credentials, no subprocess in
  production files. Enforced by `tests/test_engine.py` import-boundary tests
  and by `check_shelf.py` self-scan (exit 5).
- **no silent checks**: an unimplemented or skipped check must be reported
  visibly (e.g. an `info` finding), never presented as passed.
- **`check_shelf.py` is frozen P1 contract**: do not loosen its locks (36
  cards, all `draft`, `unimplemented` ops, no `implemented` anywhere) without
  an explicit P3 spec change.
- Card bodies: English, 12 required H2 sections, no CJK, one card per file.
  The shelf checker enforces all of this.

## Layout

```
check_shelf.py        # P1 shelf checker (frozen contract, read-only)
mtdt.py               # P2 CLI: select / validate / normalize / ops / validators
update_index.py       # sanctioned index writer (validates before writing)
engine/               # score model, op registry, validators, registry.json
skills/               # 36 card bodies + index.json (hash-pinned)
tests/                # unittest suite + fixtures (selection + scores)
docs/                 # drafts, specs, reports
```

## Commit messages

Style: `docs: ...`, `feat: ...`, `chore: ...`. Include the spec version for
code changes, e.g. `feat: P2 score model + op registry (v0.2.0)`.
