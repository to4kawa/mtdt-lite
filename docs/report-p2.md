# Report P2 — score model, op registry, mechanical validators, CLI

日付: 2026-09-25
状態: 完了
対象: `docs/draft-p2.md` → `docs/spec-p2.yaml` (v0.2.0) → `docs/spec-p2.test.yaml`

## 何が変わったか

**新規ファイル**

| ファイル | 内容 |
|---|---|
| `AGENTS.md` | standalone repo のワークフロー規約（6段階フロー、4ゲート、index rules） |
| `docs/draft-p2.md` | P2 設計文書（RAT 表を事前登録） |
| `docs/spec-p2.yaml` | P2 仕様（score schema / registry / validators / CLI / update_index / import境界） |
| `docs/spec-p2.test.yaml` | P2 テスト仕様（13件） |
| `engine/score.py` | 厳密 exact-keys の JSON スコアモデル: parse / validate / canonical serialize |
| `engine/ops.py` | `OPS_IMPL`: score-load / score-normalize / score-validate（3本すべて実装） |
| `engine/validators.py` | `Finding` + measure-fill / voice-range / note-overlap + 決定的ソート |
| `engine/registry.json` | 機械可読メタデータ（3 ops + 3 validators、exact-keys、id ソート済み） |
| `engine/registry.py` | registry ローダ（構造検証 + コード↔JSON 完全同期チェック） |
| `mtdt.py` | CLI: select / validate / normalize / ops / validators |
| `update_index.py` | index の唯一の公的 writer（default dry-run、`--apply` で書込） |
| `tests/test_engine.py` | P2 suite（schema 負例、CLI exit、registry 同期、境界 AST、update_index、encoding） |
| `tests/fixtures/scores/*.json` | RAT 譜例5枚（good-chorale / good-melody / bad-underfull / bad-range / bad-overlap） |

**変更ファイル**

