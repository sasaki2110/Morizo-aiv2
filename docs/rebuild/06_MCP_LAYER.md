# Morizo AI v2 - MCP層設計

## 📋 概要

**作成日**: 2025年1月29日  
**バージョン**: 1.0  
**目的**: MCP層のアーキテクチャ設計と実装方針

## 🧠 設計思想

### **MCP実装技術スタック**
- **FastMCP**: MCPサーバーの実装にFastMCPライブラリを使用
- **stdio接続**: 標準入出力による軽量通信
- **アノテーション方式**: `@mcp.tool()`デコレータによるツール定義

### **MCP層の役割**
- **疎結合な通信**: 複数のマイクロエージェント間の疎結合な通信を実現
- **単独動作保証**: 各MCPは単独での動作を保証
- **相互独立性**: 各MCPサーバー間の直接通信を禁止
- **動的ツール提供**: ツールの動的発見と実行

### **疎結合設計の実装**
- **動的ツール取得**: MCPサーバーからツール詳細を動的に取得
- **プロンプト動的埋め込み**: 取得したツール説明を本体プロンプトに動的に埋め込み
- **直接呼び出し禁止**: MCPツールの機能を直接呼び出さず、MCP経由で実行
- **相互独立性**: 各MCPサーバー間の直接通信を禁止

## 🏗️ MCP層アーキテクチャ

### **全体構成**
```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Layer                               │
├─────────────┬─────────────┬─────────────────────────────────────┤
│  RecipeMCP  │InventoryMCP │         RecipeHistoryMCP            │
│             │             │                                     │
│ • レシピ生成│ • 在庫CRUD  │ • 履歴CRUD                          │
│ • レシピ検索│ • 在庫検索  │ • 履歴検索                          │
│ • Web検索   │ • 在庫更新  │ • 履歴更新                          │
│ • RAG検索   │ • 在庫削除  │ • 履歴削除                          │
└─────────────┴─────────────┴─────────────────────────────────────┘
```

### **データフロー**
```
Service Layer (各サービス + MCP Client)
    ↓
MCP Servers (各MCPツール)
    ↓
External Systems (DB, API, etc.)
```

## 🛠️ FastMCP実装パターン

### **基本実装構造**
```python
#!/usr/bin/env python3
"""
MCP Server (FastMCP implementation)
"""

import os
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
from fastmcp import FastMCP
from pydantic import BaseModel
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# FastMCPロゴを非表示にする
os.environ["FASTMCP_DISABLE_BANNER"] = "1"

# MCPサーバーの初期化
mcp = FastMCP("Server Name")

class DatabaseClient:
    """データベースクライアントのラッパークラス"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        self._client: Optional[Client] = None

    def get_client(self) -> Client:
        if self._client is None:
            self._client = create_client(self.supabase_url, self.supabase_key)
        return self._client

# グローバルインスタンス
db_client = DatabaseClient()

# ツール定義の例
@mcp.tool()
async def example_tool(
    user_id: str,
    param1: str,
    param2: Optional[str] = None
) -> Dict[str, Any]:
    """
    ツールの説明
    
    Args:
        user_id: ユーザーID（認証はAPI層で完了済み）
        param1: パラメータ1
        param2: パラメータ2（オプション）
    
    Returns:
        実行結果
    """
    try:
        # ツール固有の処理
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# サーバー起動
if __name__ == "__main__":
    mcp.run()
```

### **実装ガイドライン**
1. **FastMCPの使用**: すべてのMCPサーバーはFastMCPライブラリを使用
2. **stdio接続**: 標準入出力による軽量通信を採用
3. **エラーハンドリング**: 統一されたエラーレスポンス形式
4. **ログ出力**: 適切なログレベルでの出力管理

## 🔧 MCPコンポーネント

### **1. RecipeMCP（レシピMCP）**

#### **役割**
- 献立提案とレシピ検索機能の専門化されたツール提供
- 単独動作保証
- 説明の手厚さ

#### **設計思想の核心**
- **根本的な問題**: LLMには魂のこもったレシピ作成ができない
- **解決策**: 人間が蓄積してきたレシピを参照する必要がある
- **2段階アプローチ**: タイトル提案 → 具体レシピ取得

#### **利用可能ツール**

##### **1. タイトル提案段階（並列実行）**

