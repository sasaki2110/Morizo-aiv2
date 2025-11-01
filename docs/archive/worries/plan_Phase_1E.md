# Phase 1E: 曖昧性解消後の再開機能

## 概要

曖昧性検出後のユーザー回答を処理し、元のリクエストと統合して4タスクを実行する再開機能を実装します。これにより、「主菜を教えて」→「レンコンでお願い」という会話の流れが自然に処理されます。

## 対象範囲

- ユーザー回答の受付機能
- コンテキスト統合機能（元のリクエスト + ユーザー回答）
- タスクチェーンの再開機能
- セッション状態管理の拡張
- プランナープロンプトの拡張
- エラーハンドリング
- テストケース

## 実装計画

### 1. セッション状態管理の拡張

**修正ファイル**: `services/session_service.py`

**変更内容**:
- セッションに確認待ち状態を保存する機能を追加
- 曖昧性解消の確認コンテキストを管理
- 元のリクエストと確認質問を保存

**実装例**:
```python
class Session:
    def __init__(self, session_id: str, user_id: str):
        self.id = session_id
        self.user_id = user_id
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.data: Dict[str, Any] = {}
        self.confirmation_context: Dict[str, Any] = {
            "type": None,  # "inventory_operation" | "ambiguity_resolution"
            "original_request": None,  # 元のユーザーリクエスト
            "clarification_question": None,  # システムが出した確認質問
            "detected_ambiguity": None,  # 検出された曖昧性の詳細
            "timestamp": None
        }
    
    def is_waiting_for_confirmation(self) -> bool:
        """確認待ち状態かどうか"""
        return self.confirmation_context.get("type") is not None
    
    def set_ambiguity_confirmation(
        self, 
        original_request: str, 
        question: str,
        ambiguity_details: Dict[str, Any]
    ):
        """曖昧性解消の確認状態を設定"""
        self.confirmation_context = {
            "type": "ambiguity_resolution",
            "original_request": original_request,
            "clarification_question": question,
            "detected_ambiguity": ambiguity_details,
            "timestamp": datetime.now()
        }
    
    def clear_confirmation_context(self):
        """確認コンテキストをクリア"""
        self.confirmation_context = {
            "type": None,
            "original_request": None,
            "clarification_question": None,
            "detected_ambiguity": None,
            "timestamp": None
        }
    
    def get_confirmation_type(self) -> Optional[str]:
        """確認タイプを取得"""
        return self.confirmation_context.get("type")
```

### 2. ユーザー回答の受付機能

**修正ファイル**: `core/agent.py`

**変更内容**:
- `process_message()`メソッドでセッション状態を確認
- 確認待ち状態の場合は回答処理として扱う
- 通常メッセージと確認回答を区別して処理

**実装箇所**: `process_request()`内
```python
# 曖昧性解決の回答かチェック
if is_confirmation_response and sse_session_id:
    self.logger.info(f"🔄 [AGENT] Checking for saved confirmation state...")
    saved_state = await self.session_service.get_confirmation_state(sse_session_id)
    if saved_state:
        self.logger.info(f"🔄 [AGENT] Found saved state, resuming from confirmation")
        # 確認コンテキストもチェック
        session = await self.session_service.get_session(sse_session_id, user_id)
        if session and session.is_waiting_for_confirmation():
            # Phase 1E: 曖昧性解消の再開処理
            return await self._handle_ambiguity_resolution(
                session, user_request, user_id, token, sse_session_id
            )
```

### 3. コンテキスト統合機能

**新規メソッド**: `core/agent.py`の`_integrate_confirmation_response()`

