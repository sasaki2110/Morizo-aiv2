# Phase 2D-2: フロントエンド実装

## 概要

主菜提案にWeb検索機能を追加した4タスク構成に対応するフロントエンド実装を行います。レシピの画像表示、詳細情報表示、ポップアップモーダルなどの機能を実装します。

## 実装内容

1. **レシピ画像表示コンポーネント**
2. **SelectionOptionsの拡張**
3. **レシピ詳細モーダル**

## Phase 2D-2-1: レシピ画像表示コンポーネント

### **新規作成ファイル**
- **ファイル**: `/app/Morizo-web/components/RecipeImageViewer.tsx`
- **目的**: レシピ画像の表示とポップアップ機能

### **実装する機能**
1. **画像表示コンポーネント**
2. **ポップアップビューアー**
3. **詳細サイト遷移機能**
4. **レスポンシブ対応**

### **具体的な実装**
```typescript
interface RecipeImageViewerProps {
  recipes: RecipeWithImage[];
  onRecipeClick: (recipe: RecipeWithImage) => void;
}

interface RecipeWithImage {
  title: string;
  url: string;
  imageUrl?: string;
  description?: string;
  site?: string;
  source?: string;
}

const RecipeImageViewer: React.FC<RecipeImageViewerProps> = ({ 
  recipes, 
  onRecipeClick 
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {recipes.map((recipe, index) => (
        <div 
          key={index}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => onRecipeClick(recipe)}
        >
          {recipe.imageUrl && (
            <div className="aspect-w-16 aspect-h-9">
              <img 
                src={recipe.imageUrl} 
                alt={recipe.title}
                className="w-full h-48 object-cover"
                onError={(e) => {
                  e.currentTarget.src = '/placeholder-recipe.jpg';
                }}
              />
            </div>
          )}
          <div className="p-4">
            <h3 className="text-lg font-medium text-gray-800 dark:text-white mb-2">
              {recipe.title}
            </h3>
            {recipe.description && (
              <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
                {recipe.description}
              </p>
            )}
            {recipe.site && (
              <span className="text-xs text-blue-600 dark:text-blue-400">
                {recipe.site}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
```

## Phase 2D-2-2: SelectionOptionsの拡張

### **修正する場所**
- **ファイル**: `/app/Morizo-web/components/SelectionOptions.tsx`
- **対象**: レシピ表示部分

### **修正する内容**
1. **画像表示機能の追加**
2. **詳細表示ボタンの追加**
3. **Web検索結果の統合表示**

### **具体的な変更**
```typescript
interface SelectionOptionsProps {
  candidates: RecipeCandidate[];
  webSearchResults?: RecipeWithImage[]; // 追加
  onSelect: (selection: number) => void;
  onViewDetails: (recipe: RecipeCandidate) => void; // 追加
  taskId: string;
  sseSessionId: string;
  isLoading?: boolean;
}

// レシピカードに画像表示と詳細ボタンを追加
<div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 border-2 transition-all duration-200">
  {/* 画像表示 */}
  {webSearchResults?.[index]?.imageUrl && (
    <div className="mb-3">
      <img 
        src={webSearchResults[index].imageUrl} 
        alt={candidate.title}
        className="w-full h-32 object-cover rounded-lg"
        onError={(e) => {
          e.currentTarget.style.display = 'none';
        }}
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
  
  {/* 詳細表示ボタン */}
  <div className="mt-3">
    <button 
      onClick={() => onViewDetails(candidate)}
      className="w-full px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md transition-colors"
    >
      詳細を見る
    </button>
  </div>
</div>
```

## Phase 2D-2-3: レシピ詳細モーダル

### **新規作成ファイル**
- **ファイル**: `/app/Morizo-web/components/RecipeDetailModal.tsx`
- **目的**: レシピの詳細情報表示とサイト遷移

### **実装する機能**
1. **レシピ詳細情報の表示**
2. **画像の拡大表示**
3. **外部サイトへの遷移**
4. **レスポンシブ対応**

