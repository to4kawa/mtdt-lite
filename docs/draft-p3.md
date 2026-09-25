# draft-p3: SATB vertical slice (first end-to-end)

## Goal

P3 は最初のエンドツーエンド縦断スライス。ソプラノ+バス固定・コード進行プラン（離散候補のみ）を入力に、
決定的バックトラッカーが alto/tenor を生成し、新規2本を含む計5+バリデータで検査、
有界 revise ループで受理スコア JSON を得る。同時にカード wiring の初実施:
`parallel-motion-avoidance` / `voice-leading-rules` / `satb-chorale-harmonization` の3枚を
`status: validated` に昇格し、P1 ロックの初緩和を P3 spec の授権で行う。

## Users

- 学生コラール断片を検査したい作曲・編曲者（4小節スケルトン → 完成SATB）。
- 将来 controller（P4以降）が消費する `validate` 終了コード / findings 形状の最初の本番消費者。

## Inputs / Outputs

- in: SATB スケルトン score（soprano+bass のみ whole notes、4小節 C major、手作り・パブリックドメイン不要）+
  chord plan JSON（1小節1シンボル、合法集合からの列挙のみ）。
- out: 完成 SATB score JSON（voice-filled）+ findings（exit 0/3）。失敗時は revise 要求（別プラン）。

## Architecture decision (Perplexity consult 2026-09-25, operator delegation)

- 採用 **A: 離散プラン + 決定的 voicer**。LLM はコード進行プラン（`I/vi/IV/V` 等の列挙）だけを出し、
  音符はバックトラッキング voicer が生成。P0 原則5（LLM は生音符を「受理結果」として出せない）に忠実。
- 棄却 B（LLM が SATB JSON 直出力 = 原則違反の rejection sampler 化）、C（決定的のみ先行 = E2E 未提示）。
- 採用した落とし穴対策: ①ドメインはコード構成音×宣言 range・順次進行優先（探索爆発防止）、
  ②候補コードはソプラノ適合で事前フィルタ（隠れた非充足）、
  ③配置時に直前ソノリティとのペア検査で早期失敗（平行・交差の遅延発見を防ぐ）。
- Perplexity 提案「runtime は validated カードのみ import」は不採用:
  engine はカード本文を一切読まない（`select` は matcher のみ）ため写像先が無い。
  代替として機械テスト「validated ⇔ 登録済み op/validator 連結」+ 無効譜面を reject する統合テストを強制。

## Scope

in:
- 新 validator 2本: `parallel-perfect`（平行5度・8度、相似進行のみ。反対進行の完全音程は合法 =
  `parallel-motion-avoidance` Hard constraints）、`voice-crossing`（隣接声部順序 S>=A>=T>=B の同時刻検査）。
- 新 op `voice-fill`（skeleton + plan → 完成 score）+ CLI サブコマンド。
- 3枚 wiring: index の ops/validators に `implementation: implemented` を追加 + 本体 Validation status 更新
  + `--rehash`（sanctioned updater のみ）。33枚は不変。
- `check_shelf.py` ロック緩和（P3 spec 授権、初変更）: `status: validated` 許可（参照 op/validator 全 implemented の場合のみ）、
  カードの `implementation: implemented` 許可。36枚維持。
- テスト: 決定的 fixture のみ + skip-guard live smoke（`RUN_LIVE_LLM=1` 時のみ実行、マイルストン時のみ手動）。

out（非目標）: 記譜レンダリング、再生、species 対位法、spacing validator、controller 自動ループ
（live revise ループは report 記録の手動実演1回のみ。Go クォータ消費ゼロ = bridge lane 使用）。

## RAT-first (pre-registered; wiring より先に実施)

計画を崩す未知 = **voicer の充足可能性**。RAT は参照スケルトン（spec-p3 で確定する4小節、C major、
soprano/bass whole notes）+ 固定 plan（`I vi IV V` 系）に対し:
- 設定: ドメイン = コード構成音 ∩ part 宣言 range、探索順 alto→tenor・順次優先、配置時ペア検査で早期失敗。
- 成功条件: <2s で完成 score を返し、`mtdt.py validate` が exit 0（全 validator clean）。
- 失敗条件: タイムアウト or 解なし → fallback は scope-C 縮退
  （fixture plan での決定的 slice のみ + backtracker 限界を report に明記）。
- RAT 結果は wiring コミット前に `report-p3.md` へ記録。RAT 失敗時の wiring は行わない。

## Unknowns

1. chord plan schema 形状（spec で確定: `{schema_version, key, slots[]}` 予定）。
2. ペア finding の形状: 5-key Finding 凍結（P2 テスト維持）のもと `part=null` + message 内に声部ペア証拠
   （`parallel-motion-avoidance` Hard constraints「finding に voice-pair evidence」対応）。spec で確定。
3. live LLM の JSON 遵守率（手動1回のみ、失敗してもゲートにしない）。
4. ドメイン縮小（例: テナー下限）が必要になるかは RAT が決める。

## Constraints

- AST allowlist 拡張は `itertools` のみ（spec で確定）。
- P2 suite は無変更グリーン（Finding 5-key 凍結、`mtdt.py` 終了コード体系維持）。
- live 呼び出しは手動1回まで（bridge lane、Go ゼロ）。unittest に live 依存なし（skip-guard のみ）。

## Done criteria

- RAT 成功を記録。
- `parallel-perfect` + `voice-crossing` 実装 + registry 双向同期（`validate_registry`）。
- E2E fixture exit 0。adversarial fixture（平行5度・交差を仕込んだ譜面）exit 3 + ペア証拠メッセージ。
- 3枚 validated（機械テスト）、33枚 untouched（hash 同一）。
- `check_shelf` 4ゲート相当 + 新テスト全グリーン。
- 手動 live revise デモを report に記録。
- `report-p3.md` + commit + push。逸脱があれば report に明記。

## Promotion gate

spec-p3 へ進む条件: operator の draft 承認。本 draft の意思決定は Perplexity consult + operator 委任
（「聞いただけ」→「Perplexity に聞いて作っていって」）に基づく。
