# 09. 曖昧性確認フロー - 完全記録

## 🚨 最大の教訓（冒頭に記載）

**`/app/Morizo-web/app/api/chat/route.ts`の28行目と66-70行目を最初に確認していれば、数時間の無駄な試行錯誤は不要だった。**

**自分のコードを最初に疑うべきだった。**

---

## 📋 問題の全記録（時系列）

### フェーズ1: SSE問題の発見と解決（2025-10-15 06:30）

#### 問題
- `requires_confirmation`がフロントエンドに届かない
- バックエンドは正しい辞書を返しているが、フロントエンドで`undefined`

#### 無駄だった試行（4つ）
1. ❌ **Pydantic Field定義修正** - `Field(False)` → `Field(default=False)` → **効果なし**
2. ❌ **Pydantic model_config追加** - `ser_json_exclude_defaults=False` → **効果なし**
3. ❌ **FastAPIデコレータ設定** - `response_model_exclude_defaults=False` → **効果なし**
4. ❌ **response_model削除** - `response.dict()`で生の辞書を返す → **効果なし**

#### 解決策
- **根本原因**: SSE（Server-Sent Events）でデータを送信していなかった
- **解決**: SSEの`complete`イベントに確認情報を含める

---

### フェーズ2: `is_confirmation_response`が届かない問題（2025-10-15 午前）

#### 問題
- フロントエンドは`true`を送信するが、バックエンドで`false`になる
- フロントエンドのコードは正しい
- Pydanticモデルも正しい
- ログ追加しても問題特定できず

#### 状況
- **完全な謎の状態**
- 通常のWebアプリケーションでは発生しない異常な状況

---

### フェーズ3: `confirm`フィールド削除問題の発見（2025-10-15 11:13）

#### 重大な発見
**フロントエンドとバックエンドで送受信内容が完全に異なる**

- **フロントエンド送信**: `{"message":"2","sse_session_id":"fc015cb4-d1a2-465b-bf20-5f5ef8053c18","confirm":true}`
- **バックエンド受信**: `{"message":"2","sse_session_id":"fc015cb4-d1a2-465b-bf20-5f5ef8053c18"}`

**`confirm`フィールドが完全に消失している。**

#### 無駄だった試行（6つ）
1. ❌ **Pydanticバリデータ追加** - `field_validator`を追加 → バリデータが呼ばれない（フィールドが存在しないため）
2. ❌ **フィールド名変更** - `is_confirmation_response` → `is_confirmation` → `confirm` → どの名前でも同じ問題
3. ❌ **http_request.body()削除** - FastAPIのボディ読み取り問題を疑った → 問題は別の場所
4. ❌ **クエリパラメータで送信** - `?confirm=true`で送信 → Next.jsプロキシがクエリパラメータを削除
5. ❌ **ヘッダーで送信** - `x-confirm: true`ヘッダーで送信 → Next.jsプロキシがヘッダーを削除
6. ❌ **リクエストボディに戻す** - 生のJSONを直接読み取り → **フロントエンドとバックエンドで送受信内容が異なる**

#### 絶望的な状況
- 通常のWebアプリケーションでは発生しない異常な状況
- システムやフレームワークを疑うしかない状態

---

## 🎯 フェーズ4: 真の根本原因（2025-10-15 12:37）**最重要セクション**

### 衝撃的な事実
**フェーズ1～3の全試行錯誤は不要だった**

### 真犯人
**`/app/Morizo-web/app/api/chat/route.ts`**
**自分で実装したコードに問題があった**

### 問題箇所1: 28行目のリクエストボディ解析

#### 修正前（誤り）
```typescript
const { message, sse_session_id } = await request.json();
// confirm フィールドを受け取っていない！
```

#### 修正後（正しい）
```typescript
const { message, sse_session_id, confirm } = await request.json();
// confirm フィールドを追加
```

#### 問題
- `confirm`フィールドを受け取っていない
- フロントエンドから送信された`confirm: true`が**ここで消失**