**処理内容**:
```python
async def _integrate_confirmation_response(
    self, 
    original_request: str,  # 「主菜を教えて」
    user_response: str,     # 「レンコンでお願い」
    confirmation_context: Dict  # 確認時のコンテキスト
) -> str:
    """
    元のリクエストとユーザー回答を統合して、
    完全なリクエストを生成する
    
    例:
    - 元: 「主菜を教えて」
    - 回答: 「レンコンでお願い」
    - 結果: 「レンコンの主菜を教えて」
    """
    
    self.logger.info(f"🔗 [AGENT] Integrating request")
    self.logger.info(f"  Original: {original_request}")
    self.logger.info(f"  Response: {user_response}")
    
    # パターン1: 「指定しない」系の回答
    proceed_keywords = ["いいえ", "そのまま", "提案して", "在庫から", "このまま", "進めて", "指定しない", "2"]
    if any(keyword in user_response for keyword in proceed_keywords):
        # 元のリクエストをそのまま使用
        integrated_request = original_request
        self.logger.info(f"✅ [AGENT] Integrated (proceed): {integrated_request}")
        return integrated_request
    
    # パターン2: 食材名が含まれている
    # 簡易的な統合（LLMを使わない方式）
    # 「レンコン」「レンコンで」「レンコンを使って」等を抽出
    ingredient = self._extract_ingredient_simple(user_response)
    
    if ingredient:
        # 元のリクエストに食材を追加
        # 「主菜を教えて」→「レンコンの主菜を教えて」
        if "主菜" in original_request or "メイン" in original_request:
            integrated_request = f"{ingredient}の主菜を教えて"
        elif "料理" in original_request:
            integrated_request = f"{ingredient}の料理を教えて"
        else:
            integrated_request = f"{ingredient}を使って{original_request}"
        
        self.logger.info(f"✅ [AGENT] Integrated (ingredient): {integrated_request}")
        return integrated_request
    
    # パターン3: 統合できない場合は元のリクエストを返す
    self.logger.warning(f"⚠️ [AGENT] Could not integrate, using original request")
    return original_request
```

### 4. タスクチェーンの再開機能

**新規メソッド**: `core/agent.py`の`_handle_ambiguity_resolution()`

**処理内容**:
```python
async def _handle_ambiguity_resolution(
    self, 
    session: Session, 
    user_request: str,
    user_id: str, 
    token: str,
    sse_session_id: str
) -> Dict[str, Any]:
    """曖昧性解消後のタスクチェーン再開"""
    
    self.logger.info(f"🔄 [AGENT] Handling ambiguity resolution")
    
    # 確認コンテキストから元のリクエストを取得
    original_request = session.confirmation_context.get("original_request")
    confirmation_context = session.confirmation_context.get("detected_ambiguity", {})
    
    # 元のリクエストとユーザー回答を統合
    integrated_request = await self._integrate_confirmation_response(
        original_request, 
        user_request, 
        confirmation_context
    )
    
    # 確認コンテキストをクリア
    session.clear_confirmation_context()
    
    # 統合されたリクエストで通常のプランニングループを実行
    self.logger.info(f"▶️ [AGENT] Resuming planning loop with integrated request: {integrated_request}")
    result = await self.process_request(integrated_request, user_id, token, sse_session_id, False)
    
    return result
```

### 5. 食材抽出機能

**新規メソッド**: `core/agent.py`の`_extract_ingredient_simple()`

**処理内容**:
```python
def _extract_ingredient_simple(self, user_response: str) -> Optional[str]:
    """ユーザー応答から食材名を簡易抽出"""
    
    # 助詞を除去
    cleaned = user_response.replace("で", "").replace("を", "").replace("が", "")
    cleaned = cleaned.replace("使って", "").replace("お願い", "").replace("ください", "")
    cleaned = cleaned.strip()
    
    # 空でなければ食材名として扱う
    if cleaned and len(cleaned) > 0:
        return cleaned
    
    return None
```

### 6. 曖昧性検出時の確認コンテキスト保存

**修正箇所**: `core/agent.py`の`_handle_confirmation()`

**追加処理**:
```python
# Phase 1E: セッションに確認コンテキストを保存
if task_chain_manager.sse_session_id:
    session = await self.session_service.get_session(task_chain_manager.sse_session_id, user_id)
    if session:
        confirmation_message = execution_result.message if hasattr(execution_result, 'message') else ""
        session.set_ambiguity_confirmation(
            original_request=user_request,  # 元のユーザーリクエスト
            question=confirmation_message,  # 確認質問
            ambiguity_details=ambiguity_info.details if hasattr(ambiguity_info, 'details') else {}
        )
        self.logger.info(f"💾 [AGENT] Confirmation context saved to session")
```

### 7. プランナープロンプトの拡張

**修正ファイル**: `services/llm/prompt_manager.py`

**追加内容**:
```
**曖昧性解消後の処理（Phase 1E）**:
ユーザーが曖昧性解消のための回答を提供した場合:
1. 元のリクエストとユーザー回答を統合
2. 統合されたリクエストで通常のタスクチェーンを実行
3. 確認状態をクリア

例:
- 元のリクエスト: 「主菜を教えて」
- 確認質問: 「何か食材を指定しますか？それとも在庫から提案しますか？」
- ユーザー回答: 「レンコンでお願い」
- 統合リクエスト: 「レンコンの主菜を教えて」
- 実行: 4タスク（在庫取得→履歴取得→LLM+RAG統合→Web検索）

統合パターン:
- 「主菜を教えて」+「レンコン」→「レンコンの主菜を教えて」
- 「主菜を教えて」+「在庫から提案して」→「在庫の中から主菜を教えて」(main_ingredient: null)
- 「料理を提案して」+「鶏肉」→「鶏肉の料理を提案して」
```

