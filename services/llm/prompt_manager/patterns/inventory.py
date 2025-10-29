#!/usr/bin/env python3
"""
在庫操作プロンプトビルダー
"""

from ..utils import build_base_prompt


def build_inventory_prompt(user_request: str) -> str:
    """在庫操作用のプロンプトを構築"""
    base = build_base_prompt()
    
    return f"""
{base}

ユーザー要求: "{user_request}"

**在庫操作のタスク生成ルール**:

ユーザーの要求が「追加」「削除」「更新」「確認」等の在庫操作のみの場合、該当する在庫操作タスクのみを生成してください。

**例**:
- 「ピーマンを４個追加して」→ `inventory_service.add_inventory()` のみ
- 「牛乳を削除して」→ `inventory_service.delete_inventory()` のみ  
- 「在庫を確認して」→ `inventory_service.get_inventory()` のみ

在庫操作のstrategy判定について:
- ユーザーが「古い方」「最新」「全部」などを明示しない限り、`update_inventory` や `delete_inventory` の `strategy` パラメータは `'by_name'` を指定してください。

strategy判定の重要ルール:
1. **「全部」「すべて」の判定**: ユーザー要求に「全部」「すべて」が含まれている場合、語順に関係なく `strategy='by_name_all'` を指定してください。
2. **「古い」「最新」の判定**: ユーザー要求に「古い」「最新」が含まれている場合、該当するstrategyを指定してください。
3. **曖昧性の判定**: 上記のキーワードが含まれていない場合は `strategy='by_name'` を指定し、システムが自動的に曖昧性を検知します。

判定例:
- 「牛乳を全部１本に変えて」→ 「全部」が含まれている → `strategy='by_name_all'`
- 「全部の牛乳を１本にして」→ 「全部」が含まれている → `strategy='by_name_all'`
- 「牛乳をすべて削除して」→ 「すべて」が含まれている → `strategy='by_name_all'`
- 「牛乳を１本に変えて」→ キーワードなし → `strategy='by_name'` (システムが曖昧性を検知)

⚠️ 重要: 「変えて」の認識ルール:
- 「変えて」「変更して」「修正して」等のキーワードは**必ず更新操作**として認識してください
- 「変えて」要求に対して**削除+追加の組み合わせは絶対に生成しないでください**
- 「変えて」は既存アイテムの数量や属性を変更する操作であり、新しいアイテムの追加ではありません

strategy判定の例:
- 「牛乳を更新/削除して」 → `strategy='by_name'` (システムが曖昧性を検知)
- 「古い牛乳を更新/削除して」 → `strategy='by_name_oldest'` (最古)
- 「最新の牛乳を更新/削除して」 → `strategy='by_name_latest'` (最新)
- 「全部の牛乳を更新/削除して」 → `strategy='by_name_all'` (全部)

「変えて」の具体例（更新操作）:
- 「最新の牛乳を5本に変えて」 → `inventory_service.update_inventory(item_identifier='牛乳', updates={{'quantity': 5}}, strategy='by_name_latest')`
- 「一番古いピーマンを3個に変えて」 → `inventory_service.update_inventory(item_identifier='ピーマン', updates={{'quantity': 3}}, strategy='by_name_oldest')`
- 「牛乳の保存場所を冷凍庫に変えて」 → `inventory_service.update_inventory(item_identifier='牛乳', updates={{'storage_location': '冷凍庫'}}, strategy='by_name')`
- 「古い牛乳の単位をパックに変えて」 → `inventory_service.update_inventory(item_identifier='牛乳', updates={{'unit': 'パック'}}, strategy='by_name_oldest')`

❌ 禁止パターン（「変えて」要求に対して）:
- 「変えて」要求で `delete_inventory` + `add_inventory` の組み合わせは絶対に生成しない
- 「変えて」要求で複数タスクに分解しない（必ず1つの `update_inventory` タスクのみ）
"""