### 問題箇所2: 66-70行目のバックエンドへの転送

#### 修正前（誤り）
```typescript
body: JSON.stringify({
  message: message,
  sse_session_id: sse_session_id
  // confirm フィールドを送信していない！
}),
```

#### 修正後（正しい）
```typescript
body: JSON.stringify({
  message: message,
  sse_session_id: sse_session_id,
  confirm: confirm || false  // confirm フィールドを追加
}),
```

#### 問題
- `confirm`フィールドをバックエンドに送信していない
- 28行目で受け取れなかった`confirm`を、転送時にも含めていない

### なぜこれが全ての原因だったのか

1. **フロントエンド** → `confirm: true`を送信
2. **route.ts（28行目）** → `confirm`を受け取っていない → **ここで消失**
3. **route.ts（66-70行目）** → バックエンドに転送する際も`confirm`を含めない
4. **バックエンド** → `confirm`を受け取れない
5. **フェーズ1～3** → バックエンド側（Pydantic、FastAPI等）を疑って無駄な試行を繰り返す

### もし最初にここを確認していたら

- **所要時間**: 2分で解決
- **実際の所要時間**: 数時間
- **無駄だった試行**: 
  - フェーズ1の4つの試行
  - フェーズ2の調査
  - フェーズ3の6つの試行
- **結論**: **route.tsの28行目と66-70行目を見れば一目瞭然だった**

### 最大の反省

- **自分のコードを最初に疑うべきだった**
- **プロキシ層（自分で書いたコード）を最初に確認すべきだった**
- **基本的な確認（リクエストの受け取りと転送）を怠った**
- **他人やシステムのせいにしてしまった**
- **複雑な解決策を試す前に、シンプルな箇所を確認すべきだった**

---

### フェーズ5: SessionService問題の発見と解決（2025-10-15 12:37）

#### 問題
- 毎回新しい`SessionService`インスタンスが作成され、状態が失われる

#### 解決
- **シングルトンパターン** + **ユーザーID別セッション管理**を実装
- **結果**: 曖昧性確認の状態が正しく保持される

---

### フェーズ6: メッセージ表示問題の発見と解決（2025-10-15 13:00頃）

#### 問題
- ユーザーが「2」と入力しても処理されない
- メッセージで「番号でお答えください」と表示
- しかし番号選択の処理が未実装

#### 試行錯誤
- `ConfirmationService._generate_confirmation_message`を修正 → **効果なし**
- 実際は`core/agent.py`の`_create_confirmation_message`が使用されていた

#### 解決
- **両方のメッセージ生成メソッドを修正**
  - IDを非表示
  - 番号選択を削除、キーワード選択に統一
- **結果**: 完全に動作

---

## 📊 無駄だった試行の完全な記録

### 合計11個の無駄な試行

1. ❌ **Pydantic Field定義修正** - `Field(False)` → `Field(default=False)`
2. ❌ **Pydantic model_config追加** - `ser_json_exclude_defaults=False`
3. ❌ **FastAPIデコレータ設定** - `response_model_exclude_defaults=False`
4. ❌ **response_model削除** - `response.dict()`で生の辞書を返す
5. ❌ **Pydanticバリデータ追加** - `field_validator`を追加
6. ❌ **フィールド名変更** - `is_confirmation_response` → `is_confirmation` → `confirm`
7. ❌ **http_request.body()削除** - FastAPIのボディ読み取り問題を疑った
8. ❌ **クエリパラメータで送信** - `?confirm=true`で送信
9. ❌ **ヘッダーで送信** - `x-confirm: true`ヘッダーで送信
10. ❌ **リクエストボディに戻す** - 生のJSONを直接読み取り
11. ❌ **ConfirmationService修正** - 実際は別箇所が使用されていた

### 重要な事実
**これら全てが route.ts の確認で回避できた**

---

## 🏗️ 最終的なアーキテクチャ