### **具体的な実装**
```typescript
interface RecipeDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  recipe: RecipeWithImage;
}

const RecipeDetailModal: React.FC<RecipeDetailModalProps> = ({
  isOpen,
  onClose,
  recipe
}) => {
  const handleVisitSite = () => {
    window.open(recipe.url, '_blank');
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
          
          {/* 画像 */}
          {recipe.imageUrl && (
            <div className="mb-4">
              <img 
                src={recipe.imageUrl} 
                alt={recipe.title}
                className="w-full h-64 object-cover rounded-lg"
              />
            </div>
          )}
          
          {/* 説明 */}
          {recipe.description && (
            <div className="mb-4">
              <p className="text-gray-700 dark:text-gray-300">
                {recipe.description}
              </p>
            </div>
          )}
          
          {/* サイト情報 */}
          {recipe.site && (
            <div className="mb-4">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                提供サイト: {recipe.site}
              </span>
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

## Phase 2D-2-4: ChatSectionの拡張

### **修正する場所**
- **ファイル**: `/app/Morizo-web/components/ChatSection.tsx`
- **対象**: 選択UI表示部分

### **修正する内容**
1. **Web検索結果の統合表示**
2. **画像表示機能の追加**
3. **詳細モーダルの統合**

### **具体的な変更**
```typescript
// 選択UI表示部分の拡張
{message.type === 'ai' && message.requiresSelection && message.candidates && message.taskId && (
  <div className="ml-8">
    <SelectionOptions
      candidates={message.candidates}
      webSearchResults={message.webSearchResults} // 追加
      onSelect={handleSelection}
      onViewDetails={handleViewDetails} // 追加
      taskId={message.taskId}
      sseSessionId={message.sseSessionId || 'unknown'}
      isLoading={isTextChatLoading}
    />
  </div>
)}

// 詳細モーダルの状態管理
const [selectedRecipe, setSelectedRecipe] = useState<RecipeWithImage | null>(null);
const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

const handleViewDetails = (recipe: RecipeCandidate) => {
  // Web検索結果から対応するレシピを検索
  const webRecipe = webSearchResults?.find(r => r.title === recipe.title);
  if (webRecipe) {
    setSelectedRecipe(webRecipe);
    setIsDetailModalOpen(true);
  }
};
```

## Phase 2D-2-5: 型定義の追加

### **新規作成ファイル**
- **ファイル**: `/app/Morizo-web/types/recipe.ts`
- **目的**: レシピ関連の型定義

### **実装する型定義**
```typescript
export interface RecipeWithImage {
  title: string;
  url: string;
  imageUrl?: string;
  description?: string;
  site?: string;
  source?: string;
}

export interface RecipeCandidate {
  title: string;
  ingredients: string[];
  cooking_time?: string;
  description?: string;
  source?: string;
}

export interface WebSearchResult {
  recipes: RecipeWithImage[];
  success: boolean;
  error?: string;
}
```

## 実装順序

1. **Phase 2D-2-1** → レシピ画像表示コンポーネント
2. **Phase 2D-2-2** → SelectionOptionsの拡張
3. **Phase 2D-2-3** → レシピ詳細モーダル
4. **Phase 2D-2-4** → ChatSectionの拡張
5. **Phase 2D-2-5** → 型定義の追加

## 期待される効果

### **ユーザー体験の改善**
- **画像表示**: レシピの見た目を確認可能
- **詳細情報**: レシピの説明とサイト情報を確認可能
- **ポップアップモーダル**: 見やすい詳細表示
- **外部サイト遷移**: 詳細なレシピ情報へのアクセス

### **技術的改善**
- **コンポーネント化**: 再利用可能なUIコンポーネント
- **レスポンシブ対応**: モバイル・デスクトップ両対応
- **エラーハンドリング**: 画像読み込み失敗時の適切な処理
- **型安全性**: TypeScriptによる型定義

## 制約事項

- **既存機能の維持**: Phase 1-2の機能を破壊しない
- **パフォーマンス**: 画像読み込み時間の考慮
- **エラーハンドリング**: 画像読み込み失敗時の処理
- **レスポンシブ**: モバイル・デスクトップ両対応

## 次のフェーズ

- **Phase 2D-3**: 結合試験

この実装により、フロントエンド側でレシピの画像表示、詳細情報表示、ポップアップモーダルなどの機能が完成し、ユーザーが詳細情報を確認してから選択できるUIが実現されます。
