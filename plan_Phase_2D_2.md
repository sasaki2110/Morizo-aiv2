# Phase 2D-2: フロントエンド実装

## 概要

主菜提案にWeb検索機能を追加した4タスク構成に対応するフロントエンド実装を行います。既存のプリ画像抽出機能を活用してレシピの画像表示、詳細情報表示、URL遷移などの機能を実装します。

## 実装内容

1. **RecipeCandidate型の拡張**
2. **SelectionOptionsの拡張**
3. **既存ImageHandlerコンポーネントの活用**
4. **レシピ詳細モーダル**

## Phase 2D-2-1: RecipeCandidate型の拡張

### **修正する場所**
- **ファイル**: `/app/Morizo-web/types/menu.ts`
- **対象**: `RecipeCandidate`インターフェース

### **修正する内容**
1. **URL情報の追加**
2. **既存フィールドの維持**

### **具体的な変更**
```typescript
export interface RecipeCandidate {
  /** レシピのタイトル */
  title: string;
  /** 食材リスト */
  ingredients: string[];
  /** 調理時間（オプション） */
  cooking_time?: string;
  /** 説明（オプション） */
  description?: string;
  /** カテゴリ */
  category?: 'main' | 'sub' | 'soup';
  /** ソース（LLM/RAG/Web） */
  source?: 'llm' | 'rag' | 'web';
  /** URL情報（新規追加） */
  urls?: RecipeUrl[];
}
```

## Phase 2D-2-2: SelectionOptionsの拡張

### **修正する場所**
- **ファイル**: `/app/Morizo-web/components/SelectionOptions.tsx`
- **対象**: レシピ表示部分

### **修正する内容**
1. **既存ImageHandlerコンポーネントの活用**
2. **URL情報の表示**
3. **詳細サイト遷移機能の追加**
4. **モーダル表示機能の追加**

### **具体的な変更**
```typescript
// レシピカードに画像表示とURL遷移を追加
<div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 border-2 transition-all duration-200">
  {/* 画像表示（既存のImageHandlerコンポーネントを活用） */}
  {candidate.urls && candidate.urls.length > 0 && (
    <div className="mb-3">
      <ImageHandler
        urls={candidate.urls}
        title={candidate.title}
        onUrlClick={(url) => window.open(url, '_blank')}
      />
    </div>
  )}
  
  {/* 既存のレシピ情報 */}
  <div className="flex items-start mb-3">
    <input type="radio" ... />
    <label htmlFor={`recipe-${index}`} className="ml-3 flex-1 cursor-pointer">
      <h4 className="text-lg font-medium text-gray-800 dark:text-white mb-2">
        {index + 1}. {candidate.title}
      </h4>
    </label>
  </div>
  
  {/* URL遷移ボタン */}
  {candidate.urls && candidate.urls.length > 0 && (
    <div className="mt-3">
      <button 
        onClick={() => window.open(candidate.urls[0].url, '_blank')}
        className="w-full px-3 py-2 text-sm bg-blue-100 hover:bg-blue-200 dark:bg-blue-900 dark:hover:bg-blue-800 text-blue-700 dark:text-blue-300 rounded-md transition-colors"
      >
        レシピサイトを見る
      </button>
    </div>
  )}
  
  {/* 詳細モーダルボタン */}
  {candidate.urls && candidate.urls.length > 0 && (
    <div className="mt-2">
      <button 
        onClick={() => onViewDetails(candidate)}
        className="w-full px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md transition-colors"
      >
        詳細を見る
      </button>
    </div>
  )}
</div>
```

## Phase 2D-2-4: レシピ詳細モーダル

### **新規作成ファイル**
- **ファイル**: `/app/Morizo-web/components/RecipeDetailModal.tsx`
- **目的**: レシピの詳細情報表示とサイト遷移

### **実装する機能**
1. **レシピ詳細情報の表示**
2. **既存ImageHandlerコンポーネントの活用**
3. **外部サイトへの遷移**
4. **レスポンシブ対応**

### **具体的な実装**
```typescript
interface RecipeDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  recipe: RecipeCandidate;
}

const RecipeDetailModal: React.FC<RecipeDetailModalProps> = ({
  isOpen,
  onClose,
  recipe
}) => {
  const handleVisitSite = () => {
    if (recipe.urls && recipe.urls.length > 0) {
      window.open(recipe.urls[0].url, '_blank');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* ヘッダー */}
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-xl font-bold text-gray-800 dark:text-white">
              {recipe.title}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              ✕
            </button>
          </div>
          
          {/* 画像表示（既存のImageHandlerコンポーネントを活用） */}
          {recipe.urls && recipe.urls.length > 0 && (
            <div className="mb-4">
              <ImageHandler
                urls={recipe.urls}
                title={recipe.title}
                onUrlClick={(url) => window.open(url, '_blank')}
              />
            </div>
          )}
          
          {/* 食材情報 */}
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-2">
              使用食材
            </h3>
            <p className="text-gray-700 dark:text-gray-300">
              {recipe.ingredients.join(', ')}
            </p>
          </div>
          
          {/* 調理時間 */}
          {recipe.cooking_time && (
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-2">
                調理時間
              </h3>
              <p className="text-gray-700 dark:text-gray-300">
                {recipe.cooking_time}
              </p>
            </div>
          )}
          
          {/* 説明 */}
          {recipe.description && (
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-2">
                説明
              </h3>
              <p className="text-gray-700 dark:text-gray-300">
                {recipe.description}
              </p>
            </div>
          )}
          
          {/* アクションボタン */}
          <div className="flex gap-3">
            <button
              onClick={handleVisitSite}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              レシピサイトを見る
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-300 hover:bg-gray-400 text-gray-700 rounded-lg transition-colors"
            >
              閉じる
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
```

