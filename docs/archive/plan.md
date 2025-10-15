# 曖昧性解決の完全修正プラン

⚠️ **重要**: 247行目までは作業完了済み。248行目以降の「曖昧性解決の実装状況」を参照してください。

## 問題の詳細

### **問題1: 選択肢の表示がユーザーフレンドリーでない**
- `_create_confirmation_message()`が`ambiguity_info`の構造に対応できていない
- 確認メッセージが適切に生成されていない可能性

### **問題2: ユーザー回答が新しいリクエストとして処理される**
**根本原因（ログから確認）:**
1. **`is_confirmation_response`が常に`False`**
   - フロントエンドがこのフラグを送信していない
2. **SSEセッションIDが毎回変わる**
   - 1回目: `eec66c8a-d5c3-417a-9576-54d072324d22`
   - 2回目: `243819bd-3124-4d4e-bb8c-d71e5b2afabe`
   - 同じセッションを継続していない

---

## 修正方針

**バックエンドとフロントエンドの両方を修正**して、確実に動作するようにします。

---

## 修正内容

### **バックエンド修正**

#### **1. ChatResponseモデルの拡張**

**ファイル:** `api/models/responses.py`

**修正内容:**
- `requires_confirmation`フィールドを追加
- `confirmation_session_id`フィールドを追加

これにより、フロントエンドが曖昧性検出を判定できます。

**修正理由:**
- フロントエンドが「これは曖昧性確認が必要なレスポンスか？」を判断できるように

---

#### **2. TrueReactAgent._handle_confirmation()の修正**

**ファイル:** `core/agent.py`の`_handle_confirmation()`メソッド（141-187行目）

**修正内容:**
- レスポンスに曖昧性情報を含める
- 確認メッセージをより詳細に生成

**修正理由:**
- フロントエンドに曖昧性検出を通知
- ユーザーに分かりやすい選択肢を提示

---

#### **3. _create_confirmation_message()の改善**

**ファイル:** `core/agent.py`の`_create_confirmation_message()`メソッド（260-297行目）

**修正内容:**
- `ambiguity_info`の構造を正しく処理
- より詳細な確認メッセージを生成
- 選択肢を番号付きで表示

**修正理由:**
- 現在の実装では`ambiguity_info`の詳細情報を取得できていない
- ユーザーフレンドリーな選択肢表示が必要

---

#### **4. APIルートの修正**

**ファイル:** `api/routes/chat.py`の`chat()`エンドポイント（22-81行目）

**修正内容:**
- レスポンスに`requires_confirmation`と`confirmation_session_id`を追加

**修正理由:**
- フロントエンドに曖昧性検出を通知

---

### **フロントエンド修正**

#### **1. ChatMessage型の拡張**

**ファイル:** `/app/Morizo-web/components/ChatSection.tsx`（11-16行目）

**修正内容:**
```typescript
interface ChatMessage {
  type: 'user' | 'ai' | 'streaming';
  content: string;
  sseSessionId?: string;
  result?: unknown;
  requiresConfirmation?: boolean;  // ★追加
}
```

**修正理由:**
- 曖昧性確認が必要なメッセージかを記録

---

#### **2. 状態管理の追加**

**ファイル:** `/app/Morizo-web/components/ChatSection.tsx`（33-34行目付近）

**修正内容:**
```typescript
const [textMessage, setTextMessage] = useState<string>('');
const [awaitingConfirmation, setAwaitingConfirmation] = useState<boolean>(false);  // ★追加
const [confirmationSessionId, setConfirmationSessionId] = useState<string | null>(null);  // ★追加
const chatEndRef = useRef<HTMLDivElement>(null);
```

**修正理由:**
- 曖昧性確認待ち状態を管理
- SSEセッションIDを保持

---

#### **3. sendTextMessage()の修正**

**ファイル:** `/app/Morizo-web/components/ChatSection.tsx`の`sendTextMessage()`関数（45-99行目）

**修正内容:**
1. SSEセッションIDの生成ロジックを変更
   - 曖昧性確認中は既存のセッションIDを使用
   - 新規リクエストは新しいセッションIDを生成

