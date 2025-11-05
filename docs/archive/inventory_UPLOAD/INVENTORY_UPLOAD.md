# 在庫初期登録機能 - 実装計画

## 📋 概要

在庫管理システムに、CSVアップロード機能とレシートOCR機能を追加します。
初期登録時に大量の在庫データを効率的に登録できるようにします。

**作成日**: 2025年1月29日  
**バージョン**: 1.0  
**目的**: CSVファイルとレシート画像から在庫データを一括登録

## 🎯 目標

1. **CSVアップロード機能**: 指定フォーマットのCSVファイルから在庫データを一括登録
2. **レシートOCR機能**: レシート画像を解析して在庫データを自動抽出・登録

## 📊 現状の確認

### 既存機能

1. **在庫管理のCRUD機能**: 実装済み
   - 単一アイテムの追加・更新・削除・一覧取得
   - `api/routes/inventory.py`: REST APIエンドポイント
   - `mcp_servers/inventory_crud.py`: CRUD操作クラス
   - `InventoryPanel.tsx`: フロントエンドUI（一覧・編集・削除）

2. **直接DBアクセス**: 既に実装済み
   - `api/routes/inventory.py`で`InventoryCRUD`を直接呼び出し
   - コメント: 「【特例】直接DB呼び出しは設計思想に反するが、在庫ビューアーは例外とする」

3. **フロントエンド**: Next.js/React
   - `/app/Morizo-web/components/InventoryPanel.tsx`
   - `/app/Morizo-web/components/InventoryEditModal.tsx`

4. **LLM設定**: デフォルトで`gpt-4o-mini`を使用
   - `OPENAI_MODEL`環境変数で変更可能
   - 各LLMクライアントで環境変数から読み込み

### 課題点

1. **一括登録機能**: 現在は1件ずつ登録（`add_item`メソッドのみ）
2. **CSVアップロード機能**: 未実装
3. **OCR機能**: 未実装（マルチモーダルモデルが必要）

## 🔧 技術スタック

### 既存の依存関係

- `python-multipart>=0.0.6`: ファイルアップロード対応（既に導入済み）
- `pandas>=2.0.0`: CSV解析（既に導入済み）
- `openai>=1.50.0`: OpenAI API（既に導入済み）
- `fastapi>=0.115.0`: Webフレームワーク（既に導入済み）

### 新規追加が必要な依存関係

- なし（既存の依存関係で対応可能）

### 環境変数

- `OPENAI_MODEL`: 通常の会話用（デフォルト: `gpt-4o-mini`）
- `OPENAI_OCR_MODEL`: OCR用（新規追加、デフォルト: `gpt-4o`）
- `OPENAI_API_KEY`: OpenAI APIキー（既存）

## 📝 機能詳細

### 1. CSVアップロード機能

#### 1.1 機能概要

ユーザーがCSVファイルをアップロードし、在庫データを一括登録します。

#### 1.2 CSVフォーマット

```csv
item_name,quantity,unit,storage_location,expiry_date
りんご,5,個,冷蔵庫,2024-02-15
米,2,kg,常温倉庫,
牛乳,1,L,冷蔵庫,2024-01-25
```

**必須項目**:
- `item_name`: アイテム名（文字列、1-100文字）
- `quantity`: 数量（数値、0より大きい）
- `unit`: 単位（文字列、1-20文字）

**オプション項目**:
- `storage_location`: 保管場所（文字列、最大50文字、デフォルト: "冷蔵庫"）
- `expiry_date`: 消費期限（日付形式: YYYY-MM-DD）

**エンコーディング**: UTF-8（BOM付き・なし両対応）

#### 1.3 バックエンドAPI

**エンドポイント**: `POST /api/inventory/upload-csv`

**リクエスト**:
- Content-Type: `multipart/form-data`
- フィールド: `file` (CSVファイル)

**レスポンス**:
```json
{
  "success": true,
  "total": 100,
  "success_count": 98,
  "error_count": 2,
  "errors": [
    {
      "row": 5,
      "item_name": "不正なデータ",
      "error": "数量は0より大きい値が必要です"
    }
  ]
}
```

