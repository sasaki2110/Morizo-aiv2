# Morizo AI - データベース設計 (DDL)

## Smart Pantry MVP用テーブル設計

### 1. 基本テーブル構成

```sql
-- 在庫管理テーブル
CREATE TABLE inventory (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    item_name VARCHAR(255) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL DEFAULT 0,
    unit VARCHAR(50) NOT NULL DEFAULT '個',
    storage_location VARCHAR(100), -- '冷蔵庫', '冷凍庫', '常温倉庫', '野菜室'
    expiry_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 料理履歴テーブル（過去に作ったレシピの保存）
CREATE TABLE recipe_historys (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    source VARCHAR(100), -- 'web', 'rag', 'manual'
    url TEXT, -- レシピのURL
    cooked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    rating INTEGER CHECK (rating BETWEEN 1 AND 5), -- 評価
    notes TEXT, -- メモ
    ingredients JSONB, -- 利用食材リスト（食材削除機能用）
    ingredients_deleted BOOLEAN DEFAULT FALSE, -- 食材削除済みフラグ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ユーザー設定テーブル
CREATE TABLE user_settings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3. インデックスと制約

```sql
-- インデックス作成
CREATE INDEX idx_inventory_user_id ON inventory(user_id);
CREATE INDEX idx_inventory_item_name ON inventory(item_name);
CREATE INDEX idx_inventory_storage_location ON inventory(storage_location);
CREATE INDEX idx_recipe_historys_user_id ON recipe_historys(user_id);
CREATE INDEX idx_recipe_historys_title ON recipe_historys(title);

-- 更新日時自動更新のトリガー
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_inventory_updated_at BEFORE UPDATE ON inventory
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recipe_historys_updated_at BEFORE UPDATE ON recipe_historys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_settings_updated_at BEFORE UPDATE ON user_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 4. Row Level Security (RLS) 設定

```sql
-- RLS有効化
ALTER TABLE inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE recipe_historys ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

-- ポリシー作成（ユーザーは自分のデータのみアクセス可能）
CREATE POLICY "Users can view own inventory" ON inventory
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own inventory" ON inventory
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own inventory" ON inventory
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own inventory" ON inventory
    FOR DELETE USING (auth.uid() = user_id);

-- recipe_historysテーブル用ポリシー
CREATE POLICY "Users can view own recipe_historys" ON recipe_historys
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own recipe_historys" ON recipe_historys
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own recipe_historys" ON recipe_historys
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own recipe_historys" ON recipe_historys
    FOR DELETE USING (auth.uid() = user_id);

-- user_settingsテーブル用ポリシー
CREATE POLICY "Users can view own settings" ON user_settings
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own settings" ON user_settings
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own settings" ON user_settings
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own settings" ON user_settings
    FOR DELETE USING (auth.uid() = user_id);
```

## 実行手順

1. **Supabaseダッシュボード** → **SQL Editor**
2. **上記のSQLを順番に実行**
3. **テーブル作成確認**

## テーブル設計の特徴

### inventory テーブル
- **item_name**: 食材名（必須）
- **quantity**: 数量（小数点対応）
- **unit**: 単位（個、kg、L等）
- **storage_location**: 保管場所（冷蔵庫、冷凍庫、常温倉庫、野菜室等）
- **expiry_date**: 消費期限

### recipe_historys テーブル（料理履歴）
- **title**: レシピタイトル
- **source**: レシピの出典（web, rag, manual）
- **url**: レシピのURL（Web検索で見つけた場合）
- **cooked_at**: 実際に作った日時
- **rating**: 評価（1-5段階）
- **notes**: メモ・感想
- **ingredients**: 利用食材リスト（JSONB形式、食材削除機能用）
- **ingredients_deleted**: 食材削除済みフラグ（BOOLEAN）

### user_settings テーブル
- **preferences**: JSONB形式でユーザー設定
- **user_id**: ユニーク制約で1ユーザー1設定

#### MVP段階での想定設定例
```json
{
  "taste_preferences": {
    "spicy_level": 3,
    "sweet_preference": 2,
    "garlic_love": true,
    "cuisine_preferences": ["中華料理", "和食", "イタリアン"]
  }
}
```

#### 将来の一般公開時の拡張案
- **アレルギー情報**: 小麦、乳製品、卵等
- **調理器具制限**: オーブンなし、電子レンジのみ等
- **食事制限**: ベジタリアン、ビーガン、ハラル等
- **調理時間制限**: 15分以内、1時間以内等
- **難易度制限**: 初心者向け、上級者向け等

## セキュリティ
- **RLS**: ユーザーは自分のデータのみアクセス可能
- **CASCADE DELETE**: ユーザー削除時に関連データも削除
- **UUID**: セキュアなID生成