2. `is_confirmation_response`フラグの送信
   - `awaitingConfirmation`が`true`の場合は`true`を送信

3. レスポンス処理の追加
   - `requires_confirmation`が`true`の場合、状態を保存

**修正理由:**
- バックエンドに曖昧性解決の回答であることを明示的に伝える
- SSEセッションIDを継続

---

## 修正の影響範囲

### **バックエンド:**
1. `api/models/responses.py` - ChatResponseにフィールド追加
2. `core/agent.py` - `_handle_confirmation()`と`_create_confirmation_message()`の改善
3. `api/routes/chat.py` - レスポンスに情報追加

### **フロントエンド:**
1. `/app/Morizo-web/components/ChatSection.tsx` - 状態管理と送信ロジックの追加

### **影響を受けない部分:**
- ActionPlanner - 変更なし
- TaskExecutor - 変更なし
- ConfirmationService - 変更なし
- SessionService - 変更なし（既に実装済み）
- その他のフロントエンドコンポーネント - 変更なし

### **後方互換性:**
- ✅ 新しいフィールドはオプショナルのため、既存の動作に影響なし
- ✅ フロントエンドの古いバージョンでも動作（ただし曖昧性解決は機能しない）

---

## 実装順序

1. **バックエンド: ChatResponseモデル拡張**
2. **バックエンド: _create_confirmation_message()改善**
3. **バックエンド: _handle_confirmation()修正**
4. **バックエンド: APIルート修正**
5. **フロントエンド: ChatMessage型拡張**
6. **フロントエンド: 状態管理追加**
7. **フロントエンド: sendTextMessage()修正**
8. **統合テスト**

---

## テストシナリオ

### **シナリオ1: 曖昧性解決の正常フロー**
1. ユーザー: 「りんごを削除して」→ 3つの選択肢が表示される
2. システム: `requires_confirmation: true`を返す
3. フロントエンド: 同じSSEセッションIDを保持
4. ユーザー: 「最新の」
5. フロントエンド: `is_confirmation_response: true`で送信
6. バックエンド: 保存された状態から再開、ActionPlannerをスキップ
7. システム: 最新のりんごを削除

### **シナリオ2: 通常リクエスト（曖昧でない）**
1. ユーザー: 「在庫一覧を見せて」
2. システム: `requires_confirmation: false`で通常処理

### **シナリオ3: 曖昧性解決後の新しいリクエスト**
1. ユーザー: 「りんごを削除して」→ 選択肢表示
2. ユーザー: 「やっぱり牛乳を追加して」（全く別のリクエスト）
3. システム: 長いメッセージなので新規リクエストと判定
4. 通常のActionPlannerフローで処理

---

## TODOリスト

- [ ] ChatResponseモデルにrequires_confirmationとconfirmation_session_idフィールドを追加
- [ ] _create_confirmation_message()を改善してambiguity_infoの構造に対応
- [ ] _handle_confirmation()でレスポンスに曖昧性情報を含める
- [ ] api/routes/chat.pyのchat()エンドポイントでrequires_confirmationを返す
- [ ] ChatMessage型にrequiresConfirmationフィールドを追加
- [ ] awaitingConfirmationとconfirmationSessionIdの状態管理を追加
- [ ] sendTextMessage()でis_confirmation_responseフラグとSSEセッションID継続を実装
- [ ] 統合テスト：曖昧性解決の正常フロー、通常リクエスト、新しいリクエストの3シナリオを確認

---

## 既に実装済みの内容（第1フェーズ）

### **SessionService拡張**
- ✅ `save_confirmation_state()` - 曖昧性解決状態の保存
- ✅ `get_confirmation_state()` - 状態の取得
- ✅ `clear_confirmation_state()` - 状態のクリア

### **TrueReactAgent基本ロジック**
- ✅ `__init__()` - SessionServiceの初期化
- ✅ `process_request()` - `is_confirmation_response`分岐ロジック
- ✅ `_resume_from_confirmation()` - ActionPlannerをスキップしてTaskExecutor再実行
- ✅ `_create_confirmation_message()` - 確認メッセージ生成（要改善）