### 曖昧性確認フローの全体像
```
ユーザー入力 → ActionPlanner → TaskExecutor → ConfirmationService → ユーザー確認 → 実行
```

### フロントエンド↔バックエンドの連携
```
フロントエンド                   バックエンド
┌─────────────────┐             ┌─────────────────┐
│ ChatSection.tsx │             │ core/agent.py  │
│ - 状態管理      │ ←────────→ │ - メッセージ生成 │
│ - 送信制御      │             │ - フロー制御    │
└─────────────────┘             └─────────────────┘
```

### SessionServiceによる状態管理
- **状態保存**: `save_confirmation_state()` - 曖昧性確認状態を保存
- **状態取得**: `get_confirmation_state()` - 保存された状態を取得
- **状態クリア**: `clear_confirmation_state()` - 処理完了後に状態をクリア

### ConfirmationServiceの役割
- **曖昧性検出**: `detect_ambiguity()` - 複数候補の検出
- **応答解析**: `_parse_user_response()` - ユーザー入力の解析
- **戦略判定**: `_determine_strategy()` - キーワードから戦略を決定

### 2つのメッセージ生成箇所
1. **`core/agent.py`の`_create_confirmation_message`** - **実際に使用されるメッセージ生成**
2. **`ConfirmationService._generate_confirmation_message`** - 現在は未使用（整合性のため修正済み）

---

## 📱 ユーザーフレンドリーなメッセージ形式

### 修正後のメッセージ例
```
「りんご」が3件見つかりました。

アイテム1:
  数量: 2.0 本
  保存場所: 冷蔵庫
  期限: 2025-10-04
  追加日: 2025-09-24T10:00:00+00:00

アイテム2:
  数量: 1.0 本
  保存場所: 冷蔵庫
  期限: 2025-10-02
  追加日: 2025-09-25T14:30:00+00:00

アイテム3:
  数量: 3.0 本
  保存場所: 冷蔵庫
  期限: 2025-10-07
  追加日: 2025-09-26T09:15:00+00:00

以下のいずれかを選択してください：
- 「最新の」または「新しい」: 最も最近追加されたもの
- 「古い」または「古いの」: 最も古いもの
- 「全部」または「すべて」: 全てのアイテム
- 「キャンセル」: 操作を中止
```

### 改善点
- **IDを非表示**: ユーザーには不要な技術的情報を削除
- **番号は視認性のため**: 選択肢としては使用しない
- **キーワードベースの選択**: 自然な日本語での選択が可能
- **詳細な説明**: 各選択肢の動作を明確に説明

---

## 🔧 キーワード判定ロジック

### `_determine_strategy`メソッドの実装

**サポートされるキーワード**:

| キーワード | 戦略 | 動作 |
|------------|------|------|
| 「最新の」「新しい」「一番新しい」「新」「最新の」「新しいの」「一番新」 | `by_name_latest` | 最も最近追加されたアイテムを選択 |
| 「古い」「古」「一番古い」「古いの」「古の」「一番古」 | `by_name_oldest` | 最も古いアイテムを選択 |
| 「全部」「すべて」「全て」「全部の」「すべての」「全ての」「全部で」「すべてで」 | `by_name` | 全てのアイテムを選択 |
| 「キャンセル」「やめる」「中止」「止める」等 | `cancelled` | 操作を中止 |

---

## 🔄 動作フロー

### ステップバイステップの説明

1. **ユーザー入力**: 「りんごを4個に変更して」
2. **ActionPlanner**: タスクを生成（`inventory_service.update_inventory`）
3. **TaskExecutor**: 曖昧性検出を実行
4. **ConfirmationService**: 複数のりんごを検出
5. **Agent**: 確認メッセージを生成・送信
6. **フロントエンド**: ユーザーに選択肢を表示
7. **ユーザー入力**: 「最新の」
8. **ConfirmationService**: `by_name_latest`戦略を判定
9. **TaskExecutor**: 最新のりんごを特定・更新
10. **完了**: 成功メッセージを表示

