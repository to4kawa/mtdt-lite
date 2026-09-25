# mtdt-lite P1 Implementation Report

日付: 2026-09-25
状態: 実装済み
公開リポ: https://github.com/to4kawa/mtdt-lite
レイアウト: スタンドアロン（親リポの `tools/mtdt-lite/` をルートに展開）

## 変更内容

- `skills/` に英語正文36枚を追加。11カテゴリ、JSON index、body/catalog SHA-256を固定。
- `check_shelf.py` を追加。Python標準ライブラリのみ、read-only、AST self-scan、終了コード1/2/3/4/5を実装。
- `tests/` にselection fixtureとunittestを追加。11カテゴリ、not_when除外、mode/category filter、負例を確認。
- `docs/spec.yaml` と `docs/spec.test.yaml` を実装済み状態で同梱。

## なぜこの形にしたか

P1はスコアエンジンを作らず、美術判断と機械的検査を分離した検査可能なスキル棚を先に固定する。P1では全カードを`draft`、ops/validatorsは未実装またはadvisoryのままにし、存在しない検査を検査済みと表示しない。P2でJSON score model、operation registry、validatorを別行導入する。

## 検証

本リポのルートで:

```bash
python3 check_shelf.py --root skills --check
python3 check_shelf.py --root skills --selection-fixture tests/fixtures/selection_cases.json
python3 -m unittest discover -s tests -p "test_*.py"
```

- `--check`: exit 0
- `--selection-fixture`: exit 0
- unittest: 14 tests, OK
- 36 ID、11カテゴリ件数、必須12セクション、BOM/CRLF、hash、依存参照、AST import、終了コード優先順位を検証。
- P1はPython標準ライブラリのみ。cargo / bridge / network / LLM / credential は使っていない。

## 残りリスク

- selection smokeは正確なtrigger phrase中心であり、将来controllerのLLM選択品質を保証するものではない。
- P2以前のscore JSON、operation registry、実validator、MusicXML/MIDI往復は未実装。
- cardのpublic referenceと音楽理論の記述はoperator review対象。P3で実validatorとSATB縦断スライス着手時に再検証する。
- 本P1ではbridge route、音声生成、PDF engraver、deployは行っていない。

## Artifacts（本リポ）

- Draft: `docs/draft.md`
- Spec: `docs/spec.yaml`
- Test spec: `docs/spec.test.yaml`
- Report: `docs/report-p1.md`
- Tool root: `。`（`check_shelf.py` / `skills/` / `tests/`）