### **APIモデル拡張**
- ✅ `ChatRequest`に`is_confirmation_response: bool = False`フィールド追加

### **APIルート**
- ✅ `chat()`エンドポイントで`is_confirmation_response`をTrueReactAgentに渡す

---

## 次のセッションでの開始方法

```
plan.mdを読んで、TODOリストの項目を実装してください
```

---

## 曖昧性解決の実装状況（2025-10-15 06:30時点）

### これまで試したこととその結果

#### ✅ 完了した実装
1. **ChatResponseモデル拡張** - `requires_confirmation`と`confirmation_session_id`フィールドを追加
2. **_create_confirmation_message()改善** - `candidates`を`items`に修正、詳細な確認メッセージ生成
3. **_handle_confirmation()修正** - レスポンスに曖昧性情報を含む辞書を返すように変更
4. **APIルート修正** - `process_request()`の戻り値を適切に処理
5. **フロントエンド修正** - ChatMessage型拡張、状態管理追加、sendTextMessage()修正
6. **デバッグログ追加** - フロントエンドとバックエンドに詳細なログを追加

#### ❌ 失敗した修正試行
1. **Pydantic Field定義修正** - `Field(False)` → `Field(default=False)` → **効果なし**
2. **Pydantic model_config追加** - `ser_json_exclude_defaults=False` → **効果なし**
3. **FastAPIデコレータ設定** - `response_model_exclude_defaults=False` → **効果なし**
4. **response_model削除** - `response.dict()`で生の辞書を返す → **効果なし**

### 現在の状況

#### バックエンドログ（正常）
```
📤 [AGENT] Returning confirmation result: {
  'response': '複数のりんごが見つかりました...', 
  'requires_confirmation': True, 
  'confirmation_session_id': '984a1fc4-...'
}
🔍 [API] Final response object: {
  'response': '...', 
  'success': True, 
  'requires_confirmation': True, 
  'confirmation_session_id': '984a1fc4-...'
}
```

#### HTTPレスポンス（異常）
```json
{
  "response": "複数のりんごが見つかりました...",
  "success": true
}
```

#### フロントエンドコンソール（異常）
```javascript
[DEBUG] Response received: 
Object { requires_confirmation: undefined, confirmation_session_id: undefined }
```

### 根本原因の特定

**SSE（Server-Sent Events）が原因**

フロントエンドは`useStreamingConnection`を使用してSSE経由でデータを受信している。通常のHTTPレスポンスとは別の処理が必要。

- バックエンドは正しい辞書を返している
- HTTPレスポンスには含まれていない
- SSEの`complete`イベントで`requires_confirmation`と`confirmation_session_id`を含める必要がある

### これからトライすること

#### 1. SSEのcompleteイベント修正
**ファイル**: `api/utils/sse_manager.py`または`core/task_manager.py`
**内容**: `send_complete()`メソッドで`requires_confirmation`と`confirmation_session_id`を含める

#### 2. フロントエンドのSSE処理修正
**ファイル**: `/app/Morizo-web/lib/useStreamingConnection.ts`
**内容**: `complete`イベントで`requires_confirmation`と`confirmation_session_id`を処理

#### 3. テスト手順
1. 「りんごを4個に変更して」→ 詳細な選択肢表示
2. 「2」→ `is_confirmation_response: true`で送信
3. 最新のりんごが更新される

### 重要なポイント

- **バックエンドの実装は完了済み**
- **問題はSSEのデータ伝送**
- **フロントエンドの状態管理は実装済み**
- **デバッグログで問題を特定済み**

---

## 曖昧性確認フロー修正の完全な記録（2025-10-15 最新）

### ✅ 完了した実装

#### 1. バックエンド修正
- **`core/agent.py`**: 
  - 確認処理で`send_complete()`を呼び出し、SSE経由で確認情報を送信
  - 変数スコープエラー修正（`confirmation_result`を正しいスコープ内でアクセス）
  
- **`core/models.py`**: 
  - `TaskChainManager.send_complete()`に`confirmation_data`パラメータ追加
  