### ログ出力例（成功時）
```
2025-10-15 13:01:46 - morizo_ai.service.tool_router - INFO - Strategy 'by_name_latest' → tool: inventory_update_by_name_latest
2025-10-15 13:01:47 - morizo_ai.mcp.inventory_advanc - INFO - Updating latest item by name: りんご
2025-10-15 13:01:47 - morizo_ai.mcp.inventory_advanc - INFO - Updated latest item: 2a6c9f79-f29c-492d-94f5-20eaab44159c
2025-10-15 13:01:47 - morizo_ai.core.executor - INFO - Task task1 completed successfully
```

---

## ⚠️ 再発防止のためのチェックリスト

### デバッグ時の確認順序

1. **自分のコードを最初に疑う**
   - プロキシ層の実装を確認
   - リクエストの受け取りと転送を確認

2. **基本的な確認を最初に行う**
   - リクエストボディの型定義
   - フィールドの受け取りと転送
   - ログでの送受信内容の確認

3. **複雑な解決策の前にシンプルな確認**
   - フレームワークの設定変更より、自分のコードを確認
   - 外部ツールのせいにしない

4. **メッセージ生成箇所の確認**
   - 複数箇所ある場合は全て確認
   - 実際に使用される箇所を特定

### 今後の注意事項

- **メッセージ生成箇所は`core/agent.py`の`_create_confirmation_message`**
- **`ConfirmationService._generate_confirmation_message`との関係**
- **修正時は両方を確認すること**

---

## 📁 関連ファイル

### バックエンド
- `/app/Morizo-aiv2/core/agent.py` - メッセージ生成とフロー制御
- `/app/Morizo-aiv2/services/confirmation_service.py` - 曖昧性検出と応答解析
- `/app/Morizo-aiv2/services/session_service.py` - 状態管理
- `/app/Morizo-aiv2/services/tool_router.py` - 戦略に基づくツール選択

### フロントエンド
- `/app/Morizo-web/app/api/chat/route.ts` - **APIプロキシ（問題の根本原因）**
- `/app/Morizo-web/components/ChatSection.tsx` - UI状態管理

### MCP層
- `/app/Morizo-aiv2/mcp_servers/inventory_mcp.py` - 在庫操作のMCPツール
- `/app/Morizo-aiv2/mcp_servers/inventory_advanced.py` - 高度な在庫操作

---

## 📊 修正結果

### 修正前の問題
- ❌ IDと番号を表示するが、番号選択が未実装
- ❌ ユーザーが「2」と入力しても処理されない
- ❌ 再度曖昧性確認が発生
- ❌ 数時間の無駄な試行錯誤

### 修正後の動作
- ✅ ユーザーフレンドリーなメッセージ表示
- ✅ キーワードベースの選択が正常動作
- ✅ 曖昧性確認が一度で完了
- ✅ 正しいアイテムが選択・更新される

### テスト結果
```
ユーザー入力: 「りんごを4個に変更して」→「最新の」
結果: 最新のりんご（2025-09-26追加）が4.0本に更新
ログ: Strategy 'by_name_latest' → inventory_update_by_name_latest
```

---

## 🎯 まとめ

### 最大の教訓
**自分のコードを最初に疑うべきだった**

### 問題解決までの道のり
1. **フェーズ1～3**: 11個の無駄な試行（数時間）
2. **フェーズ4**: 真の根本原因発見（route.tsの実装ミス）
3. **フェーズ5～6**: その他の問題解決

### 最終的な成果
- 曖昧性確認フローが完全に動作
- ユーザーフレンドリーなインターフェース
- 正しいアイテム選択と更新

### 重要な教訓
- **プロキシ層の確認を怠った代償は大きい**
- **基本的な確認を最初に行う**
- **他人やシステムのせいにしない**
- **複雑な解決策よりシンプルな確認**

この修正により、ユーザーは直感的にアイテムを選択でき、システムは正確にユーザーの意図を理解して実行できるようになりました。