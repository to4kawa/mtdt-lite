# Draft P2: score JSON model, op registry, mechanical validators, CLI

日付: 2026-09-25
状態: 設計（P1 実装済みの上での P2 設計）
種別: 機能設計
出典: `docs/draft.md`（P0）、`docs/spec.yaml`（P1 implemented）、`AGENTS.md`

## Goal

P2 は mtdt-lite の**決定的エンジン最小実装**である。P1 のスキル棚
（36カード + index + check_shelf.py）の上に以下を追加する:

1. **検証済み JSON スコアモデル**（canonical representation の schema 確定）
2. **名前付き op レジストリ**（3本、実装済み、機械可読 `registry.json` 付き）
3. **機械的バリデータ3本**（measure-fill / voice-range / note-overlap）
4. **決定的 CLI**（select / validate / normalize / ops / validators）と
   **index の唯一の公的 writer**（update_index.py）

P2 の完成状態: LLM なしで「スコアを読み、機械チェックし、正規化し、棚から
カードを選ぶ」がすべて再現テスト可能になる。芸術的判断・カード wiring・
対位法チェックは P3 へ。

## RAT-first experiment（実装より先に）

**Unknown（外れたら計画が崩れるもの）**: スコア JSON schema に穴がないか —
つまり schema + 機械的3バリデータが、手書き譜例に対して「事前登録した
findings どおりに」純粋な関数として成立するか。

**実験**: `tests/fixtures/scores/` に手書き譜例5枚を置き、期待値を以下に
事前登録する（この表が成功/失敗条件。実装後に1枚でもズレたら schema を
改訂して本 draft を修正する — 実装側を期待値に合わせない）:

| fixture | 内容 | 事前登録 findings | CLI exit |
|---|---|---|---|
| `good-chorale.json` | 4/4 × 2小節、4声部（soprano/alto/tenor/bass）、全 part range 宣言、全 measure 満杯 | findings = `[]`（ゼロ） | 0 |
| `good-melody.json` | 3/4 × 1小節、単旋律、rest（`pitch: null`）1つ、range **未宣言** | 恰好 1件の **info**（voice-range の可視スキップ）。error はゼロ | 0 |
| `bad-underfull.json` | 4/4 × 2小節、2声部。melody は両小節満杯、harmony は小節1のみ（小節2が空） | 恰好 1件: `measure-fill` error（part=harmony, measure=2）。他ゼロ | 3 |
| `bad-range.json` | 4/4 × 1小節、1声部、range C4..G5 に G3 イベント1つ（他は range 内）、coverage 満杯 | 恰好 1件: `voice-range` error。他ゼロ | 3 |
| `bad-overlap.json` | 4/4 × 1小節、1声部、イベント `[0,1/2]` + `[1/4,1/4]` + `[1/2,1/2]`（union = 満杯） | 恰好 1件: `note-overlap` error（2番目のイベント）。measure-fill はゼロ | 3 |

- **成功条件**: 5/5 が上表どおり（findings の validator/part/measure/severity
  と exit code の一致）。
- **失敗条件**: 1枚でもズレる → schema に追加フィールドまたは緩和が必要。
  実装を止めて schema 改訂 → 本 draft の表と `docs/spec-p2.yaml` を先に修正。

## Decisions

1. **`check_shelf.py` は P1 凍結のまま。変更しない。**
   36カード / 全 draft / ops=unimplemented / validators∈{unimplemented,
   advisory} のロックも、self-scan の対象（check_shelf.py 自身のみ）もそのまま。
   P2 ファイルの境界（stdlib allowlist、banned call）は `tests/test_engine.py`
   の AST テストで担保する。
2. **レジストリは「Python コード + `engine/registry.json`」の二層**。
   - コード層: `engine/ops.py`（`OPS_IMPL`）、`engine/validators.py`
     （`VALIDATORS`）= 呼び出し可能な実体。
   - メタデータ層: `engine/registry.json` = 機械可読な宣言
     （id / severity / autofix / implementation / summary）。
   - `engine/registry.py` がロード検証し、**コード ↔ JSON の完全一致を
     テストで強制**（ドリフト検出）。
   - 実装言語は Python（P1 と同じ stdlib only を継続。Rust は非目標のまま）。
3. **CLI のみ。LLM コントローラは作らない。**
   `mtdt.py select` は `check_shelf.select_skills` の決定的 matcher を
   再利用（P1 の selection smoke と同じ正規化・スコアリング・top_k=3）。
4. **バリデータは機械的3本のみ**:
   - `measure-fill`: 全 part × 全 measure の union coverage（欠け=underfull）
   - `voice-range`: 宣言レンジ内の pitch 検査（未宣言 part は **info finding
     で可視スキップ** — no silent checks）
   - `note-overlap`: part 内の絶対時間オーバーラップ / 重複イベント
   - 対位法（平行5度・8度等）と **voice crossing は P3**（判断に議論が要るため）。
5. **カードは unwired のまま。** index の ops/validators は P1 ロック
   （unimplemented / advisory）のままで、registry の `implemented` と
   カードは無関係。カード↔registry の wiring と status 選抜は P3。
6. **exit code**: `0` 成功 / `1` usage・internal / `2` file・score schema・
   registry 違反 / `3` severity=error の findings あり。info findings は
   exit code を変えない。