**処理フロー**:
1. ファイル受信・検証（ファイルサイズ、形式チェック）
2. CSV解析（`pandas`または標準`csv`モジュール）
3. データバリデーション（各行の必須項目・データ型チェック）
4. 一括DB挿入（`InventoryCRUD.add_items_bulk`）
5. 結果返却（成功件数・エラー件数・エラー詳細）

#### 1.4 フロントエンドUI

**追加場所**: `InventoryPanel.tsx`

**UI要素**:
- CSVアップロードボタン
- ファイル選択ダイアログ
- アップロード進捗表示（進捗バー、メッセージ）
- 結果表示（成功件数、エラー件数、エラー詳細）
- エラーハンドリング（ファイル形式エラー、ネットワークエラー等）

**実装方針**:
- 既存の「+ 新規追加」ボタンの近くに「CSVアップロード」ボタンを追加
- モーダルまたはインラインでファイル選択と進捗表示

### 2. レシートOCR機能

#### 2.1 機能概要

レシート画像をアップロードし、OCR解析で在庫情報を自動抽出して登録します。

#### 2.2 対応画像形式

- JPEG (.jpg, .jpeg)
- PNG (.png)
- 最大ファイルサイズ: 10MB
- 推奨サイズ: 1920x1080以下

#### 2.3 バックエンドAPI

**エンドポイント**: `POST /api/inventory/ocr-receipt`

**リクエスト**:
- Content-Type: `multipart/form-data`
- フィールド: `image` (画像ファイル)

**レスポンス**:
```json
{
  "success": true,
  "items": [
    {
      "item_name": "りんご",
      "quantity": 5,
      "unit": "個",
      "storage_location": "冷蔵庫",
      "expiry_date": null
    }
  ],
  "registered_count": 5,
  "errors": []
}
```

**処理フロー**:
1. 画像ファイル受信・検証（ファイルサイズ、形式チェック）
2. 画像をbase64エンコード
3. `gpt-4o`でOCR解析
   - プロンプト: レシート画像から在庫情報を抽出
   - レスポンス形式: JSON（構造化データ）
4. 解析結果をバリデーション
5. CSV登録機能を呼び出し（`InventoryCRUD.add_items_bulk`）
6. 結果返却（解析結果、登録件数、エラー情報）

#### 2.4 OCRプロンプト設計

```
このレシート画像から、在庫管理に必要な情報を抽出してください。

抽出すべき情報:
- 商品名（item_name）
- 数量（quantity）
- 単位（unit）
- 保管場所（storage_location、推測可）
- 消費期限（expiry_date、もし記載されていれば）

レスポンス形式: JSON配列
[
  {
    "item_name": "商品名",
    "quantity": 数量,
    "unit": "単位",
    "storage_location": "保管場所",
    "expiry_date": "YYYY-MM-DD または null"
  }
]
```

#### 2.5 フロントエンドUI

**追加場所**: `InventoryPanel.tsx`

**UI要素**:
- レシート画像アップロードボタン
- 画像ファイル選択ダイアログ
- 画像プレビュー
- OCR解析進捗表示（進捗バー、メッセージ）
- 解析結果の確認・編集UI（テーブル形式）
  - 各項目を編集可能
  - 登録する項目を選択可能（チェックボックス）
- 登録ボタン
- 結果表示（登録件数、エラー情報）

**実装方針**:
- 既存の「+ 新規追加」ボタンの近くに「レシートOCR」ボタンを追加
- モーダルで画像選択→プレビュー→解析→結果確認→登録の流れ

## 🏗️ アーキテクチャ設計

### バックエンド構造

```
api/routes/inventory.py
  ├─ POST /api/inventory/upload-csv
  └─ POST /api/inventory/ocr-receipt

mcp_servers/inventory_crud.py
  └─ InventoryCRUD
      ├─ add_item (既存)
      └─ add_items_bulk (新規追加)

services/ocr_service.py (新規作成)
  └─ OCRService
      ├─ analyze_receipt_image
      └─ extract_inventory_items
```

### フロントエンド構造

```
/app/Morizo-web/components/
  ├─ InventoryPanel.tsx (拡張)
  ├─ InventoryEditModal.tsx (既存)
  ├─ InventoryCSVUploadModal.tsx (新規作成)
  └─ InventoryOCRModal.tsx (新規作成)
```

### モデル選択の実装方針

