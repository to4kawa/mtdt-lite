# Draft: mtdt-lite — inspectable skill shelf for score work

日付: 2026-09-25
状態: 設計
種別: 機能設計

## Goal

LLMに楽譜（スコア）関連の判断をさせるとき、判断根拠を「検査可能なスキルカード」と
「決定的なエンジン操作/バリデータ」に分離し、LLMを芸術的選択者に限定する軽量フレーム
ワーク `mtdt-lite` を設計する。Phase 1 の成果物はスコアエンジンではなく**スキル棚
（skill shelf）のみ**。棚と機械可読インデックス、内容チェッカー、選択フィクスチャを
先に固め、エンジン実装はその後のフェーズに置く。

### 出典とクリーンルームの位置づけ

- 触発元は Jeffrey Emanuel が公開で語っている mtdt の**公開記述のみ**: Rust CLI +
  300+ skills、合法候補の列挙とLLMによる芸術的選択、ブラックボックスでなく検査可能
  という思想。
- 本物の mtdt はクローズド/商用。**アクセス権は持たない**と明示し、そのスキル本文を
  一切複製しない。本 draft は公開記述から得た概念（棚/選択/検査可能性）だけを
  クリーンルームで再構成する。用語・文章・カード構成の一致を狙わない。

### 命名

- 採用名: **`mtdt-lite`**。
- `polygen-score` と `muse_spark` は本概念とは無関係の名前衝突（既存 draft/素材の
  命名被り）であり、本プロジェクトの候補名・別名ではない。混同しないこと。

## Users

- repo operator（自分）: スキルカードを書き、棚を保守し、将来のエンジンで使う
- opencode 上の LLM レーン: 将来、コントローラ経由でスキルを選択・適用する側
- 将来の外部利用者: MusicXML/MIDI を持ち込み、検査可能な分析・候補を受け取る人

## Inputs / Outputs

### Inputs（Phase 1）

- スキルカード原稿（英語本文、Markdown、1カード1ファイル想定）
- カードメタデータ（下記 Decisions の選択メタデータ一式）

### Inputs（将来フェーズ）

- MusicXML / MIDI ファイル（外部 interchange）
- 内部は**検証済み JSON スコアモデル**を標準表現（canonical representation）として扱う

### Outputs（Phase 1）

- スキル棚: 36カード（シード、承認済み 30–50 レンジ内）
- 機械可読インデックス（カードメタデータの要約、日本語サマリ付き）
- カード内容チェッカー（メタデータ整合・必須項目の検査）
- 選択フィクスチャ（トリガ→選択カードの期待値テスト）

### Outputs（将来フェーズ）

- 分析レポート、または**合法候補操作IDのリスト**（LLM出力はこれに限定）
- MusicXML / MIDI への書き出し（interchange）

## Decisions

1. **Phase 1 の成果物はスキル棚のみ。スコアエンジンは作らない。**
   棚・インデックス・チェッカー・選択フィクスチャで Phase 1 を閉じる。
   エンジン（JSONスコアモデル、操作レジストリ、バリデータ）は P2 以降。
2. **シードは36カード**（承認済み 30–50 レンジ内）。カード本文は英語、インデックス
   のサマリは日本語。全文カードは本 draft では書かない（下記シード表のみ）。
3. **将来のLLM実行は既存の `opencode run` subprocess パターン**:
   `opencode run -m opencode-go/<model> --format json --pure ... -f <prompt-file>`。
   bridge ルートを新設しない。`API_SECRET` を要求しない。Phase 1 で候補ごとの
   LLM呼び出しは行わない。**Go クォータ/コストは制約**として扱う（下記 Constraints）。
4. **外部interchangeは MusicXML と MIDI。内部標準表現は検証済み JSON スコアモデル。**
   音声生成・ミックス/マスタリング・PDF engraving・LilyPond/MuseScore は v1 の外。
5. **中核安全原則: 決定的エンジン操作/バリデータが判定可能な規則を強制し、LLMは
   合法候補IDの中から選び、芸術的判断だけを行う。**
   LLMが生の音符ストリームを「受理される結果」として出力することは禁止。
   未実装の操作/バリデータは**明示的に advisory/unimplemented と表示**し、
   実在しない検査を検査として装うことを禁止（no silent checks）。