```python
@mcp.tool()
async def generate_menu_with_llm_constraints(
    inventory_items: List[str],
    user_id: str,
    menu_type: str = "和食",
    excluded_recipes: List[str] = None
) -> Dict[str, Any]:
    """
    LLM推論による独創的な献立タイトル生成
    
    Args:
        inventory_items: 在庫食材リスト
        user_id: ユーザーID
        menu_type: 献立のタイプ
        excluded_recipes: 除外するレシピタイトル
    
    Returns:
        {
            "candidates": [
                {
                    "main_dish": {"title": "牛乳と卵のフレンチトースト", "ingredients": ["牛乳", "卵", "パン"]},
                    "side_dish": {"title": "ほうれん草の胡麻和え", "ingredients": ["ほうれん草", "胡麻"]},
                    "soup": {"title": "白菜とハムのクリームスープ", "ingredients": ["白菜", "ハム", "牛乳"]}
                }
            ],
            "selected": {
                "main_dish": {"title": "牛乳と卵のフレンチトースト", "ingredients": ["牛乳", "卵", "パン"]},
                "side_dish": {"title": "ほうれん草の胡麻和え", "ingredients": ["ほうれん草", "胡麻"]},
                "soup": {"title": "白菜とハムのクリームスープ", "ingredients": ["白菜", "ハム", "牛乳"]}
            }
        }
    """

@mcp.tool()
async def search_menu_from_rag_with_history(
    inventory_items: List[str],
    user_id: str,
    menu_type: str = "和食",
    excluded_recipes: List[str] = None
) -> Dict[str, Any]:
    """
    RAG検索による伝統的な献立タイトル生成
    (実装注: 現行ではChromaDBとOpenAIEmbeddingsを利用)
    
    Args:
        inventory_items: 在庫食材リスト
        user_id: ユーザーID
        menu_type: 献立のタイプ
        excluded_recipes: 除外するレシピタイトル
    
    Returns:
        {
            "candidates": [
                {
                    "main_dish": {"title": "オムライス", "ingredients": ["卵", "ご飯", "玉ねぎ"]},
                    "side_dish": {"title": "サラダ", "ingredients": ["レタス", "トマト"]},
                    "soup": {"title": "味噌汁", "ingredients": ["豆腐", "わかめ"]}
                }
            ],
            "selected": {
                "main_dish": {"title": "オムライス", "ingredients": ["卵", "ご飯", "玉ねぎ"]},
                "side_dish": {"title": "サラダ", "ingredients": ["レタス", "トマト"]},
                "soup": {"title": "味噌汁", "ingredients": ["豆腐", "わかめ"]}
            }
        }
    """
```

##### **2. 具体レシピ取得段階**

```python
@mcp.tool()
async def search_recipe_from_web(
    recipe_titles: List[str]
) -> List[Dict[str, Any]]:
    """
    Web検索による具体的レシピ取得
    
    Args:
        recipe_titles: 検索するレシピタイトルリスト
    
    Returns:
        [
            {
                "title": "牛乳と卵のフレンチトースト",
                "url": "https://cookpad.com/recipe/123456",
                "source": "Cookpad",
                "description": "ふわふわのフレンチトースト",
                "ingredients": ["牛乳", "卵", "パン", "バター", "砂糖"],
                "instructions": ["1. 牛乳と卵を混ぜる", "2. パンを浸す", "3. フライパンで焼く"]
            }
        ]
    """
```

##### **3. 統合献立提案**

```python
@mcp.tool()
async def generate_menu_plan_with_history(
    inventory_items: List[str],
    user_id: str,
    menu_type: str = "和食"
) -> Dict[str, Any]:
    """
    在庫食材から献立構成を生成（過去履歴を考慮）
    ※内部で並列提示システムを実行
    
    Args:
        inventory_items: 在庫食材リスト
        user_id: ユーザーID（履歴チェック用）
        menu_type: 献立のタイプ
    
    Returns:
        {
            "main_dish": {
                "title": "牛乳と卵のフレンチトースト",
                "ingredients": ["牛乳", "卵", "パン", "バター"]
            },
            "side_dish": {
                "title": "ほうれん草の胡麻和え",
                "ingredients": ["ほうれん草", "胡麻", "醤油"]
            },
            "soup": {
                "title": "白菜とハムのクリームスープ",
                "ingredients": ["白菜", "ハム", "牛乳", "バター", "小麦粉"]
            },
            "ingredient_usage": {
                "used": ["牛乳", "卵", "パン", "バター", "ほうれん草", "胡麻", "白菜", "ハム", "小麦粉"],
                "remaining": []
            },
            "excluded_recipes": ["フレンチトースト", "オムレツ"],
            "fallback_used": true
        }
    """
```

