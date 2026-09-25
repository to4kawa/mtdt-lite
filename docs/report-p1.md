# mtdt-lite P1 Implementation Report

日付: 2026-09-25
状態: 実装済み

## 変更内容

- `tools/mtdt-lite/skills/` に英語正文36枚を追加。11カテゴリ、JSON index、body/catalog SHA-256を固定。
- `tools/mtdt-lite/check_shelf.py` を追加。Python標準ライブラリのみ、read-only、AST self-scan、終了コード1/2/3/4/5を実装。
- `tools/mtdt-lite/tests/` にselection fixtureとunittestを追加。11カテゴリ、not_when除外、mode/category filter、負例を確認。
- `specs/mtdt-lite.yaml` と `specs/mtdt-lite.test.yaml` を実装済み状態へ更新。

## なぜこの形にしたか

P1はスコアエンジンを作らず、美術判断と機械的検査を分離した検査可能なスキル棚を先に固定する。P1では全カードを`draft`、ops/validatorsは未実装またはadvisoryのままにし、存在しない検査を検査済みと表示しない。P2でJSON score model、operation registry、validatorを另行導入する。

## 検証

- `python3 tools/mtdt-lite/check_shelf.py --root tools/mtdt-lite/skills --check`: exit 0
- `python3 tools/mtdt-lite/check_shelf.py --root tools/mtdt-lite/skills --selection-fixture tools/mtdt-lite/tests/fixtures/selection_cases.json`: exit 0
- `python3 -m unittest discover -s tools/mtdt-lite/tests -p "test_*.py"`: 14 tests, OK
- 36 ID、11カテゴリ件数、必須12セクション、BOM/CRLF、hash、依存参照、AST import、終了コード優先順位を検証。
- P1はPython標準ライブラリのみで、cargo/bridge/network/LLM/credentialは使用していない。
- repo fast gateは試行したが、並行作業中の無関係な`privobs-drills`/`log-stack` Draft追加により`build-draft-index --check`がstale。P1のために無関係なindexを生成・上書きしていない。

## 残りリスク

- selection smokeは正確なtrigger phrase中心であり、将来controllerのLLM選択品質を保証するものではない。
- P2以前的score JSON、operation registry、実validator、MusicXML/MIDI往復は未実装。
- cardのpublic referenceと音楽理論の記述はoperator review対象。P3で実validatorとSATB縦断スライス着手時に再検証する。
- 本P1ではbridge route、音声生成、PDF engraver、deployは行っていない。

## Artifacts

- Draft: `draft/mtdt-lite.md`
- Spec: `specs/mtdt-lite.yaml`
- Test spec: `specs/mtdt-lite.test.yaml`
- Tool: `tools/mtdt-lite/`