**通常の会話**: `gpt-4o-mini`（既存）
- `OPENAI_MODEL=gpt-4o-mini`

**OCR機能**: `gpt-4o`（新規）
- `OPENAI_OCR_MODEL=gpt-4o`（環境変数、新規追加）

**実装**:
- `services/ocr_service.py`で`AsyncOpenAI`クライアントを初期化
- 環境変数から`OPENAI_OCR_MODEL`を読み込み（デフォルト: `gpt-4o`）

## 📋 実装フェーズ分割

コンテキストウィンドウに配慮し、1セッション（1-3時間）で実装・テスト・不具合対応が完了できる単位に分割します。

### Phase 1: CSV一括登録機能（バックエンド）

**目標**: CSVファイルから在庫データを一括登録するバックエンド機能を実装

**実装内容**:
1. `InventoryCRUD.add_items_bulk`メソッドの追加
2. `POST /api/inventory/upload-csv`エンドポイントの実装
3. CSV解析・バリデーション処理
4. エラーハンドリング（部分成功の処理）

**対象ファイル**:
- `mcp_servers/inventory_crud.py` (拡張)
- `api/routes/inventory.py` (拡張)
- `api/models/requests.py` (拡張、レスポンスモデル追加)

**テスト項目**:
- CSVファイルのアップロード
- 正常データの一括登録
- エラーデータの検出と報告
- 部分成功の処理

**推定時間**: 1-2時間

---

### Phase 2: CSVアップロード機能（フロントエンド）

**目標**: CSVファイルをアップロードして在庫データを一括登録するUIを実装

**実装内容**:
1. `InventoryCSVUploadModal.tsx`コンポーネントの作成
2. `InventoryPanel.tsx`にCSVアップロードボタンを追加
3. ファイル選択・進捗表示・結果表示の実装
4. エラーハンドリング

**対象ファイル**:
- `/app/Morizo-web/components/InventoryCSVUploadModal.tsx` (新規作成)
- `/app/Morizo-web/components/InventoryPanel.tsx` (拡張)

**テスト項目**:
- CSVファイルの選択とアップロード
- 進捗表示の動作
- 成功・エラーメッセージの表示
- エラー詳細の表示

**推定時間**: 1-2時間

---

### Phase 3: OCR機能（バックエンド）

**目標**: レシート画像を解析して在庫データを抽出するバックエンド機能を実装

**実装内容**:
1. `services/ocr_service.py`の作成（OCRServiceクラス）
2. `POST /api/inventory/ocr-receipt`エンドポイントの実装
3. 画像処理（base64エンコード、検証）
4. `gpt-4o`を使用したOCR解析
5. 解析結果の構造化とバリデーション

**対象ファイル**:
- `services/ocr_service.py` (新規作成)
- `api/routes/inventory.py` (拡張)
- `api/models/requests.py` (拡張、レスポンスモデル追加)
- `env.example` (拡張、`OPENAI_OCR_MODEL`追加)

**テスト項目**:
- 画像ファイルのアップロード
- OCR解析の実行
- 解析結果の構造化
- エラーハンドリング（画像形式エラー、OCR失敗等）

**推定時間**: 2-3時間

---

### Phase 4: OCR機能（フロントエンド）

**目標**: レシート画像をアップロードしてOCR解析し、在庫データを登録するUIを実装

**実装内容**:
1. `InventoryOCRModal.tsx`コンポーネントの作成
2. `InventoryPanel.tsx`にレシートOCRボタンを追加
3. 画像選択・プレビュー・解析進捗表示の実装
4. 解析結果の確認・編集UIの実装
5. 登録機能の実装

**対象ファイル**:
- `/app/Morizo-web/components/InventoryOCRModal.tsx` (新規作成)
- `/app/Morizo-web/components/InventoryPanel.tsx` (拡張)

**テスト項目**:
- 画像ファイルの選択とプレビュー
- OCR解析の実行と進捗表示
- 解析結果の表示と編集
- 登録機能の動作

**推定時間**: 2-3時間

---

### Phase 5: 統合テストと不具合対応

**目標**: 全体の統合テストを実施し、不具合を修正

**実装内容**:
1. CSVアップロード機能の統合テスト
2. OCR機能の統合テスト
3. エッジケースのテスト
4. パフォーマンステスト（大量データ）
5. 不具合の修正