6. **コントローラ/ワーカー分離（高レベル設計）**:
   - コントローラはコンパクトなスキルインデックス（トリガメタデータのみ）を読み、
     **1–3枚のスキル**を選択する。
   - ワーカーに渡すのは: 選ばれたスキル本文のみ、スコアの要約/モデル、
     **名前付き操作レジストリ**。
   - ワーカー出力は「分析」または「候補操作ID」。
   - validate/revise は**有界ループ**（上限回数を明示、無限リトライ禁止）。
7. **スキルカテゴリは11種**。`analyze|generate|check|transform` はカテゴリではなく
   **モードfacet**として別軸で持つ。
   - `foundations`: 音名・音程・音価など共通基礎
   - `counterpoint`: **声部の独立性**（線対線）
   - `harmony`: **縦の響き・機能**（和声）
   - `melody`: 旋律の形状・動機
   - `rhythm`: 拍・リズム構造
   - `form`: 曲式・セクション構成
   - `orchestration`: **音色・テクスチャ**（楽器編成）
   - `playability`: **人間実行の実現可能性**（演奏可能性）
   - `notation`: **engraving・移調を含む記譜法**
   - `text_setting`: 歌詞のアンダーレイ（音節割り）
   - `production_export`: interchange・出力まわり
8. **選択メタデータ（カード1枚あたり）**:
   `id / title / category / mode / level / idiom / ensemble / status`、
   `use_when / not_when`、`inputs / outputs / preconditions / effects`、
   名前付きops、`validator IDs`（severity / autofix 付き）、
   `theory_refs / examples / failure_modes`、`requires / composes_with`、
   `schema_version / content hash`。
   **エンジン語彙（ops・validator ID・severity等）とスキル本文（内容）は明確に分離**
   する。語彙はレジストリ側で一元管理し、カードは参照するだけ。
9. **ライフサイクル: `draft → validated → stable`**。
   `validated` = カードが参照する名前付きops/バリデータが実装済みで、選択スモークが
   通ること。`stable` = 実運用で誤トリガ/誤適用が観測されないこと。
   数百カードへの成長は**需要駆動**。カタログ完成主義（数を揃える）はしない。
10. **将来の縦断スライス（vertical slice）: SATB コラールハーモニゼーション**。
    harmony / counterpoint / notation の3カテゴリ横断 + **最低3つのバリデータ**
    （例: 平行5度・8度検出、声域レンジ検査、声部間隔/交差検査）で
    エンドツーエンドを最初に通す。P3 の受け入れ基準とする。

### シード36カード表（カテゴリ別・目標枚数と代表例）

| category | 枚数 | 代表スキル名/例 |
|---|---|---|
| foundations | 4 | pitch-spelling-scales, pitch-intervals, key-signatures, metric-hierarchy |
| counterpoint | 4 | species-counterpoint-1, voice-leading-rules, parallel-motion-avoidance, dissonance-treatment |
| harmony | 5 | functional-harmony-basics, cadence-types, satb-chorale-harmonization, secondary-dominants, modulation-common-tone |
| melody | 4 | motive-development, melodic-contour, phrase-arc, sequence-technique |
| rhythm | 3 | note-values, syncopation-basics, rhythmic-variation |
| form | 3 | period-sentence, binary-ternary, theme-and-variation |
| orchestration | 3 | string-section-idioms, wind-pairing, texture-density |
| playability | 3 | piano-idiomatic-limits, string-double-stops, breath-phrase-limits |
| notation | 3 | satb-closed-score, clefs-and-transposing-instruments, beaming-dynamics-conventions |
| text_setting | 2 | syllable-underlay-basics, melisma-vs-syllabic |
| production_export | 2 | musicxml-roundtrip, midi-export-basics |
| **合計** | **36** | |

（名前は代表例であり、P1 で確定させる。本 draft では全文カードを書かない。）

## Constraints