## 現在の実装状況との対応関係

### 実装済みの機能
- 曖昧性検出: Phase 1Bで実装済み
- 確認メッセージの表示: Phase 1Bで実装済み
- ユーザー回答の受付: Phase 1Eで実装（本Phase）
- セッション状態管理: Phase 1Eで実装（本Phase）

### 未実装の機能（Phase 2以降）
- ユーザー選択UI: Phase 2Bで予定
- 主菜の再提案（5件→5件の追加提案）: Phase 3で予定
- 副菜・汁物の段階的選択: Phase 3で予定
- タスクチェーンのロールバック: Phase 4で予定

### worries.mdとの対応関係
plan_Phase_1E.mdは、worries.mdで言及されている課題の一部を解決します：

- ✅ **解決**: 曖昧性検出後のユーザー回答→元のリクエスト統合→再実行フロー
- ❌ **未解決（Phase 2以降）**: 主菜の再提案（5件→5件追加）
- ❌ **未解決（Phase 3以降）**: 副菜・汁物の段階的選択
- ❌ **未解決（Phase 4以降）**: 前段階への戻り機能

## テスト計画

### 単体テスト

1. **セッション状態管理のテスト**
   - `set_ambiguity_confirmation()`が正しく動作
   - `is_waiting_for_confirmation()`が正しい状態を返す
   - `clear_confirmation_context()`が正しくクリア

2. **コンテキスト統合のテスト**
   - パターン1: 「指定しない」→元のリクエストを返す
   - パターン2: 「レンコン」→「レンコンの主菜を教えて」
   - パターン3: 不明瞭な回答→元のリクエストを返す

3. **食材抽出のテスト**
   - 「レンコンでお願い」→「レンコン」
   - 「鶏肉を使って」→「鶏肉」
   - 「在庫から提案して」→None

### 統合テスト

**テスト1: 食材指定の曖昧性解消**
```
入力1: 「主菜を教えて」
応答1: 「食材を指定しますか？」
入力2: 「レンコンでお願い」
期待: レンコンの主菜5件が提案される（4タスク実行）
```

**テスト2: 在庫からの提案選択**
```
入力1: 「主菜を教えて」
応答1: 「食材を指定しますか？」
入力2: 「在庫から提案して」
期待: 在庫の中から主菜5件が提案される（main_ingredient: null）
```

**テスト3: エラーハンドリング**
```
入力1: 「主菜を教えて」
応答1: 「食材を指定しますか？」
入力2: 「わからない」
期待: デフォルト動作（在庫から提案）またはエラーメッセージ
```

### エンドツーエンドテスト

1. **正常フロー**
   - ユーザーが曖昧なリクエストを送信
   - システムが確認を求める
   - ユーザーが回答
   - システムが4タスクを実行して5件提案

2. **セッション永続性**
   - 確認待ち状態がセッションに保存される
   - 再接続後も確認コンテキストが保持される

3. **エラーリカバリ**
   - 統合失敗時のフォールバック動作
   - タイムアウト時の適切なエラーメッセージ

## 修正ファイル一覧

- `services/session_service.py` - セッション状態管理の拡張
- `core/agent.py` - ユーザー回答受付、コンテキスト統合、再開機能
- `services/llm/prompt_manager.py` - プランナープロンプトの拡張
- テストファイル（新規作成）

## 制約事項

- Phase 1A-Dが完成していること
- 既存の確認プロセスを破壊しない
- 在庫操作の確認プロセスとの共存

## 期待される効果

- Phase 1の基本機能が完成
- ユーザー体験が大幅に向上（自然な会話フロー）
- Phase 2以降の基盤が整う（ユーザー選択機能の前提条件）
- 曖昧性検出プロセスが完成

## 実装の優先度

**優先度: 高**
- Phase 1の基本機能を完成させるために必須
- Phase 2（ユーザー選択機能）の前提条件

## 実装規模

- **小〜中規模**: 既存の確認プロセスの拡張
- 新規ファイル: 0個
- 修正ファイル: 3個
- テストファイル: 1-2個

## 実装時間の目安

- コア機能: 2-3時間
- テスト: 1-2時間
- 合計: 3-5時間

