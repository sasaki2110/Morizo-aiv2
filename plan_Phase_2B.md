# Phase 2B: フロントエンド連携の実装

## 概要

Phase 2Bでは、Phase 2Aで実装したバックエンド基盤と連携するフロントエンド機能を実装します。ユーザー選択UI、選択結果送信、リアルタイム通信機能を追加し、ユーザー体験を向上させます。

## 対象範囲

- ユーザー選択UIコンポーネント
- 選択結果送信機能
- リアルタイム通信機能
- 状態管理の拡張
- ユーザー体験の改善

## 実装計画

### 1. ユーザー選択UIコンポーネント

#### 1.1 選択肢表示コンポーネント
**修正する場所**: `frontend/components/SelectionOptions.tsx`

**修正する内容**:
```typescript
import React from 'react';
import { RecipeCandidate } from '../types/recipe';

interface SelectionOptionsProps {
  candidates: RecipeCandidate[];
  onSelect: (selection: number) => void;
  taskId: string;
  isLoading?: boolean;
}

const SelectionOptions: React.FC<SelectionOptionsProps> = ({ 
  candidates, 
  onSelect, 
  taskId,
  isLoading = false
}) => {
  const handleSelection = async (selection: number) => {
    try {
      // バックエンドに選択結果を送信
      const response = await fetch('/api/chat/selection', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          task_id: taskId,
          selection: selection
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.success) {
        onSelect(selection);
      } else {
        throw new Error(result.error || 'Selection failed');
      }
    } catch (error) {
      console.error('Selection failed:', error);
      alert('選択に失敗しました。もう一度お試しください。');
    }
  };

  if (isLoading) {
    return (
      <div className="selection-options loading">
        <div className="loading-spinner"></div>
        <p>選択を処理中...</p>
      </div>
    );
  }

  return (
    <div className="selection-options">
      <h3>以下の5件から選択してください:</h3>
      <div className="candidates-grid">
        {candidates.map((candidate, index) => (
          <div key={index} className="candidate-card">
            <div className="candidate-header">
              <h4>{index + 1}. {candidate.title}</h4>
            </div>
            <div className="candidate-content">
              <p className="ingredients">
                <strong>食材:</strong> {candidate.ingredients.join(', ')}
              </p>
              {candidate.cooking_time && (
                <p className="cooking-time">
                  <strong>調理時間:</strong> {candidate.cooking_time}
                </p>
              )}
              {candidate.description && (
                <p className="description">{candidate.description}</p>
              )}
            </div>
            <div className="candidate-actions">
              <button 
                className="select-button"
                onClick={() => handleSelection(index + 1)}
              >
                選択
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SelectionOptions;
```

**修正の理由**: ユーザーが選択肢を視覚的に確認して選択できるUIを提供するため

**修正の影響**: 既存のチャットUIに影響なし

#### 1.2 選択肢表示のスタイリング
**修正する場所**: `frontend/styles/SelectionOptions.css`

**修正する内容**:
```css
.selection-options {
  margin: 20px 0;
  padding: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background-color: #f9f9f9;
}

.selection-options h3 {
  margin-bottom: 20px;
  color: #333;
  text-align: center;
}

.candidates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.candidate-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: box-shadow 0.3s ease;
}

.candidate-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.candidate-header h4 {
  margin: 0 0 10px 0;
  color: #2c3e50;
  font-size: 1.1em;
}

.candidate-content {
  margin-bottom: 15px;
}

.candidate-content p {
  margin: 5px 0;
  font-size: 0.9em;
  line-height: 1.4;
}

.ingredients {
  color: #666;
}

.cooking-time {
  color: #888;
}

.description {
  color: #555;
  font-style: italic;
}

.candidate-actions {
  text-align: center;
}

.select-button {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 1em;
  transition: background-color 0.3s ease;
}

.select-button:hover {
  background-color: #2980b9;
}

.select-button:disabled {
  background-color: #bdc3c7;
  cursor: not-allowed;
}

.loading {
  text-align: center;
  padding: 40px;
}

.loading-spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
```

**修正の理由**: 選択肢を視覚的に分かりやすく表示するため

**修正の影響**: 既存のスタイルに影響なし

### 2. チャットインターフェースの拡張

#### 2.1 チャットインターフェースの状態管理
**修正する場所**: `frontend/components/ChatInterface.tsx`

