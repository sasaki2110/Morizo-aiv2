#!/usr/bin/env python3
"""
RAG検索テストスクリプト
ベクトルDBの状態確認と検索精度テスト
"""

import os
import sys
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_vector_db():
    """ベクトルDBの状態を確認"""
    try:
        from mcp_servers.recipe_rag.client import RecipeRAGClient
        
        print("=== ベクトルDB状態確認 ===")
        client = RecipeRAGClient()
        vectorstore = client._get_vectorstore()
        
        # ベクトルDBの件数を確認
        db_data = vectorstore.get()
        print(f"ベクトルDBの件数: {len(db_data['ids'])}")
        
        # 最初の5件のタイトルを表示
        print("\n最初の5件のレシピ:")
        for i in range(min(5, len(db_data['ids']))):
            metadata = db_data['metadatas'][i]
            print(f"{i+1}. {metadata.get('title', 'Unknown')}")
        
        return vectorstore
        
    except Exception as e:
        print(f"エラー: {e}")
        return None

def test_search(vectorstore, query, description):
    """検索テストを実行"""
    if not vectorstore:
        print("ベクトルストアが利用できません")
        return
    
    try:
        print(f"\n=== {description} ===")
        print(f"検索クエリ: '{query}'")
        
        results = vectorstore.similarity_search(query, k=5)
        
        print(f"検索結果: {len(results)}件")
        for i, result in enumerate(results):
            title = result.metadata.get("title", "Unknown")
            print(f"{i+1}. {title}")
            
    except Exception as e:
        print(f"検索エラー: {e}")

def main():
    """メイン処理"""
    print("RAG検索テスト開始")
    print("=" * 50)
    
    # 環境変数読み込み
    load_dotenv()
    
    # ベクトルDB状態確認
    vectorstore = test_vector_db()
    
    if not vectorstore:
        print("ベクトルDBの読み込みに失敗しました")
        return
    
    # 単一食材検索テスト実行
    single_ingredient_test_cases = [
        ("牛乳", "牛乳検索テスト"),
        ("卵", "卵検索テスト"),
        ("豆腐", "豆腐検索テスト"),
        ("さつまいも", "さつまいも検索テスト"),
        ("れんこん", "れんこん検索テスト"),
        ("かつお", "かつお検索テスト"),
        ("ごま", "ごま検索テスト"),
        ("チョコレート", "チョコレート検索テスト")
    ]
    
    print("\n=== 単一食材検索テスト ===")
    for query, description in single_ingredient_test_cases:
        test_search(vectorstore, query, description)
    
    # 複数食材検索テスト実行
    multi_ingredient_test_cases = [
        ("鶏もも肉 もやし パン 牛乳 豚バラブロック ほうれん草 牛すね肉 人参 ほうれん草 玉ねぎ ジャガイモ キャベツ ピーマン", "在庫食材全体検索テスト"),
        ("鶏もも肉 玉ねぎ 人参", "鶏肉野菜検索テスト"),
        ("牛乳 卵 小麦粉", "乳製品・卵・穀物検索テスト"),
        ("豚バラブロック キャベツ 塩 胡椒", "豚肉野菜検索テスト"),
        ("ほうれん草 玉ねぎ ジャガイモ", "野菜検索テスト"),
        ("キャベツ ピーマン 人参", "野菜ミックス検索テスト")
    ]
    
    print("\n=== 複数食材検索テスト ===")
    for query, description in multi_ingredient_test_cases:
        test_search(vectorstore, query, description)
    
    print("\n" + "=" * 50)
    print("RAG検索テスト完了")

if __name__ == "__main__":
    main()