- `tests/test_check_shelf.py`: `NON_TOOL_TOP` に `AGENTS.md`、`test_source_layout`
  の expected に P2 ファイル一式（mtdt.py / update_index.py / engine/* /
  tests/test_engine.py / スコア fixtures 5枚）を追加。
- `docs/spec.test.yaml`: notes に P2 layout 拡張の addendum（P1 の
  "no extra source files" 表記は P1-as-shipped である旨）。
- `README.md`: P2 セクション（CLI、exit code、update_index 手順）追加。
- `docs/spec-p2.yaml` / `docs/spec-p2.test.yaml`: 実装・実行完了に伴い
  `status: draft → implemented`。

**変更していないもの（P1 凍結）**

- `check_shelf.py`（バイト単位で不変。36カード / 全 draft /
  ops=unimplemented / validators∈{unimplemented, advisory} ロックも不変）
- `skills/index.json` と36カード本文（P2 期間中のコミット履歴になし）

コミット: `02121bd` (AGENTS.md) → `2cd6a5e` (P2 draft+specs) →
`71a1829` (feat v0.2.0) → 本ドキュメントコミット。

## なぜ

P1 は「棚」だけだった。P2 はその棚に**決定的エンジンの最小実装**を接続し、
「LLM を介さずにスコアを読み、機械チェックし、正規化し、カードを選ぶ」を
再現テスト可能にするためのフェーズ（`docs/draft-p2.md` Goal）。

設計判断の要点（spec-p2 の根拠）:

1. **check_shelf.py 凍結** — P1 の検査可能性ロックを P2 でも維持。P2 ファイルの
   境界は `tests/test_engine.py` の AST テストが担保（self-scan は拡張しない）。
2. **registry は二層**（コード `OPS_IMPL`/`VALIDATORS` + `registry.json`）—
   将来の controller は JSON を読み、実行はコードが担う。ドリフトはロード時
   検証とテストの両方で検出。
3. **バリデータは機械的3本のみ** — 対位法・voice crossing は判断の余地が
   あるため P3。range 未宣言は **info finding で可視スキップ**（no silent checks）。
4. **CLI のみ、LLM なし** — select は P1 の決定的 matcher をそのまま再利用。
5. **update_index は検証してから書く** — default dry-run。P1 ロック違反候補
   （`implementation: implemented` など）は exit 2 で拒否・ファイル無変更。
   これは P3 までカードを wired にしないという設計の正常動作。
6. **exit code 0/1/2/3** — usage/internal、file/schema/registry、
   error-severity findings を分離（info は exit を変えない）。

## どう検証したか

- **RAT（実装前事前登録 → 初回実行で 5/5 一致）**: `docs/draft-p2.md` の表の
  とおり findings（validator/part/severity）と CLI exit（0/0/3/3/3）が一致。
  スキーマ改訂は不要だった（失敗条件には至らず）。
- **4ゲート全緑**: `check` exit 0 / `--selection-fixture` exit 0 /
  unittest **60 tests OK** / `git diff --check` clean。
- **負例で exit mapping を実証**（spec-p2.test.yaml の名前で）:
  - `score-schema-negatives`: 29件のスキーマ違反（float/bool/余分キー/
    midi 範囲外/measure overflow/重複 part id/0分母/duplicate JSON key など）
    がすべて `ScoreError` → CLI exit 2。
  - `cli-exit-code-mapping`: 0（正常・info のみ・空選択）/ 1（usage）/ 2
    （欠損ファイル・スキーマ違反・unknown op・壊れた shelf の select）/
    3（error findings）を subprocess で確認。`mtdt.py` の書込ゼロも検証。
  - `update-index-refusal` / `update-index-apply`: implemented 拒否で
    **ファイルバイト同一**、dry-run 書込ゼロ、apply 後に
    `check_shelf --check` exit 0、remove-op で元バイトへ完全復元、
    `--rehash` 冪等。
  - `import-boundary`: 全 P2 生産ファイルが閉じた allowlist 内、
    seeded 混入（`import socket` / `os.system` / `eval`）が検出されることを
    ネガティブに確認。テストファイルは network/LLM import ゼロ。
  - `normalize-idempotent`: 冪等・part 順序保存・分数正規化（`2/4`→`1/2`,
    `4/4`→`1`）。
  - `registry-schema-and-sync`: 3+3、id ソート、双向同期、drift 負例。
- **P1 凍結の確認**: P1 の3コマンドは P2 追加後も exit 0、`check_shelf.py`
  は P2 期間で無変更。

### spec からの逸脱

なし。確認事項2つ（いずれも spec 本文の記載どおりの実装で、変更は不要）:

- voice-range の registry severity は `error` だが、range 未宣言の skip
  通知は spec-p2 が明示的に carve-out した `info`（finding_shape.severity 注記）。
- update_index の引数欠如・enum 値違反は usage（exit 1）、「操作の組み合わせ」
  違反（2操作同時、--rehash+--card、--card 単独）は exit 2 — spec の
  exit_codes / errors 表記に対応。

## 残リスク

1. **registry ↔ コードのドリフト**は gate（unittest）を回した時のみ検出される。
   ロード時同期チェックがあるので実行時は exit 2 で可視化されるが、
   gate を通さない手元編集はそれがまで耐えない。運用ルール（AGENTS.md の
   コミット前ゲート）で吸収。
2. **select は実行のたびに shelf 全体チェック**（36 body の hash 照合）を
   行う。現状は ms 想定だが、実測で遅ければ P3 で最適化。
3. **update_index の書込中断**が `index.json.tmp` を残す最悪ケース:
   shelf layout check が exit 2 で可視検出する（silent ではない）が、
   手動クリーンアップが要る。
4. **6/8 等の特殊拍子の coverage 算術は未検証**（RAT は 4/4 と 3/4）。
   whole-note 基準の単位換算が正しい前提。P3 フィクスチャで担保。
5. **P2 生産ファイルは check_shelf の self-scan 対象外**（P1 凍結の帰結）。
   保証は `tests/test_engine.py` の AST テストのみ。
6. **カードは unwired のまま** — registry は実装済みだが、36カードの
   ops/validators は unimplemented/advisory、status は全 draft。
   wiring と status 選抜は P3 の仕様変更が前提。

## 次フェーズ（P3）への引き継ぎ

- SATB 縦断スライス: カード wiring（status `draft → validated`）、対位法
  （平行5度・8度）・voice crossing バリデータ、controller/worker 有界ループ。
- P1 の `implementation: implemented` ロック解除は **P3 spec 変更でのみ**。