## Phase 2D-2-5: 既存ImageHandlerコンポーネントの活用

### **活用する既存コンポーネント**
- **ファイル**: `/app/Morizo-web/components/ImageHandler.tsx`
- **ファイル**: `/app/Morizo-web/lib/image-extractor.ts`

### **既存機能の活用**
1. **プリ画像抽出**: URLから自動的に画像を抽出
2. **遅延読み込み**: Intersection Observerによる最適化
3. **エラーハンドリング**: 画像読み込み失敗時の適切な処理
4. **レスポンシブ対応**: モバイル・デスクトップ両対応

### **実装方針**
- 新規コンポーネントの作成は不要
- 既存のImageHandlerコンポーネントをそのまま活用
- SelectionOptions内でImageHandlerを呼び出す
- URL情報があれば自動的に画像表示

## Phase 2D-2-6: ChatSectionの拡張

### **修正する場所**
- **ファイル**: `/app/Morizo-web/components/ChatSection.tsx`
- **対象**: 選択UI表示部分

### **修正する内容**
1. **URL情報の統合表示**
2. **ImageHandlerコンポーネントの統合**
3. **モーダル表示機能の統合**

### **具体的な変更**
```typescript
// 選択UI表示部分の拡張
{message.type === 'ai' && message.requiresSelection && message.candidates && message.taskId && (
  <div className="ml-8">
    <SelectionOptions
      candidates={message.candidates}
      onSelect={handleSelection}
      onViewDetails={handleViewDetails} // 追加
      taskId={message.taskId}
      sseSessionId={message.sseSessionId || 'unknown'}
      isLoading={isTextChatLoading}
    />
  </div>
)}

// モーダルの状態管理
const [selectedRecipe, setSelectedRecipe] = useState<RecipeCandidate | null>(null);
const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

const handleViewDetails = (recipe: RecipeCandidate) => {
  setSelectedRecipe(recipe);
  setIsDetailModalOpen(true);
};

// モーダルの表示
{isDetailModalOpen && selectedRecipe && (
  <RecipeDetailModal
    isOpen={isDetailModalOpen}
    onClose={() => {
      setIsDetailModalOpen(false);
      setSelectedRecipe(null);
    }}
    recipe={selectedRecipe}
  />
)}
```

## Phase 2D-2-7: バックエンドレスポンス統合

### **修正する場所**
- **ファイル**: `/app/Morizo-aiv2/services/llm/response_processor.py`
- **対象**: `_process_service_method()`メソッド

### **修正する内容**
1. **task3とtask4の結果統合**
2. **URL情報の統合**
3. **フロントエンド向けレスポンス形式の統一**

### **具体的な変更**
```python
elif service_method == "recipe_service.generate_main_dish_proposals":
    # 主菜提案の場合は選択UI用のデータを生成
    if data.get("success") and data.get("data", {}).get("candidates"):
        candidates = data["data"]["candidates"]
        
        # task4のWeb検索結果を統合（実装予定）
        # web_search_results = get_web_search_results(task_id)
        # for i, candidate in enumerate(candidates):
        #     if i < len(web_search_results):
        #         candidate["urls"] = web_search_results[i]["urls"]
        
        # 選択UI用のデータを返す
        return [], {
            "requires_selection": True,
            "candidates": candidates,
            "task_id": task_id,
            "message": "以下の5件から選択してください:"
        }
    else:
        # エラー時は従来のテキスト表示
        response_parts.extend(self.formatters.format_main_dish_proposals(data))
```

## 実装順序

1. **Phase 2D-2-1** → RecipeCandidate型の拡張
2. **Phase 2D-2-2** → SelectionOptionsの拡張
3. **Phase 2D-2-3** → 既存ImageHandlerコンポーネントの活用
4. **Phase 2D-2-4** → レシピ詳細モーダル
5. **Phase 2D-2-5** → 既存ImageHandlerコンポーネントの活用
6. **Phase 2D-2-6** → ChatSectionの拡張
7. **Phase 2D-2-7** → バックエンドレスポンス統合

## 期待される効果

### **ユーザー体験の改善**
- **画像表示**: 既存のプリ画像抽出機能でレシピの見た目を確認可能
- **URL遷移**: レシピサイトへの直接アクセス
- **詳細情報**: レシピの説明とサイト情報を確認可能
- **モーダル表示**: 見やすい詳細表示とポップアップ機能
- **既存機能活用**: 既存のImageHandlerコンポーネントを活用

### **技術的改善**
- **既存機能活用**: 新規コンポーネント作成不要
- **型安全性**: TypeScriptによる型定義の拡張
- **レスポンシブ対応**: 既存のImageHandlerの機能を活用
- **エラーハンドリング**: 既存の画像読み込み失敗時の処理を活用

## 制約事項

- **既存機能の維持**: Phase 1-2の機能を破壊しない
- **パフォーマンス**: 既存の遅延読み込み機能を活用
- **エラーハンドリング**: 既存の画像読み込み失敗時の処理を活用
- **レスポンシブ**: 既存のImageHandlerの機能を活用

## 次のフェーズ

- **Phase 2D-3**: 結合試験

この実装により、フロントエンド側で既存のプリ画像抽出機能を活用してレシピの画像表示、URL遷移、詳細情報表示、モーダル表示などの機能が完成し、ユーザーが詳細情報を確認してから選択できるUIが実現されます。