- **no silent checks**: 未実装のops/バリデータを検査済みと見せない。advisory/
  unimplemented を明示する。
- **有界コスト/有界ループ**: validate/revise ループに上限を設ける。LLM呼び出しは
  Go クォータ/コスト制約内（`opencode run` は bridge 外の有料Goレーン）。
  Phase 1 は LLM 呼び出しゼロで完結させる。
- **決定的テストに live-LLM 非決定性を持ち込まない**: 選択フィクスチャ等の
  決定的テストは、LLMを介さずメタデータのみで判定する。
- **秘密情報の保存禁止**: `API_SECRET` 等のクレデンシャルを本機能のファイルに
  書かない（そもそも要求しない設計）。
- **需要駆動の成長**: カード追加は実際の使用要求に応答して行う。枚数目標の
  段取り消化をしない。
- UTF-8 NoBOM / LF。PowerShell ネストクォート禁止（repo規約どおり）。

## Non-goals

- mtdt 本体との互換・パリティ（クローズド/商用、アクセス不能）
- 300スキルの即時整備（シード36から需要駆動で成長）
- Rust エンジン実装（将来の実装言語選択は spec で決める）
- 音声生成・ミックス/マスタリング
- PDF engraving・LilyPond/MuseScore の必須化
- Suno API 統合
- bridge レーン新設
- モデル学習/ファインチューニング
- クローズドソース mtdt コンテンツの複製

## Done criteria（P0 = 本draft）

- 本 draft が承認され、`draft/.index/taxonomy.yaml` に `mtdt-lite: topic: agent-infra`
  の override が入っていること
- 後続フェーズの境界（P1–P4）と、P1 実装前に `specs/mtdt-lite.yaml` が必要なことが
  明記されていること
- シード36カードの配分表と SATB 縦断スライスの要件（3カテゴリ + 3バリデータ以上）
  が合意事項として記録されていること

## Unknowns / residual risk

- スコアJSON・ops の正確なスキーマ（P2 で確定。本 draft は意図的に書かない）
- MusicXML ラウンドトリップの忠実度（読み込み→正規モデル→書き出しで何が落ちるか）
- バリデータの severity / override の意味論（autofix 可能性の境界）
- Go クォータの予算感（選択1回・revise 1回あたりの実測コスト）
- text_setting の適用範囲（音節割りのみか、言語別規則まで含むか）
- 参照/著作権ポリシー（theory_refs に何を引用してよいか）
- スキルチェッカーゲートの置き場所（agent-check への組み込み可否）
- live モデルを使う選択テストの安定性（決定的テストとの分離方法）

## Promotion gate

P0 → P1 へ進む条件:

1. 本 draft の Decisions（特に Phase 1 = 棚のみ、36カード、LLM実行パターン、
   安全原則）が operator 承認を得ること
2. `specs/mtdt-lite.yaml` が書かれ、受け入れ基準が曖昧でないこと
   （**P1 実装の前に spec が必須**）
3. taxonomy override が反映され、本 draft 分の draft index 再生成が完了していること
   （`node scripts/build-draft-index.cjs --check` 通過を確認済み）

## Phases

- **P0（本draft）**: 設計文書 + taxonomy override。実装なし。
- **P1**: スキル棚36カード + 機械可読インデックス + カードチェッカー +
  選択フィクスチャ。LLM 呼び出しゼロ。**事前に `specs/mtdt-lite.yaml` が必要。**
- **P2**: Python CLI / 操作レジストリのスタブを `tools/mtdt-lite` 以下に作成。
  JSON スコアモデルのスキーマ確定。
- **P3**: エンドツーエンド縦断スライス（SATB コラールハーモニゼーション、
  harmony/counterpoint/notation + 3バリデータ以上）。
- **P4**: 需要駆動のカード拡張（数百規模は要求が続いた場合のみ）。

## Documents

- spec: `specs/mtdt-lite.yaml` (P1 implemented)
- test spec: `specs/mtdt-lite.test.yaml` (P1 tests implemented)
- report: `reports/mtdt-lite.md`
- P2以降: score JSON / op registry / validator は spec另行