#### **実装方針**
```python
class RecipeMCPServer:
    def __init__(self):
        self.llm_client = OpenAI()
        self.rag_client = RAGClient()
        self.web_search_client = WebSearchClient()
    
    async def generate_menu_with_llm_constraints(
        self, 
        inventory_items: List[str], 
        user_id: str,
        menu_type: str = "和食",
        excluded_recipes: List[str] = None
    ) -> Dict[str, Any]:
        """LLM推論による独創的な献立タイトル生成"""
        # 1. 複数候補の生成
        candidates = await self._generate_llm_candidates(
            inventory_items, menu_type, excluded_recipes
        )
        
        # 2. AI制約解決による最適選択
        selected = await self._solve_ingredient_constraints(candidates, inventory_items)
        
        return {
            "candidates": candidates,
            "selected": selected
        }
    
    async def search_menu_from_rag_with_history(
        self, 
        inventory_items: List[str], 
        user_id: str,
        menu_type: str = "和食",
        excluded_recipes: List[str] = None
    ) -> Dict[str, Any]:
        """RAG検索による伝統的な献立タイトル生成"""
        # 1. RAG検索による候補生成
        candidates = await self._search_rag_candidates(
            inventory_items, menu_type, excluded_recipes
        )
        
        # 2. AI制約解決による最適選択
        selected = await self._solve_ingredient_constraints(candidates, inventory_items)
        
        return {
            "candidates": candidates,
            "selected": selected
        }
    
    async def search_recipe_from_web(
        self, 
        recipe_titles: List[str]
    ) -> List[Dict[str, Any]]:
        """Web検索による具体的レシピ取得（並列実行）"""
        
        async def _search_single(title: str):
            # 個別のレシピを検索する内部関数
            try:
                search_result = await self.web_search_client.search_recipe(title)
                if search_result:
                    return {
                        "title": title,
                        "url": search_result.get("url"),
                        "source": "web",
                        "description": search_result.get("description", ""),
                        "ingredients": search_result.get("ingredients", []),
                        "instructions": search_result.get("instructions", [])
                    }
            except Exception as e:
                # エラーが発生しても他の検索は継続
                logger.error(f"Failed to search for recipe '{title}': {e}")
            return None

        # 各タイトルに対する検索タスクをリストとして作成
        tasks = [_search_single(title) for title in recipe_titles]
        
        # asyncio.gatherでタスクを並列実行
        results = await asyncio.gather(*tasks)
        
        # Noneの結果を除外してリストを形成
        recipes = [res for res in results if res is not None]
        
        return recipes
    
    async def generate_menu_plan_with_history(
        self, 
        inventory_items: List[str], 
        user_id: str,
        menu_type: str = "和食"
    ) -> Dict[str, Any]:
        """統合献立提案"""
        # 1. 並列提示システムの実行
        llm_result = await self.generate_menu_with_llm_constraints(
            inventory_items, user_id, menu_type
        )
        rag_result = await self.search_menu_from_rag_with_history(
            inventory_items, user_id, menu_type
        )
        
        # 2. 最終的な献立選択（LLM推論結果を優先）
        selected_menu = llm_result["selected"]
        
        return selected_menu
    
    async def _generate_llm_candidates(
        self, 
        inventory_items: List[str], 
        menu_type: str,
        excluded_recipes: List[str] = None
    ) -> List[Dict[str, Any]]:
        """LLMによる独創的な献立候補生成"""
        prompt = f"""
        在庫食材: {inventory_items}
        献立タイプ: {menu_type}
        除外レシピ: {excluded_recipes or []}
        
        以下の条件で独創的な献立タイトルを生成してください:
        1. 主菜・副菜・汁物の3品構成
        2. 在庫食材のみを使用
        3. 食材の重複を避ける
        4. 独創的で新しいレシピタイトル
        5. 除外レシピは使用しない
        
        重要: 具体的な調理手順は生成せず、レシピタイトルのみを生成してください。
        例: "牛乳と卵のフレンチトースト"、"ほうれん草の胡麻和え"
        
        生成する献立タイトル:
        """
        
        response = await self.llm_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8  # 独創性を高める
        )
        
        return self._parse_menu_response(response.choices[0].message.content)
    
    async def _search_rag_candidates(
        self, 
        inventory_items: List[str], 
        menu_type: str,
        excluded_recipes: List[str] = None
    ) -> List[Dict[str, Any]]:
        """RAG検索による伝統的な献立候補生成"""
        # RAG検索で類似レシピを取得
        similar_recipes = await self.rag_client.search_similar_recipes(
            ingredients=inventory_items,
            menu_type=menu_type,
            excluded_recipes=excluded_recipes
        )
        
        return similar_recipes
    
    async def _solve_ingredient_constraints(
        self, 
        candidates: List[Dict[str, Any]], 
        inventory_items: List[str]
    ) -> Dict[str, Any]:
        """AI制約解決による最適選択"""
        # 複数候補から食材重複を避ける最適な組み合わせを選択
        constraint_prompt = f"""
        候補献立: {candidates}
        在庫食材: {inventory_items}
        
        以下の条件で最適な献立を選択してください:
        1. 食材の重複を避ける
        2. 在庫食材を最大限活用する
        3. バランスの良い献立構成
        
        選択する献立:
        """
        
        response = await self.llm_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": constraint_prompt}],
            temperature=0.3  # 一貫性を重視
        )
        
        return self._parse_selected_menu(response.choices[0].message.content)
```

