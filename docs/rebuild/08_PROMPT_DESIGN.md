# Morizo AI v2 - プロンプト設計: ActionPlanner

## 📋 概要

**作成日**: 2025年10月3日  
**バージョン**: 2.0  
**目的**: `ActionPlanner` がユーザー要求を、サービス層のメソッド呼び出しに分解するためのコアロジック（プロンプト）を定義する。

> **⚠️ 警告:** このドキュメントに記載されたプロンプトは、Morizo AIのタスク分解能力の根幹をなすものです。将来のAIが実装する際は、このプロンプトの意図と構造を完全に理解し、可能な限り忠実に再現する必要があります。

## 🧠 設計思想

この設計では、`ActionPlanner` は下位層の具体的なツール（MCPなど）を一切意識しない。代わりに、`RecipeService` や `InventoryService` といった、ビジネスロジックをカプセル化した**サービス層のインターフェース**のみを認識する。

LLMには、利用可能なサービスとその機能（メソッド）の一覧が与えられ、ユーザーの要求を達成するために「どのサービスの、どのメソッドを、どのパラメータで呼び出すべきか」を判断させ、タスクプランとして出力させる。

これにより、コア層と下位層の実装が完全に分離され、疎結合なアーキテクチャが実現される。

## 📝 ActionPlanner用プロンプト全文

以下に、`ActionPlanner`がタスク分解のために使用するプロンプトの全文を記載します。

```python
planning_prompt = f"""
ユーザー要求を分析し、適切なサービスクラスのメソッド呼び出しに分解してください。

ユーザー要求: "{user_request}"

利用可能なサービスと機能:

- **inventory_service**: 在庫管理サービス
  - `get_inventory()`: 現在の全在庫アイテムのリストを取得します。
  - `add_inventory(item_name: str, quantity: float, ...)`: 在庫に新しいアイテムを追加します。
  - `update_inventory(item_identifier: str, updates: dict, strategy: str)`: 在庫情報を更新します。strategyには 'by_id', 'by_name', 'by_name_oldest', 'by_name_latest' が指定可能です。
  - `delete_inventory(item_identifier: str, strategy: str)`: 在庫を削除します。strategyには 'by_id', 'by_name', 'by_name_oldest', 'by_name_latest' が指定可能です。

- **recipe_service**: レシピ・献立サービス
  - `generate_menu_plan(inventory_items: list, user_id: str, ...)`: 在庫リストに基づき、最適な献立（主菜・副菜・汁物）を提案します。内部でLLMによる独創的な提案とRAGによる伝統的な提案を比較検討します。
  - `search_recipes(title: str)`: 指定された料理名のレシピをWeb検索し、URLを含む詳細情報を返します。
  - `check_cooking_history(user_id: str, ...)`: 過去の料理履歴を取得します。

- **session_service**: セッション管理サービス（通常は直接呼び出し不要）


**最重要ルール: 献立生成の際のタスク構成**
ユーザーの要求が「献立」や「レシピ」に関するものである場合、必ず以下の2段階のタスク構成を使用してください:
1. `inventory_service.get_inventory()` を呼び出し、現在の在庫をすべて取得する。
2. `recipe_service.generate_menu_plan()` を呼び出す。その際、ステップ1で取得した在庫情報を `inventory_items` パラメータに設定する。

**在庫追加と献立生成を同時に要求された場合のタスク構成**:
1. `inventory_service.add_inventory()` でアイテムを追加する。（複数アイテムの場合は並列実行）
2. `inventory_service.get_inventory()` を呼び出し、追加後を含めた最新の在庫を取得する。
3. `recipe_service.generate_menu_plan()` を呼び出し、ステップ2の結果を注入する。

**曖昧な在庫操作の指示について**:
- ユーザーが「古い方」「最新」などを明示しない限り、`update_inventory` や `delete_inventory` の `strategy` パラメータは `'by_name'` を指定してください。これにより、サービス層でユーザーへの確認プロセスが起動します。
- 例: 「牛乳を削除して」 → `delete_inventory(item_identifier='牛乳', strategy='by_name')`
- 例: 「古い牛乳を削除して」 → `delete_inventory(item_identifier='牛乳', strategy='by_name_oldest')`

**出力形式**: 必ず以下のJSON形式で回答してください（コメントは禁止）：

{{
    "tasks": [
        {{
            "id": "task1",
            "description": "タスクの自然言語での説明",
            "service": "呼び出すサービス名",
            "method": "呼び出すメソッド名",
            "parameters": {{ "key": "value" }},
            "dependencies": []
        }}
    ]
}}

**依存関係のルール**:
- 各タスクには一意のID（task1, task2, ...）を付与してください。
- `dependencies` には、実行前に完了しているべきタスクのIDをリストで指定してください。
- 依存関係がない場合は空配列 `[]` を指定してください。

**挨拶や一般的な会話の場合**:
- タスクは生成せず、空の配列 `{{"tasks": []}}` を返してください。
"""
```