- **`api/utils/sse_manager.py`**: 
  - `send_complete()`に`confirmation_data`パラメータ追加
  - `result`に`requires_confirmation`と`confirmation_session_id`を含める処理追加
  
- **`api/routes/chat.py`**:
  - `is_confirmation_response`の値をログ出力
  - `request.model_dump()`でPydanticモデル全体をログ出力
  
- **`api/models/requests.py`**:
  - `Field(False)` → `Field(default=False)`に修正（Pydantic v2推奨形式）

#### 2. フロントエンド修正
- **`/app/Morizo-web/components/streaming/types.ts`**:
  - `StreamingMessage`型の`result`を詳細化（`requires_confirmation`と`confirmation_session_id`を含む）
  
- **`/app/Morizo-web/components/streaming/useStreamingConnection.ts`**:
  - `complete`イベント処理にデバッグログ追加
  
- **`/app/Morizo-web/components/ChatSection.tsx`**:
  - HTTPレスポンスによる曖昧性確認処理を削除（SSEが優先）
  - `onComplete`で確認情報を処理し、状態を更新
  - `setIsTextChatLoading(false)`の呼び出し位置を明示化
  - **重要**: `isConfirmationRequest`変数を導入し、送信時点の状態を記録
  - HTTPレスポンスでの状態リセット条件を修正

### ✅ 動作確認済みの部分

1. **SSE送信**: バックエンドは正しく`requires_confirmation: true`と`confirmation_session_id`をSSEで送信
2. **SSE受信**: フロントエンドは正しくSSE経由で確認情報を受信
3. **状態管理**: `awaitingConfirmation`が正しく`true`に設定される
4. **状態リセット**: 送信時点の状態（`isConfirmationRequest`）を使用して正しくリセット

### ❌ 未解決の問題

#### 問題: `is_confirmation_response`がバックエンドで`False`になる

**フロントエンドログ**（正しい）:
```javascript
[DEBUG] Sending request with: { 
  message: "2", 
  sse_session_id: "552dc501-6694-4061-972c-ba4fba248ce1", 
  is_confirmation_response: true  ← フロントは true を送信
}
```

**バックエンドログ**（誤り）:
```python
🔍 [API] Parsed request model: {
  'message': '2', 
  'token': None, 
  'sse_session_id': '552dc501-6694-4061-972c-ba4fba248ce1', 
  'is_confirmation_response': False  ← バックは False を受信
}
```

**確認済み事項**:
- フロントエンドのコードは正しい（`is_confirmation_response: isConfirmationRequest`を送信）
- `isConfirmationRequest`変数は送信時点で`true`
- Pydanticモデルは`Field(default=False)`で正しく定義
- `authenticatedFetch`はリクエストボディをそのまま渡す

**仮説**:
1. **JSON.stringify()の問題**: JavaScriptの`true`がJSONシリアライズ時に何らかの理由で失われている
2. **Hot Reloadの影響**: `[Fast Refresh] rebuilding`により、変数の値が変わっている可能性
3. **非同期タイミング**: `isConfirmationRequest`の評価と実際の送信のタイミングにズレがある
4. **HTTPリクエスト形式**: Content-Typeやヘッダーの問題でフィールドが欠落している

### 🔍 次のセッションでの作業方針

#### アプローチ1: フロントエンドのリクエストボディを直接ログ出力

**ファイル**: `/app/Morizo-web/components/ChatSection.tsx` (95-100行目付近)

**現在のコード**:
```typescript
body: JSON.stringify({ 
  message: currentMessage,
  sse_session_id: sseSessionId,
  is_confirmation_response: isConfirmationRequest
}),
```

**修正案**:
```typescript
const requestBody = { 
  message: currentMessage,
  sse_session_id: sseSessionId,
  is_confirmation_response: isConfirmationRequest
};
const requestBodyString = JSON.stringify(requestBody);
console.log('[DEBUG] Request body object:', requestBody);
console.log('[DEBUG] Request body string:', requestBodyString);

body: requestBodyString,
```

**目的**: `JSON.stringify()`の前後で`is_confirmation_response`の値を確認