### **2. InventoryMCP（在庫管理MCP）**

#### **役割**
- `inventory`テーブルのCRUD操作の専門化
- 在庫管理のビジネスロジック実装
- 単独動作保証

#### **利用可能ツール**

##### **1. 在庫追加・取得**
```python
@mcp.tool()
async def inventory_add(
    user_id: str,
    item_name: str,
    quantity: float,
    unit: str = "個",
    storage_location: str = "冷蔵庫",
    expiry_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    在庫にアイテムを1件追加（個別在庫法）
    
    🎯 使用場面: 「入れる」「追加」「保管」等のキーワードで新たに在庫を作成
    ⚠️ 重要: item_idは自動採番されるため、パラメータには不要
    """

@mcp.tool()
async def inventory_list(user_id: str) -> Dict[str, Any]:
    """
    ユーザーの全在庫アイテムを取得
    
    🎯 使用場面: 在庫一覧の表示、献立提案時の在庫確認
    """

@mcp.tool()
async def inventory_list_by_name(user_id: str, item_name: str) -> Dict[str, Any]:
    """
    指定されたアイテム名の在庫一覧を取得
    
    🎯 使用場面: 曖昧性検出や前提タスク生成で使用
    """

@mcp.tool()
async def inventory_get(user_id: str, item_id: str) -> Dict[str, Any]:
    """
    特定の在庫アイテムを1件取得
    
    🎯 使用場面: 特定アイテムの詳細情報取得
    """
```

##### **2. 在庫更新（複数戦略）**
```python
@mcp.tool()
async def inventory_update_by_id(
    user_id: str,
    item_name: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    storage_location: Optional[str] = None,
    expiry_date: Optional[str] = None,
    item_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    ID指定での在庫アイテム1件更新
    
    🎯 使用場面: 「変更」「変える」「替える」「更新」「クリア」等のキーワード
    ⚠️ 重要: item_idは必須
    """

@mcp.tool()
async def inventory_update_by_name(
    user_id: str,
    item_name: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    storage_location: Optional[str] = None,
    expiry_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    名前指定での在庫アイテム一括更新
    
    🎯 使用場面: 「全部」「一括」「全て」等のキーワードで複数のアイテムを同時更新
    """

@mcp.tool()
async def inventory_update_by_name_oldest(
    user_id: str,
    item_name: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    storage_location: Optional[str] = None,
    expiry_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    名前指定での最古アイテム更新（FIFO原則）
    
    🎯 使用場面: 「古い方」「最初に買った」等のキーワード
    ⚠️ 重要: 同名アイテムが複数ある場合、最も古いもの（created_atが最も古い）のみ更新
    """

@mcp.tool()
async def inventory_update_by_name_latest(
    user_id: str,
    item_name: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    storage_location: Optional[str] = None,
    expiry_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    名前指定での最新アイテム更新
    
    🎯 使用場面: 「新しい方」「最後に買った」等のキーワード
    """
```

