# OCR商品名変換テーブル - DDL

レシートOCR読み取り精度向上のための商品名変換テーブル定義

## 1. テーブル作成

```sql
-- OCR商品名変換テーブル（レシートOCR読み取り精度向上用）
CREATE TABLE ocr_item_mappings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    original_name VARCHAR(255) NOT NULL,  -- OCRで読み取られた元の名前（例: "もっちり仕込み"）
    normalized_name VARCHAR(255) NOT NULL, -- 正規化後の名前（例: "食パン"）
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, original_name)  -- 同一ユーザー内で元の名前は一意
);
```

## 2. インデックス作成

```sql
-- インデックス作成
CREATE INDEX idx_ocr_item_mappings_user_id ON ocr_item_mappings(user_id);
CREATE INDEX idx_ocr_item_mappings_original_name ON ocr_item_mappings(original_name);
CREATE INDEX idx_ocr_item_mappings_normalized_name ON ocr_item_mappings(normalized_name);
```

## 3. 更新日時自動更新のトリガー

```sql
-- 更新日時自動更新のトリガー（既に存在する場合はスキップ）
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_ocr_item_mappings_updated_at BEFORE UPDATE ON ocr_item_mappings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

## 4. Row Level Security (RLS) 設定

```sql
-- RLS有効化
ALTER TABLE ocr_item_mappings ENABLE ROW LEVEL SECURITY;

-- ポリシー作成（ユーザーは自分のデータのみアクセス可能）
CREATE POLICY "Users can view own ocr_item_mappings" ON ocr_item_mappings
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own ocr_item_mappings" ON ocr_item_mappings
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own ocr_item_mappings" ON ocr_item_mappings
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own ocr_item_mappings" ON ocr_item_mappings
    FOR DELETE USING (auth.uid() = user_id);
```

## 実行手順

1. **Supabaseダッシュボード** → **SQL Editor**
2. **上記のSQLを順番に実行**
3. **テーブル作成確認**

## テーブル設計の特徴

### ocr_item_mappings テーブル（OCR商品名変換）
- **original_name**: OCRで読み取られた元の商品名（例: "もっちり仕込み"、"新ＢＰコクのある絹豆腐"）
- **normalized_name**: 正規化後の食材名（例: "食パン"、"豆腐"）
- **user_id**: ユーザーID（ユーザーごとに変換テーブルを管理）
- **UNIQUE(user_id, original_name)**: 同一ユーザー内で元の名前は一意（同じ元の名前に対して複数の変換を登録できない）

## 使用例

### 変換テーブルへの登録例
```sql
-- ユーザーがOCR読み取り編集時に変換した場合の例
INSERT INTO ocr_item_mappings (user_id, original_name, normalized_name)
VALUES (
    'ユーザーID',
    'もっちり仕込み',
    '食パン'
);
```

### 変換テーブルの参照例
```sql
-- OCR結果を変換テーブルで正規化
SELECT 
    COALESCE(m.normalized_name, o.item_name) AS normalized_item_name,
    o.quantity,
    o.unit
FROM ocr_results o
LEFT JOIN ocr_item_mappings m 
    ON m.user_id = 'ユーザーID' 
    AND m.original_name = o.item_name;
```

## セキュリティ
- **RLS**: ユーザーは自分のデータのみアクセス可能
- **CASCADE DELETE**: ユーザー削除時に関連データも削除
- **UUID**: セキュアなID生成