7. **`update_index.py` は「検証してから書く」**。
   default は dry-run（候補を検証して報告のみ、書かない）、`--apply` で書込。
   候補は `check_shelf.validate_index` + `validate_bodies` + canonical
   シリアライズを通し、P1 ロック違反（例: op に `implementation: implemented`）
   を含む候補は **exit 2 で拒否・ファイル無変更** — これは不良入力に対する
   正常動作であり、P3 前に implemented を書ける仕組みは作らない。
8. **score schema は厳密（exact-keys）**。任意レベルの余分な/欠けたキーは
   schema error。分数は **int か `"n/d"` 文字列のみ（float 拒否）**、
   rest は `pitch: null`、bool は int として扱わない（`true` は不正な measure）。
9. **正規化（normalize）は同順維持**: parts / events の並び順は楽譜上の
   意味を持つため並べ替えない。正規化するのは分数表現（`"2/4"` → `"1/2"`、
   `"4/4"` → `1`）とシリアライズ（`sort_keys` + indent 2 + 末尾 LF）のみ。
   normalize の冪等性はテストする。

## Constraints

- **stdlib only**: P2 の生産ファイル（`mtdt.py` / `update_index.py` /
  `engine/*.py`）の import は `docs/spec-p2.yaml` の**閉じた allowlist**
  （`argparse, dataclasses, fractions, json, pathlib, re, sys` + local
  `check_shelf`, `engine`）の内のみ。network / LLM / subprocess / os / eval
  は禁止。`check_shelf.py` の self-scan は P1 どおり check_shelf.py 自身のみ。
- **no silent checks**: range 未宣言は info finding、未実装は registry に
  置かない（P2 は3本とも実装済み）、スキップは必ず可視。
- **check_shelf.py 凍結**: ロック緩和・コード変更なし。
- 決定性: 時計・乱数・ネットワーク・モデルなし。同入力なら同出力。
- 秘密情報なし（本 repo はクレデンシャルを一切要求しない）。
- UTF-8 without BOM / LF。PowerShell nested-quote 禁止（規約どおり、
  複雑な検証は `.ps1` か Write tool、Python テストは subprocess を使用）。

## Non-goals (P2)

- 対位法バリデータ（平行5度・8度）、voice crossing / spacing 検査
- MusicXML / MIDI の読み書き（interchange は将来フェーズ）
- LLM コントローラ・ワーカー・有界 revise ループ
- カード status の `draft → validated` 選抜、カード↔registry wiring（P3）
- Rust 実装、音声生成、PDF engraving、bridge レーン
- registry の autofix 実行（P2 は autofix=false 固定）

## Done criteria（P2）

1. `AGENTS.md` の4ゲート（3コマンド + `git diff --check`）が exit 0。
2. RAT 5/5 が事前登録どおり（上表）。
3. `docs/spec-p2.yaml` の acceptance をすべて満たす（負例テスト含む:
   exit code 0/1/2/3、schema 負例、update_index 拒否、import 境界の
   seeded violation 検出）。
4. `docs/report-p2.md` に「何が変わったか → なぜ → どう検証したか →
   残リスク」を記録し、逸脱（あれば）を明記する。
5. README に P2 のコマンドが載る。

## Unknowns / residual risk

- **スキーマの穴**（→ 上記 RAT で実装前に検証する。これが本 draft の
  RAT-first unknown）
- measure-fill の coverage 計算が 4/4 以外（3/4, 6/8）で正しいか
  （good-melody 3/4 で一部担保、6/8 は単位が whole-note 基準である点に注意）
- `registry.json` とコードの二重管理ドリフト（テスト同期で担保、
  ロード時の検証が甘い場合はここが残リスク）
- update_index の dry-run / --apply の運用 UX（失敗時に何を書かなかったか
  が stderr に十分出るか）
- select が shelf 全体チェック（36カードの hash 照合）を毎回行うコスト
  （数 ms 想定。実測が問題なら P3 で最適化）

## Promotion gate

P2 → P3 へ進む条件:

1. 本 draft の Decisions（check_shelf 凍結、registry 二層、機械的3本、
   exit code、unwired カード、update_index 拒否）が operator 承認
2. `docs/spec-p2.yaml` がレビュー済みで、受け入れ基準が曖昧でない
   （**P2 実装の前に spec が必須** — P1 と同じゲート）
3. 実装後: 4ゲート緑 + RAT 5/5 + `docs/report-p2.md` 完成

## Phases（P0 draft からの位置づけ）

- **P1**: スキル棚（完了、`docs/spec.yaml` implemented）
- **P2（本 draft）**: score JSON schema + op registry + 機械的3バリデータ +
  CLI + update_index
- **P3**: SATB 縦断スライス（カード wiring、status 選抜、対位法・voice
  crossing を含む >= 3 バリデータ、controller/worker）
- **P4**: 需要駆動のカード拡張

## Documents

- P1 spec: `docs/spec.yaml`（implemented、P2 では変更しない）
- P2 spec: `docs/spec-p2.yaml`（本 draft の承認後、実装前に確定）
- P2 test spec: `docs/spec-p2.test.yaml`
- P2 report: `docs/report-p2.md`（実装後に作成）