##### **3. 在庫削除（複数戦略）**
```python
@mcp.tool()
async def inventory_delete_by_id(user_id: str, item_id: str) -> Dict[str, Any]:
    """
    ID指定での在庫アイテム1件削除
    
    🎯 使用場面: 特定アイテムの削除
    """

@mcp.tool()
async def inventory_delete_by_name(user_id: str, item_name: str) -> Dict[str, Any]:
    """
    名前指定での在庫アイテム一括削除
    
    🎯 使用場面: 「全部削除」「全て消す」等のキーワード
    """

@mcp.tool()
async def inventory_delete_by_name_oldest(
    user_id: str,
    item_name: str
) -> Dict[str, Any]:
    """
    名前指定での最古アイテム削除（FIFO原則）
    
    🎯 使用場面: 「古い方を削除」「最初に買ったのを消す」等
    """

@mcp.tool()
async def inventory_delete_by_name_latest(
    user_id: str,
    item_name: str
) -> Dict[str, Any]:
    """
    名前指定での最新アイテム削除
    
    🎯 使用場面: 「新しい方を削除」「最後に買ったのを消す」等
    """
```

### **3. RecipeHistoryMCP（レシピ履歴MCP）**

#### **役割**
- `recipe_historys`テーブルのCRUD操作の専門化
- レシピ履歴管理のビジネスロジック実装
- 単独動作保証

#### **利用可能ツール**
```python
@mcp.tool()
async def history_add(
    user_id: str,
    title: str,
    source: str,
    url: str = None
) -> str:
    """
    レシピを保存する
    
    Args:
        user_id: ユーザーID
        title: レシピタイトル
        source: レシピの出典
        url: レシピのURL
    
    Returns:
        保存されたレシピのID
    """

@mcp.tool()
async def history_list(user_id: str) -> List[Dict[str, Any]]:
    """
    レシピ履歴一覧を取得する
    
    Args:
        user_id: ユーザーID
    
    Returns:
        レシピ履歴のリスト
    """

@mcp.tool()
async def history_update_by_id(
    user_id: str,
    history_id: str,
    title: str = None,
    source: str = None,
    url: str = None
) -> bool:
    """
    レシピ履歴を更新する
    
    Args:
        user_id: ユーザーID
        history_id: 履歴ID
        title: レシピタイトル（オプション）
        source: レシピの出典（オプション）
        url: レシピのURL（オプション）
    
    Returns:
        更新成功の可否
    """

@mcp.tool()
async def history_delete_by_id(
    user_id: str,
    history_id: str
) -> bool:
    """
    レシピ履歴を削除する
    
    Args:
        user_id: ユーザーID
        history_id: 履歴ID
    
    Returns:
        削除成功の可否
    """
```

#### **実装方針**

```python
class RecipeHistoryMCPServer:
    def __init__(self):
        self.supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
```

##### **CRUD操作の実装**
```python
    async def history_add(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """履歴追加"""
        # recipe_historysテーブルにレコード追加
        
    async def history_list(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """履歴一覧取得"""
        # ユーザーIDに基づく履歴一覧取得
        
    async def history_update_by_id(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """履歴更新（ID指定）"""
        # 指定IDの履歴レコード更新
        
    async def history_delete_by_id(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """履歴削除（ID指定）"""
        # 指定IDの履歴レコード削除（論理削除推奨）
```

##### **エラーハンドリング**
- **認証エラー**: トークン検証失敗時の適切なエラーメッセージ
- **データベースエラー**: Supabase操作失敗時の詳細エラー情報
- **バリデーションエラー**: パラメータ検証失敗時の明確なエラーメッセージ

## 🚀 実装戦略

### **Phase 1: 基本MCP**
1. **RecipeMCP**: 基本的なレシピ生成・検索
2. **InventoryMCP**: 基本的な在庫管理操作
3. **RecipeHistoryMCP**: 基本的なレシピ履歴操作

### **Phase 2: 高度な機能**
1. **エラーハンドリング**: MCP固有のエラー処理
2. **パフォーマンス最適化**: 通信速度の向上

### **Phase 3: 最適化**
1. **メモリ最適化**: メモリ使用量の削減
2. **ログ最適化**: ログ出力の最適化
3. **監視・メトリクス**: MCPサーバーの監視機能

## 📊 成功基準

### **機能面**
- [ ] RecipeMCPの動作確認
- [ ] InventoryMCPの動作確認
- [ ] RecipeHistoryMCPの動作確認
- [ ] 疎結合通信の動作確認

### **技術面**
- [ ] 全ファイルが100行以下
- [ ] 単独動作保証

---

**このドキュメントは、Morizo AI v2のMCP層設計を定義します。**
**すべてのMCPは、この設計に基づいて実装されます。**