**修正する内容**:
```typescript
import React, { useState, useEffect } from 'react';
import SelectionOptions from './SelectionOptions';
import { RecipeCandidate } from '../types/recipe';

interface ChatResponse {
  success: boolean;
  response: string;
  requires_selection?: boolean;
  candidates?: RecipeCandidate[];
  task_id?: string;
  error?: string;
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Array<{role: 'user' | 'assistant', content: string}>>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isWaitingForSelection, setIsWaitingForSelection] = useState(false);
  const [selectionCandidates, setSelectionCandidates] = useState<RecipeCandidate[]>([]);
  const [currentTaskId, setCurrentTaskId] = useState<string>('');

  const handleChatResponse = (response: ChatResponse) => {
    if (response.requires_selection && response.candidates && response.task_id) {
      // ユーザー選択が必要な場合
      setIsWaitingForSelection(true);
      setSelectionCandidates(response.candidates);
      setCurrentTaskId(response.task_id);
      
      // 選択要求メッセージを追加
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.response || '以下の5件から選択してください:'
      }]);
    } else {
      // 通常のレスポンス
      setIsWaitingForSelection(false);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.response
      }]);
    }
  };

  const handleSelection = (selection: number) => {
    // 選択完了後の処理
    setIsWaitingForSelection(false);
    setSelectionCandidates([]);
    setCurrentTaskId('');
    
    // 選択結果メッセージを追加
    setMessages(prev => [...prev, {
      role: 'user',
      content: `${selection}番を選択しました`
    }]);
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setIsLoading(true);

    // ユーザーメッセージを追加
    setMessages(prev => [...prev, {
      role: 'user',
      content: userMessage
    }]);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          message: userMessage,
          token: localStorage.getItem('token'),
          sseSessionId: `session_${Date.now()}`
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: ChatResponse = await response.json();
      handleChatResponse(result);

    } catch (error) {
      console.error('Chat request failed:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '申し訳ございません。エラーが発生しました。もう一度お試しください。'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-messages">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            <div className="message-content">
              {message.content}
            </div>
          </div>
        ))}
        
        {isWaitingForSelection && (
          <div className="selection-container">
            <SelectionOptions 
              candidates={selectionCandidates}
              onSelect={handleSelection}
              taskId={currentTaskId}
              isLoading={isLoading}
            />
          </div>
        )}
        
        {isLoading && !isWaitingForSelection && (
          <div className="loading-message">
            <div className="loading-spinner"></div>
            <p>処理中...</p>
          </div>
        )}
      </div>
      
      <div className="chat-input">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="メッセージを入力してください..."
          disabled={isLoading || isWaitingForSelection}
        />
        <button 
          onClick={sendMessage}
          disabled={isLoading || isWaitingForSelection || !inputMessage.trim()}
        >
          送信
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;
```

**修正の理由**: ユーザー選択機能を統合したチャットインターフェースを提供するため

**修正の影響**: 既存のチャット機能に影響なし

### 3. リアルタイム通信機能

#### 3.1 WebSocket接続管理
**修正する場所**: `frontend/services/websocket.ts`

**修正する内容**:
```typescript
class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect(token: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `ws://localhost:8000/ws?token=${token}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.attemptReconnect(token);
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  private attemptReconnect(token: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.connect(token);
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  private handleMessage(data: any) {
    // メッセージタイプに応じて処理を分岐
    switch (data.type) {
      case 'task_update':
        this.handleTaskUpdate(data);
        break;
      case 'selection_required':
        this.handleSelectionRequired(data);
        break;
      case 'selection_result':
        this.handleSelectionResult(data);
        break;
      default:
        console.log('Unknown message type:', data.type);
    }
  }

  private handleTaskUpdate(data: any) {
    // タスク更新の処理
    console.log('Task update:', data);
  }

  private handleSelectionRequired(data: any) {
    // 選択要求の処理
    console.log('Selection required:', data);
  }

  private handleSelectionResult(data: any) {
    // 選択結果の処理
    console.log('Selection result:', data);
  }

  sendSelection(taskId: string, selection: number) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'selection',
        task_id: taskId,
        selection: selection
      }));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const websocketService = new WebSocketService();
```

**修正の理由**: リアルタイム通信で選択結果を送信するため

**修正の影響**: 既存の通信機能に影響なし

### 4. 状態管理の拡張

#### 4.1 選択状態の管理
**修正する場所**: `frontend/hooks/useSelection.ts`

**修正する内容**:
```typescript
import { useState, useCallback } from 'react';
import { RecipeCandidate } from '../types/recipe';