**テスト項目**:
- CSVアップロードのエンドツーエンドテスト
- OCRのエンドツーエンドテスト
- 大量データの処理（100件以上）
- エラーハンドリングの確認
- UI/UXの確認

**推定時間**: 1-2時間

---

## 📚 実装詳細ドキュメント

実装の詳細は、各フェーズごとのドキュメントを参照してください：

- [INVENTORY_UPLOAD_Phase1.md](./INVENTORY_UPLOAD_Phase1.md) - CSV一括登録機能（バックエンド）
- [INVENTORY_UPLOAD_Phase2.md](./INVENTORY_UPLOAD_Phase2.md) - CSVアップロード機能（フロントエンド）
- [INVENTORY_UPLOAD_Phase3.md](./INVENTORY_UPLOAD_Phase3.md) - OCR機能（バックエンド）
- [INVENTORY_UPLOAD_Phase4.md](./INVENTORY_UPLOAD_Phase4.md) - OCR機能（フロントエンド）
- [INVENTORY_UPLOAD_Phase5.md](./INVENTORY_UPLOAD_Phase5.md) - 統合テストと不具合対応

## 🚨 注意事項

### 1. パフォーマンス

- **大量データ**: 1000件以上のデータをアップロードする場合は、非同期処理またはバッチ処理を検討
- **OCR処理時間**: 画像解析は数秒〜数十秒かかる可能性があるため、非同期処理またはSSEで進捗通知を実装

### 2. エラーハンドリング

- **部分成功**: CSVアップロードで一部失敗した場合、成功したものは登録し、失敗したものはエラー詳細を返却
- **OCR失敗**: OCR解析が失敗した場合、エラーメッセージを表示し、手動入力へのフォールバックを提供

### 3. セキュリティ

- **ファイルサイズ制限**: アップロードファイルのサイズ制限を設定（CSV: 10MB、画像: 10MB）
- **ファイル形式検証**: アップロードファイルの形式を厳密に検証
- **認証**: 既存の認証ミドルウェアを使用

### 4. コスト

- **OCRコスト**: `gpt-4o`は`gpt-4o-mini`より高額。画像サイズに応じたトークン消費に注意
- **使用量監視**: OCR機能の使用量を監視し、コストを把握

### 5. 精度

- **OCR精度**: レシートの形式や品質によって精度が変動する可能性がある
- **フォールバック**: OCR結果が不正確な場合、手動修正UIを提供

## 📊 成功基準

### Phase 1: CSV一括登録機能（バックエンド）
- [ ] CSVファイルから在庫データを一括登録できる
- [ ] エラーデータを検出して報告できる
- [ ] 部分成功を処理できる

### Phase 2: CSVアップロード機能（フロントエンド）
- [ ] CSVファイルを選択してアップロードできる
- [ ] 進捗表示が動作する
- [ ] 成功・エラーメッセージが表示される

### Phase 3: OCR機能（バックエンド）
- [ ] レシート画像を解析して在庫情報を抽出できる
- [ ] 解析結果を構造化データに変換できる
- [ ] エラーハンドリングが動作する

### Phase 4: OCR機能（フロントエンド）
- [ ] レシート画像を選択してアップロードできる
- [ ] OCR解析の進捗が表示される
- [ ] 解析結果を確認・編集して登録できる

### Phase 5: 統合テストと不具合対応
- [ ] エンドツーエンドテストが成功する
- [ ] 大量データの処理が正常に動作する
- [ ] エラーハンドリングが適切に動作する

## 🔄 実装順序

1. **Phase 1** → CSV一括登録機能（バックエンド）
2. **Phase 2** → CSVアップロード機能（フロントエンド）
3. **Phase 3** → OCR機能（バックエンド）
4. **Phase 4** → OCR機能（フロントエンド）
5. **Phase 5** → 統合テストと不具合対応

## 📚 参考資料

- 既存の在庫管理機能: `api/routes/inventory.py`
- 既存のCRUDクラス: `mcp_servers/inventory_crud.py`
- 既存のフロントエンドUI: `/app/Morizo-web/components/InventoryPanel.tsx`
- OpenAI API ドキュメント: https://platform.openai.com/docs/api-reference