#### アプローチ2: Hot Reloadの影響を排除

**テスト手順**:
1. ブラウザを完全リロード（Ctrl+Shift+R）
2. Hot Reloadが発生しない状態で「りんごを4個に変更して」→「2」を送信
3. バックエンドログで`is_confirmation_response: True`が表示されるか確認

#### アプローチ3: ブラウザのネットワークタブで確認

**手順**:
1. ブラウザの開発者ツール → Networkタブを開く
2. 「2」を送信
3. `/api/chat`リクエストを選択
4. Payloadタブで実際のリクエストボディを確認
5. `is_confirmation_response`の値が`true`か`false`か確認

#### アプローチ4: 代替案 - クエリパラメータまたはヘッダーで送信

`is_confirmation_response`をリクエストボディではなく、クエリパラメータまたはカスタムヘッダーで送信する方法も検討。

### 🎯 推奨アクション

**次のセッションで最初に行うこと**:

1. **アプローチ3**（ネットワークタブ確認）を実施
   - 最も確実に問題箇所を特定できる
   - コード修正不要

2. 結果に応じて:
   - **`is_confirmation_response: true`が含まれている場合**: バックエンドのPydanticパース問題 → アプローチ4を検討
   - **`is_confirmation_response`が含まれていない、または`false`の場合**: フロントエンドのシリアライズ問題 → アプローチ1を実施

3. **アプローチ2**（Hot Reload排除）も並行して実施

### 📝 重要な注意点

- フロントエンドの状態管理は完璧に動作している
- SSEの送受信も完璧に動作している
- 唯一の問題は、HTTPリクエストボディの`is_confirmation_response`フィールドのみ
- この1点が解決すれば、曖昧性確認フローは完全に動作する

---

## 🚨 **重大な問題発見（2025-10-15 11:13）**

### ❌ **完全に異常な状況**

**フロントエンドが送信している内容と、バックエンドが受信している内容が完全に異なります。**

#### フロントエンド（送信）
```json
{"message":"2","sse_session_id":"fc015cb4-d1a2-465b-bf20-5f5ef8053c18","confirm":true}
```

#### バックエンド（受信）
```
🔍 [API] Raw request body: b'{"message":"2","sse_session_id":"fc015cb4-d1a2-465b-bf20-5f5ef8053c18"}'
🔍 [API] Raw JSON: {'message': '2', 'sse_session_id': 'fc015cb4-d1a2-465b-bf20-5f5ef8053c18'}
```

**`confirm` フィールドが完全に消失しています。**

---

## 🔍 **試行した無駄な作業（2025-10-15）**

### 1. **Pydanticバリデータ追加** ❌
- `field_validator` を追加
- 結果: バリデータが呼ばれない（フィールドが存在しないため）

### 2. **フィールド名変更** ❌
- `is_confirmation_response` → `is_confirmation` → `confirm`
- 結果: どの名前でも同じ問題が発生

### 3. **http_request.body()削除** ❌
- FastAPIのボディ読み取り問題を疑った
- 結果: 問題は別の場所にあった

### 4. **クエリパラメータで送信** ❌
- `?confirm=true` で送信
- 結果: Next.jsプロキシがクエリパラメータを削除

### 5. **ヘッダーで送信** ❌
- `x-confirm: true` ヘッダーで送信
- 結果: Next.jsプロキシがヘッダーを削除

### 6. **リクエストボディに戻す** ❌
- 生のJSONを直接読み取り
- 結果: **フロントエンドとバックエンドで送受信内容が異なる**

---

## 🎯 **根本原因の特定**

**これは明らかにNext.jsプロキシまたはFastAPIの深刻な問題です。**

### 可能性
1. **Next.jsプロキシがリクエストボディを改変している**
2. **FastAPIが特定のフィールドを削除している**
3. **認証ミドルウェアがボディを改変している**
4. **CORS設定がフィールドをフィルタリングしている**

---

## 📋 **次セッションでの作業方針**

### 🚨 **絶対にやらないこと**
- フィールド名の変更
- Pydanticバリデータの追加
- クエリパラメータやヘッダーでの送信
- `http_request.body()` の削除

