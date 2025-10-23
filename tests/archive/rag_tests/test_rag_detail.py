#!/usr/bin/env python3
"""
RAG検索詳細テストスクリプト
埋め込みベクトルと検索アルゴリズムの詳細分析
"""

import os
import sys
import numpy as np
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def cosine_similarity(a, b):
    """コサイン類似度を計算"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def test_embedding_vectors():
    """埋め込みベクトルの確認テスト"""
    try:
        from mcp_servers.recipe_rag.client import RecipeRAGClient
        
        print("=== 埋め込みベクトルの確認テスト ===")
        client = RecipeRAGClient()
        embeddings = client.embeddings
        
        # テスト用のテキスト
        test_texts = [
            "さつまいも",
            "さつまいも ごま 栗粉 れんこん",
            "さつまいも 卵黄 生クリーム",
            "さつまいも ツナ缶",
            "さつまいも 黒ごま 水"
        ]
        
        print("テキストとベクトルの確認:")
        vectors = {}
        for text in test_texts:
            vector = embeddings.embed_query(text)
            vectors[text] = vector
            print(f"テキスト: {text}")
            print(f"ベクトル次元: {len(vector)}")
            print(f"ベクトル最初の5要素: {vector[:5]}")
            print()
        
        # 類似度計算
        print("類似度計算:")
        base_text = "さつまいも"
        base_vector = vectors[base_text]
        
        for text, vector in vectors.items():
            if text != base_text:
                similarity = cosine_similarity(base_vector, vector)
                print(f"「{base_text}」と「{text}」の類似度: {similarity:.4f}")
        
        return vectors
        
    except Exception as e:
        print(f"埋め込みベクトルテストエラー: {e}")
        return None

def test_similarity_comparison():
    """類似度比較テスト（検索結果の妥当性確認）"""
    try:
        from mcp_servers.recipe_rag.client import RecipeRAGClient
        
        print("\n=== 類似度比較テスト ===")
        client = RecipeRAGClient()
        embeddings = client.embeddings
        
        # 検索クエリ
        query = "さつまいも"
        query_vector = embeddings.embed_query(query)
        
        # 検索結果のベクトル化対象テキスト
        search_result_texts = [
            "鶏皮余ったもの 七味唐辛子お",
            "長芋 キッチンペーパー"
        ]
        
        # SQLiteで確認した「さつまいも」を含むベクトル化対象テキスト
        sqlite_result_texts = [
            "さつまいも 黒ゴマ 水あめ 水",
            "さつまいも ツナ缶 レーズン",
            "さつまいも 黒ゴマ 蜂蜜",
            "さつまいも ごま 栗粉 れんこん",
            "さつまいも 卵黄 生クリーム"
        ]
        
        # 問題のある「さつまいも」データ
        problematic_texts = [
            "卵黄 ( 牛乳〜 ) さつまいも中",
            "バニラエッセンス さつまいも− 牛乳 卵",
            "さつまいも中"
        ]
        
        print(f"検索クエリ「{query}」との類似度比較:")
        print()
        
        # 検索結果のベクトル化対象テキストとの類似度
        print("1. 検索結果のベクトル化対象テキストとの類似度:")
        for text in search_result_texts:
            vector = embeddings.embed_query(text)
            similarity = cosine_similarity(query_vector, vector)
            print(f"   「{query}」と「{text}」の類似度: {similarity:.4f}")
        print()
        
        # SQLiteで確認した「さつまいも」を含むテキストとの類似度
        print("2. SQLiteで確認した「さつまいも」を含むテキストとの類似度:")
        for text in sqlite_result_texts:
            vector = embeddings.embed_query(text)
            similarity = cosine_similarity(query_vector, vector)
            print(f"   「{query}」と「{text}」の類似度: {similarity:.4f}")
        print()
        
        # 問題のある「さつまいも」データとの類似度
        print("3. 問題のある「さつまいも」データとの類似度:")
        for text in problematic_texts:
            vector = embeddings.embed_query(text)
            similarity = cosine_similarity(query_vector, vector)
            print(f"   「{query}」と「{text}」の類似度: {similarity:.4f}")
        print()
        
        # 類似度の比較分析
        print("4. 類似度の比較分析:")
        all_texts = search_result_texts + sqlite_result_texts + problematic_texts
        similarities = []
        
        for text in all_texts:
            vector = embeddings.embed_query(text)
            similarity = cosine_similarity(query_vector, vector)
            similarities.append((text, similarity))
        
        # 類似度でソート
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        print("   類似度順（高い順）:")
        for i, (text, similarity) in enumerate(similarities):
            print(f"   {i+1:2d}. {similarity:.4f} - {text}")
        
        return similarities
        
    except Exception as e:
        print(f"類似度比較テストエラー: {e}")
        return None

def test_search_algorithm(vectorstore, query="さつまいも"):
    """検索アルゴリズムの詳細確認"""
    if not vectorstore:
        print("ベクトルストアが利用できません")
        return
    
    try:
        print(f"\n=== 検索アルゴリズムの詳細確認 ===")
        print(f"検索クエリ: '{query}'")
        
        # 1. 通常の検索
        print("\n1. 通常の検索結果:")
        results = vectorstore.similarity_search(query, k=5)
        for i, result in enumerate(results):
            title = result.metadata.get("title", "Unknown")
            content = result.page_content
            print(f"{i+1}. タイトル: {title}")
            print(f"   内容: {content}")
            print()
        
        # 2. スコア付き検索
        print("2. スコア付き検索結果:")
        try:
            results_with_score = vectorstore.similarity_search_with_score(query, k=20)
            for i, (result, score) in enumerate(results_with_score):
                title = result.metadata.get("title", "Unknown")
                content = result.page_content
                print(f"{i+1}. スコア: {score:.4f}")
                print(f"   タイトル: {title}")
                print(f"   内容: {content}")
                print()
        except Exception as e:
            print(f"スコア付き検索エラー: {e}")
        
        # 3. 低い閾値での検索
        print("3. 低い閾値での検索結果:")
        try:
            results_low_threshold = vectorstore.similarity_search(query, k=20, score_threshold=0.0)
            for i, result in enumerate(results_low_threshold):
                title = result.metadata.get("title", "Unknown")
                content = result.page_content
                print(f"{i+1}. タイトル: {title}")
                print(f"   内容: {content}")
                print()
        except Exception as e:
            print(f"低い閾値検索エラー: {e}")
        
        # 4. 文字列マッチングでのフィルタリング
        print("4. 文字列マッチングでのフィルタリング:")
        try:
            all_results = vectorstore.similarity_search(query, k=50)
            filtered_results = [r for r in all_results if query in r.page_content]
            print(f"全検索結果: {len(all_results)}件")
            print(f"フィルタリング後: {len(filtered_results)}件")
            
            for i, result in enumerate(filtered_results[:10]):
                title = result.metadata.get("title", "Unknown")
                content = result.page_content
                print(f"{i+1}. タイトル: {title}")
                print(f"   内容: {content}")
                print()
        except Exception as e:
            print(f"文字列マッチングフィルタリングエラー: {e}")
            
    except Exception as e:
        print(f"検索アルゴリズムテストエラー: {e}")

def test_vector_db_content():
    """ベクトルDBの内容確認"""
    try:
        print("\n=== ベクトルDBの内容確認 ===")
        
        # SQLiteで直接確認
        import sqlite3
        conn = sqlite3.connect('recipe_vector_db/chroma.sqlite3')
        cursor = conn.cursor()
        
        # さつまいもを含むレシピを確認
        cursor.execute("""
        SELECT em1.string_value as title, em2.string_value as ingredients 
        FROM embedding_metadata em1 
        JOIN embedding_metadata em2 ON em1.id = em2.id 
        WHERE em1.key = 'title' AND em2.key = 'chroma:document' 
        AND em2.string_value LIKE '%さつまいも%'
        LIMIT 10
        """)
        
        print("SQLiteで確認した「さつまいも」を含むレシピ:")
        for row in cursor.fetchall():
            print(f"  タイトル: {row[0]}")
            print(f"  食材: {row[1]}")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"ベクトルDB内容確認エラー: {e}")

def test_chromadb_content():
    """ChromaDBの内容確認"""
    try:
        print("\n=== ChromaDBの内容確認 ===")
        
        from mcp_servers.recipe_rag.client import RecipeRAGClient
        client = RecipeRAGClient()
        vectorstore = client._get_vectorstore()
        
        # ベクトルDBの全データを取得
        db_data = vectorstore.get()
        
        print(f"ベクトルDBの総レコード数: {len(db_data['documents'])}")
        
        # 「さつまいも」を含むレシピを検索
        sweet_potato_recipes = []
        for i, doc in enumerate(db_data['documents']):
            if 'さつまいも' in doc:
                title = db_data['metadatas'][i].get('title', 'Unknown')
                sweet_potato_recipes.append((title, doc))
        
        print(f"「さつまいも」を含むレシピ: {len(sweet_potato_recipes)}件")
        for i, (title, ingredients) in enumerate(sweet_potato_recipes[:10]):
            print(f"  {i+1}. タイトル: {title}")
            print(f"     食材: {ingredients}")
            print()
        
        # 検索クエリのテスト
        print("=== 検索クエリのテスト ===")
        
        # 1. 単純な「さつまいも」検索
        print("1. 単純な「さつまいも」検索:")
        results = vectorstore.similarity_search("さつまいも", k=5)
        print(f"   検索結果数: {len(results)}")
        for i, result in enumerate(results):
            title = result.metadata.get("title", "Unknown")
            content = result.page_content
            print(f"   {i+1}. タイトル: {title}")
            print(f"      内容: {content}")
            print()
        
        # 2. 「さつまいも 和食」検索
        print("2. 「さつまいも 和食」検索:")
        results = vectorstore.similarity_search("さつまいも 和食", k=5)
        print(f"   検索結果数: {len(results)}")
        for i, result in enumerate(results):
            title = result.metadata.get("title", "Unknown")
            content = result.page_content
            print(f"   {i+1}. タイトル: {title}")
            print(f"      内容: {content}")
            print()
        
        # 3. スコア付き検索
        print("3. スコア付き「さつまいも」検索:")
        try:
            results_with_score = vectorstore.similarity_search_with_score("さつまいも", k=5)
            print(f"   スコア付き検索結果数: {len(results_with_score)}")
            for i, (result, score) in enumerate(results_with_score):
                title = result.metadata.get("title", "Unknown")
                content = result.page_content
                print(f"   {i+1}. スコア: {score:.4f}")
                print(f"      タイトル: {title}")
                print(f"      内容: {content}")
                print()
        except Exception as e:
            print(f"   スコア付き検索エラー: {e}")
        
    except Exception as e:
        print(f"ChromaDB内容確認エラー: {e}")

def main():
    """メイン処理"""
    print("RAG検索詳細テスト開始")
    print("=" * 60)
    
    # 環境変数読み込み
    load_dotenv()
    
    # 1. 埋め込みベクトルの確認
    vectors = test_embedding_vectors()
    
    # 2. 類似度比較テスト（新規追加）
    similarities = test_similarity_comparison()
    
    # 3. ベクトルDBの内容確認
    test_vector_db_content()
    
    # 4. ChromaDBの内容確認
    test_chromadb_content()
    
    # 5. 検索アルゴリズムの確認
    try:
        from mcp_servers.recipe_rag.client import RecipeRAGClient
        client = RecipeRAGClient()
        vectorstore = client._get_vectorstore()
        test_search_algorithm(vectorstore)
    except Exception as e:
        print(f"検索アルゴリズムテストエラー: {e}")
    
    print("\n" + "=" * 60)
    print("RAG検索詳細テスト完了")

if __name__ == "__main__":
    main()