interface SelectionState {
  isWaitingForSelection: boolean;
  candidates: RecipeCandidate[];
  taskId: string | null;
  isLoading: boolean;
}

export const useSelection = () => {
  const [selectionState, setSelectionState] = useState<SelectionState>({
    isWaitingForSelection: false,
    candidates: [],
    taskId: null,
    isLoading: false
  });

  const startSelection = useCallback((candidates: RecipeCandidate[], taskId: string) => {
    setSelectionState({
      isWaitingForSelection: true,
      candidates,
      taskId,
      isLoading: false
    });
  }, []);

  const submitSelection = useCallback(async (selection: number) => {
    if (!selectionState.taskId) return;

    setSelectionState(prev => ({ ...prev, isLoading: true }));

    try {
      const response = await fetch('/api/chat/selection', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          task_id: selectionState.taskId,
          selection: selection
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.success) {
        setSelectionState({
          isWaitingForSelection: false,
          candidates: [],
          taskId: null,
          isLoading: false
        });
        return result;
      } else {
        throw new Error(result.error || 'Selection failed');
      }
    } catch (error) {
      setSelectionState(prev => ({ ...prev, isLoading: false }));
      throw error;
    }
  }, [selectionState.taskId]);

  const cancelSelection = useCallback(() => {
    setSelectionState({
      isWaitingForSelection: false,
      candidates: [],
      taskId: null,
      isLoading: false
    });
  }, []);

  return {
    selectionState,
    startSelection,
    submitSelection,
    cancelSelection
  };
};
```

**修正の理由**: 選択状態を一元管理するため

**修正の影響**: 既存の状態管理に影響なし

### 5. 型定義の追加

#### 5.1 レシピ候補の型定義
**修正する場所**: `frontend/types/recipe.ts`

**修正する内容**:
```typescript
export interface RecipeCandidate {
  title: string;
  ingredients: string[];
  cooking_time?: string;
  description?: string;
  category?: 'main' | 'sub' | 'soup';
  source?: 'llm' | 'rag' | 'web';
}

export interface SelectionRequest {
  task_id: string;
  selection: number;
}

export interface SelectionResponse {
  success: boolean;
  message?: string;
  error?: string;
  next_step?: string;
}
```

**修正の理由**: 型安全性を確保するため

**修正の影響**: 既存の型定義に影響なし

## テスト計画

### 1. コンポーネントテスト

#### 1.1 選択肢表示コンポーネントテスト
**テストケース**: `SelectionOptions.test.tsx`
- 選択肢の表示
- 選択ボタンの動作
- ローディング状態の表示
- エラーハンドリング

#### 1.2 チャットインターフェーステスト
**テストケース**: `ChatInterface.test.tsx`
- 選択要求の表示
- 選択結果の送信
- 状態管理の確認

### 2. 統合テスト

#### 2.1 エンドツーエンドテスト
**テストケース**: `e2e/selection.test.ts`
- 5件提案 → ユーザー選択 → 結果受信の流れ
- エラーハンドリングの確認
- リアルタイム通信の確認

#### 2.2 ユーザー体験テスト
**テストケース**: `ux/selection.test.ts`
- UI/UXの使いやすさ
- レスポンス時間
- エラー時の動作

## 実装順序

1. **型定義の追加** → 型安全性の確保
2. **選択肢表示コンポーネント** → 基本UI
3. **チャットインターフェースの拡張** → 統合機能
4. **リアルタイム通信機能** → 通信機能
5. **状態管理の拡張** → 状態管理
6. **テスト実装** → 品質保証

## 期待される効果

- ユーザーが視覚的に選択肢を確認できる
- 選択操作が直感的で使いやすい
- リアルタイム通信でレスポンスが向上
- Phase 2Cでの統合テストが容易になる

## 制約事項

- 既存のチャット機能を破壊しない
- レスポンシブデザインに対応
- アクセシビリティを考慮
- ブラウザ互換性を維持

## 成功基準

- すべてのコンポーネントテストが成功
- エンドツーエンドテストが成功
- ユーザー体験テストが成功
- リアルタイム通信が正常に動作
- エラーハンドリングが適切に動作

## 次のステップ

Phase 2B完了後、Phase 2C（統合テストと品質保証）に進みます。