### 🎯 **やるべきこと**
1. **Next.jsプロキシ設定の確認**
   - `next.config.js` の `rewrites` 設定
   - プロキシがリクエストボディを改変していないか

2. **FastAPIのミドルウェア確認**
   - `AuthenticationMiddleware` がボディを改変していないか
   - `LoggingMiddleware` がボディを読み取っていないか

3. **直接接続テスト**
   - Next.jsプロキシを経由せず、直接 `localhost:8000` に接続
   - `fetch('http://localhost:8000/api/chat', ...)` でテスト

4. **CORS設定確認**
   - FastAPIのCORS設定がフィールドをフィルタリングしていないか

### 🔍 **デバッグ手順**
1. Next.jsプロキシを無効化
2. フロントエンドから直接 `localhost:8000` に接続
3. リクエストボディが正しく送信されるか確認
4. 問題が解決すれば、Next.jsプロキシ設定を修正

---

## ⚠️ **重要な警告**

**この問題は、フロントエンドとバックエンドの間で送受信内容が異なるという、極めて深刻な問題です。**

**通常のWebアプリケーションでは発生しない異常な状況です。**

**次セッションでは、この根本原因を特定し、解決する必要があります。**

---

## 🎯 **セッション完了報告（2025-10-15 12:37）**

### ✅ **解決した問題**

#### 1. **Next.jsプロキシでの `confirm` フィールド削除問題**
- **問題**: `/app/Morizo-web/app/api/chat/route.ts` で `confirm` フィールドが無視されていた
- **解決**: 28行目と66-70行目を修正し、`confirm` フィールドを正しく転送
- **結果**: `confirm: true` がバックエンドに正しく届くようになった

#### 2. **SessionServiceのインスタンス管理問題**
- **問題**: 毎回新しい `SessionService` インスタンスが作成され、状態が失われていた
- **解決**: シングルトンパターン + ユーザーID別セッション管理を実装
- **結果**: 曖昧性確認の状態が正しく保持されるようになった

### ❌ **残存する問題**

#### **ConfirmationServiceの確認処理ロジック問題**
- **現状**: `confirm: true` で状態は取得されるが、再度曖昧性確認が発生
- **ログ**: 247-249行目で再度曖昧性確認、250-253行目で状態クリア
- **原因**: ユーザーの選択（「2」）が正しく処理されていない

### 📋 **次セッションでの作業方針**

#### **優先度1: ConfirmationServiceの調査**
1. **`/app/Morizo-aiv2/services/confirmation_service.py` の `process_confirmation` メソッドを調査**
2. **ユーザー選択の解析ロジック（「2」→2番目のアイテム）を確認**
3. **タスクの更新処理で正しいアイテムIDが設定されているか確認**

#### **調査すべき箇所**
- `process_confirmation` メソッドの実装
- ユーザー選択の解析（「2」→`3cdf0f9b-8e59-4fb3-bc1a-bf1448b81e2c`）
- `maintain_task_chain` でのタスク更新

#### **期待される動作**
1. ユーザーが「2」を入力
2. `ConfirmationService` が2番目のアイテム（ID: `3cdf0f9b-8e59-4fb3-bc1a-bf1448b81e2c`）を特定
3. タスクの `item_identifier` を具体的なIDに更新
4. 曖昧性確認なしで実行

### 🔍 **デバッグ手順**
1. `ConfirmationService.process_confirmation` にログを追加
2. ユーザー選択の解析過程を追跡
3. 更新されたタスクの内容を確認

### ⚠️ **重要な注意事項**
- **承認制を絶対に遵守** - 修正前に必ず承認を求める
- **SessionServiceの修正は完了済み** - 再度修正しない
- **Next.jsプロキシの修正は完了済み** - 再度修正しない
- **問題はConfirmationServiceの確認処理ロジック** - ここに集中する

### 📊 **進捗状況**
- ✅ フロントエンド→バックエンド通信問題: **解決済み**
- ✅ セッション状態管理問題: **解決済み**  
- ❌ 確認処理ロジック問題: **未解決** ← **次セッションの作業対象**

