# Phase 2.5-3: 実装計画（各サブフェーズの詳細）

## 目次

- [概要](#概要)
- [Phase 2.5A: RequestAnalyzer の実装](#phase-25a-requestanalyzer-の実装)
- [Phase 2.5B: PromptManager のリファクタリング（モジュール化）](#phase-25b-promptmanager-のリファクタリングモジュール化)
- [Phase 2.5C: LLMService への統合](#phase-25c-llmservice-への統合)
- [Phase 2.5D: セッション管理の拡張](#phase-25d-セッション管理の拡張)
- [Phase 2.5E: 統合テスト](#phase-25e-統合テスト)
- [実装順序](#実装順序)
- [期待される効果](#期待される効果)
- [制約事項](#制約事項)

---

## 概要

Phase 2.5 は **システムの根幹にかかわる** 実装のため、破壊的活動（デグレード）を極力防ぐために、段階的に実装を進め、各ステップごとに回帰テストを実施します。

詳細な実装内容は各サブフェーズを参照してください。

---

## Phase 2.5A: RequestAnalyzer の実装

**修正する場所**: `services/llm/request_analyzer.py`（新規作成）

**修正する内容**: [概要ドキュメント](./plan_Phase_2.5_1_overview.md) を参照

**修正の理由**: プロンプトの肥大化を防ぐため、事前にパターン判定を行う

**修正の影響**: LLMService に RequestAnalyzer を統合する必要がある

---

## Phase 2.5B: PromptManager のリファクタリング（モジュール化）

**修正する場所**: `services/llm/prompt_manager/`（新規ディレクトリ作成）

**修正する内容**: 

### ディレクトリ構造

```
services/llm/prompt_manager/
├── __init__.py              # PromptManager クラスのエクスポート
├── base.py                   # PromptManager（基本クラス）
├── patterns/
│   ├── __init__.py
│   ├── inventory.py         # 在庫操作プロンプト（50-80行程度）
│   ├── menu.py              # 献立生成プロンプト（50-80行程度）
│   ├── main_proposal.py     # 主菜提案プロンプト（50-80行程度）
│   ├── sub_proposal.py     # 副菜提案プロンプト（50-80行程度）
│   ├── soup_proposal.py    # 汁物提案プロンプト（50-80行程度）
│   └── additional_proposal.py  # 追加提案プロンプト（50-80行程度）
└── utils.py                 # 共通ユーティリティ（ベースプロンプト等）
```

**メリット**:
- ✓ ファイルが小さくなる（50-80行程度）
- ✓ 可読性が向上
- ✓ 保守性が向上（差分が小さくなる）
- ✓ テストが容易（パターン別にテスト可能）
- ✓ コーディング支援ツールのコンテキストウインドウ圧迫が緩和

詳細な実装イメージは元の `plan_Phase_2.5.md` を参照。

**修正の理由**: プロンプトをパターン別に分割し、動的に構築することで肥大化を防ぐ

**修正の影響**: 
- `services/llm/prompt_manager.py` → `services/llm/prompt_manager/` ディレクトリに分割
- 各パターンのプロンプトが50-80行程度にシンプル化される
- 既存のインポートは `from services.llm.prompt_manager import PromptManager` のまま動作（後方互換性）

---

## Phase 2.5C: LLMService への統合

**修正する場所**: `services/llm_service.py`

**修正する内容**: RequestAnalyzer を LLMService に統合

**主な変更点**:
1. `RequestAnalyzer` を初期化
2. `plan_tasks()` メソッドでリクエスト分析を実行
3. 曖昧性検出時に確認質問を返す
4. 分析結果に基づいて動的プロンプトを構築

**修正の理由**: RequestAnalyzer と PromptManager を統合してプランニングを実行

**修正の影響**: LLMService のプランニングロジックが変更される

---

## Phase 2.5D: セッション管理の拡張

**修正する場所**: `models/session.py`

**修正する内容**: Session モデルに以下のフィールドを追加

```python
class SessionStage(enum.Enum):
    """セッション段階"""
    INITIAL = "initial"           # 初期状態
    MAIN_SELECTED = "main_selected"     # 主菜選択済み
    SUB_SELECTED = "sub_selected"      # 副菜選択済み
    SOUP_SELECTED = "soup_selected"     # 汁物選択済み
    COMPLETED = "completed"         # 完了

class Session(Base):
    # Phase 2.5D: 段階管理
    stage = Column(Enum(SessionStage), default=SessionStage.INITIAL)
    
    # Phase 2.5D: 選択履歴
    selected_recipes = Column(JSON, default=dict)  # {"main": {...}, "sub": {...}, "soup": {...}}
    
    # Phase 2.5D: 使用食材
    used_ingredients = Column(JSON, default=list)  # ["レンコン", "牛豚合挽肉", ...]
    
    # Phase 2.5D: 献立カテゴリ
    menu_category = Column(String, default="japanese")  # "japanese" / "western" / "chinese"
```

**修正の理由**: 副菜・汁物提案に必要な情報をセッションに保存

**修正の影響**: データベースマイグレーションが必要

---

## Phase 2.5E: 統合テスト

**テストファイル**: `tests/phase2_5/test_integration.py`

**テスト項目**:
1. パターン判定の正確性テスト
2. パラメータ抽出の正確性テスト
3. 曖昧性検出の正確性テスト
4. プロンプト構築の正確性テスト
5. エンドツーエンドテスト（リクエスト→タスク生成）
6. セッション管理テスト

---

## 実装順序

1. **Phase 2.5A** → RequestAnalyzer の実装
2. **Phase 2.5B** → PromptManager のリファクタリング
3. **Phase 2.5C** → LLMService への統合
4. **Phase 2.5D** → セッション管理の拡張
5. **Phase 2.5E** → 統合テスト
6. **Phase 2.5F** → バックエンド回帰テスト（[テスト計画](./plan_Phase_2.5_2_testing.md)を参照）
7. **Phase 2.5G** → フロントエンド手動テストシナリオ（[テスト計画](./plan_Phase_2.5_2_testing.md)を参照）

各サブフェーズは、**回帰テストを実施してから次のサブフェーズに進む**ことを推奨します。

---

## 期待される効果

- ✅ プロンプトがシンプル化（各パターン50-80行程度）
- ✅ LLMが混乱しない（1パターンのみ提示）
- ✅ トークン消費が削減
- ✅ レスポンス時間が改善
- ✅ 保守性が高い（パターン別に管理）
- ✅ テストが容易（パターン別にテスト可能）
- ✅ Phase 3B（副菜・汁物提案）の実装基盤が完成

---

## 制約事項

- Phase 2.5A が完了してから Phase 2.5B を開始
- Phase 2.5B が完了してから Phase 2.5C を開始
- Phase 2.5C が完了してから Phase 2.5D を開始
- Phase 2.5D が完了してから Phase 2.5E を開始
- **各サブフェーズの実装後に回帰テストを実施**（破壊的活動の早期発見）
- 既存の Phase 1-2 の機能を破壊しない
- 既存のテストが全て成功することを確認

---

## 関連ドキュメント

- [Phase 2.5-1: 概要](./plan_Phase_2.5_1_overview.md)
- [Phase 2.5-2: テスト計画](./plan_Phase_2.5_2_testing.md)
- [Phase 3: 副菜・汁物の段階的選択](./plan_Phase_3.md)

