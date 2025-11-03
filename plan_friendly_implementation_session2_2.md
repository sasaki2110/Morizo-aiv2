# ヘルプ機能テスト計画 - セッション2

## 概要

セッション2で実装した精度向上機能とフロントエンド変更のテスト計画です。

**テストの目標**: 精度向上、フロントエンド対応、統合テスト

---

## テスト項目（セッション2）

### バックエンド（精度向上の確認）

1. **ヘルプキーワードの検知（精度確認）**
   - 全ての検知対象キーワードで正しく検知されること
   - 誤検知パターンが正しく除外されること
   - エッジケースでの動作が適切であること

### フロントエンド

1. **プレースホルダーの表示**
   - 新しいプレースホルダーが正しく表示されること
   - 既存の機能に影響がないこと

### 統合テスト

1. **エンドツーエンドの動作確認**
   - 全てのシナリオが正常に動作すること
   - セッション状態が正しく管理されること
   - 通常のチャット機能に影響がないこと

---

## 自動テスト計画（セッション2）

### テストファイルの作成

**テストファイルの場所**: `/app/Morizo-aiv2/tests/makehelp/test_help_integration_session2.py`

**参考ファイル**: 
- `/app/Morizo-aiv2/tests/makehelp/test_help_integration_session1.py`（セッション1のテストを拡張）
- `/app/Morizo-aiv2/tests/test_bible_regression_check.py`（統合テストの構造を参考）

### テストファイルの構成

セッション1のテストファイルをベースに、以下の追加テストケースを含むテストファイルを作成します。

#### 追加テストケース

```python
# 誤検知防止テストケース
HELP_PRECISION_TEST_CASES = [
    HelpTestCase(
        name="TC-HELP-PREC-001: 検知対象キーワード「使い方を教えて」",
        description="「使い方を教えて」で正しく検知される",
        messages=["使い方を教えて"],
        expected_responses=[verify_help_overview_response],
        expected_help_states=["overview"]
    ),
    
    HelpTestCase(
        name="TC-HELP-PREC-002: 検知対象キーワード「使い方を知りたい」",
        description="「使い方を知りたい」で正しく検知される",
        messages=["使い方を知りたい"],
        expected_responses=[verify_help_overview_response],
        expected_help_states=["overview"]
    ),
    
    HelpTestCase(
        name="TC-HELP-PREC-003: 検知対象キーワード「使い方を説明して」",
        description="「使い方を説明して」で正しく検知される",
        messages=["使い方を説明して"],
        expected_responses=[verify_help_overview_response],
        expected_help_states=["overview"]
    ),
    
    HelpTestCase(
        name="TC-HELP-PREC-004: 検知対象キーワード「使い方を」",
        description="「使い方を」で正しく検知される",
        messages=["使い方を"],
        expected_responses=[verify_help_overview_response],
        expected_help_states=["overview"]
    ),
    
    HelpTestCase(
        name="TC-HELP-PREC-005: 検知対象キーワード「使い方は」",
        description="「使い方は」で正しく検知される",
        messages=["使い方は"],
        expected_responses=[verify_help_overview_response],
        expected_help_states=["overview"]
    ),
    
    HelpTestCase(
        name="TC-HELP-PREC-006: 検知対象キーワード「使い方について」",
        description="「使い方について」で正しく検知される",
        messages=["使い方について"],
        expected_responses=[verify_help_overview_response],
        expected_help_states=["overview"]
    ),
    
    HelpTestCase(
        name="TC-HELP-PREC-007: 検知対象キーワード「使い方って」",
        description="「使い方って」で正しく検知される",
        messages=["使い方って"],
        expected_responses=[verify_help_overview_response],
        expected_help_states=["overview"]
    ),
    
    HelpTestCase(
        name="TC-HELP-PREC-008: 検知対象キーワード「使い方 教えて」",
        description="「使い方 教えて」（スペース区切り）で正しく検知される",
        messages=["使い方 教えて"],
        expected_responses=[verify_help_overview_response],
        expected_help_states=["overview"]
    ),
    
    HelpTestCase(
        name="TC-HELP-PREC-009: 誤検知防止「在庫の使い方」",
        description="「在庫の使い方」では検知されず、通常の在庫操作として処理される",
        messages=["在庫の使い方を教えて"],
        expected_responses=[lambda r: "使い方" not in r or "在庫" in r and "使い方" not in r[:50]],  # ヘルプ応答ではない
        expected_help_states=[None]  # ヘルプモードに入らない
    ),
    
    HelpTestCase(
        name="TC-HELP-PREC-010: 誤検知防止「使い方」単独",
        description="「使い方」だけでは検知されない（誤検知防止）",
        messages=["使い方"],
        expected_responses=[lambda r: "4つの便利な機能" not in r],  # ヘルプ応答ではない
        expected_help_states=[None]  # ヘルプモードに入らない
    ),
    
    HelpTestCase(
        name="TC-HELP-PREC-011: 誤検知防止「使い方を確認」",
        description="「使い方を確認」では検知されない（誤検知防止）",
        messages=["使い方を確認"],
        expected_responses=[lambda r: "4つの便利な機能" not in r],  # ヘルプ応答ではない
        expected_help_states=[None]  # ヘルプモードに入らない
    ),
    
    HelpTestCase(
        name="TC-HELP-PREC-012: 検知対象キーワード「ヘルプ」",
        description="「ヘルプ」で正しく検知される",
        messages=["ヘルプ"],
        expected_responses=[verify_help_overview_response],
        expected_help_states=["overview"]
    ),
    
    HelpTestCase(
        name="TC-HELP-PREC-013: 検知対象キーワード「help」",
        description="「help」で正しく検知される",
        messages=["help"],
        expected_responses=[verify_help_overview_response],
        expected_help_states=["overview"]
    ),
    
    HelpTestCase(
        name="TC-HELP-PREC-014: 大文字小文字の区別「HELP」",
        description="「HELP」（大文字）でも正しく検知される",
        messages=["HELP"],
        expected_responses=[verify_help_overview_response],
        expected_help_states=["overview"]
    ),
    
    HelpTestCase(
        name="TC-HELP-PREC-015: エッジケース「無効な数字入力」",
        description="無効な数字（5以上、0、負の数）を入力した場合の動作",
        messages=["使い方を教えて", "5"],
        expected_responses=[verify_help_overview_response, lambda r: "4つの便利な機能" not in r],  # 詳細が表示されない
        expected_help_states=["overview", "overview"]  # 状態が変わらない
    ),
    
    HelpTestCase(
        name="TC-HELP-PREC-016: エッジケース「空白のみのメッセージ」",
        description="空白のみのメッセージの動作",
        messages=["使い方を教えて", "   "],
        expected_responses=[verify_help_overview_response, verify_help_overview_response],  # 空白は無視され、前の状態を維持
        expected_help_states=["overview", "overview"]
    ),
]

# エンドツーエンドシナリオテストケース
HELP_E2E_TEST_CASES = [
    HelpTestCase(
        name="TC-HELP-E2E-001: 初めてヘルプを使う",
        description="シナリオ1: 使い方を教えて → 1 → 在庫を教えて（通常復帰）",
        messages=["使い方を教えて", "1", "在庫を教えて"],
        expected_responses=[
            verify_help_overview_response,
            verify_inventory_detail_response,
            lambda r: "在庫" in r or "食材" in r  # 通常の在庫応答
        ],
        expected_help_states=["overview", "detail_1", None]  # 最後は通常モード
    ),
    
    HelpTestCase(
        name="TC-HELP-E2E-002: ヘルプから通常のチャットに復帰",
        description="シナリオ2: 使い方を教えて → 大根を１本追加して（直接復帰）",
        messages=["使い方を教えて", "大根を１本追加して"],
        expected_responses=[
            verify_help_overview_response,
            lambda r: "追加" in r or "大根" in r  # 通常の在庫追加応答
        ],
        expected_help_states=["overview", None]  # 復帰時にクリア
    ),
    
    HelpTestCase(
        name="TC-HELP-E2E-003: 複数の機能詳細を順番に見る",
        description="シナリオ3: 使い方を教えて → 1 → 2 → 3 → 4",
        messages=["使い方を教えて", "1", "2", "3", "4"],
        expected_responses=[
            verify_help_overview_response,
            verify_inventory_detail_response,
            verify_menu_bulk_detail_response,
            verify_menu_staged_detail_response,
            verify_auxiliary_detail_response
        ],
        expected_help_states=["overview", "detail_1", "detail_2", "detail_3", "detail_4"]
    ),
    
    HelpTestCase(
        name="TC-HELP-E2E-004: 誤検知防止の確認",
        description="シナリオ4: 在庫の使い方を教えて（通常処理）",
        messages=["在庫の使い方を教えて"],
        expected_responses=[lambda r: "4つの便利な機能" not in r],  # ヘルプ応答ではない
        expected_help_states=[None]  # ヘルプモードに入らない
    ),
]
```

#### テスト実行関数の拡張

セッション1のテスト実行関数をベースに、精度テストとE2Eテストを実行する関数を追加：

```python
async def run_precision_test(client: IntegrationTestClient, test_case: HelpTestCase) -> bool:
    """ヘルプキーワード精度テストケースを実行"""
    # セッション1のrun_help_testと同じロジックを使用
    return await run_help_test(client, test_case)


async def run_e2e_test(client: IntegrationTestClient, test_case: HelpTestCase) -> bool:
    """エンドツーエンドシナリオテストケースを実行"""
    # セッション1のrun_help_testと同じロジックを使用
    return await run_help_test(client, test_case)


async def main():
    """メイン関数（セッション1のベース + 精度テスト + E2Eテスト）"""
    print("🚀 ヘルプ機能統合テスト開始（セッション2）")
    print(f"📅 実行時刻: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # テストクライアントの初期化
    try:
        client = IntegrationTestClient()
    except Exception as e:
        print(f"❌ テストクライアントの初期化に失敗しました: {e}")
        return False
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python -m uvicorn api.main:app --reload でサーバーを起動してください。")
        return False
    
    print("✅ サーバー接続確認")
    
    # 全てのテストケースを統合
    all_test_cases = (
        HELP_TEST_CASES +  # セッション1のテストケース
        HELP_PRECISION_TEST_CASES +  # 精度テストケース
        HELP_E2E_TEST_CASES  # E2Eシナリオテストケース
    )
    
    # テストケースを実行
    passed = 0
    failed = 0
    
    for test_case in all_test_cases:
        result = await run_help_test(client, test_case)
        if result:
            passed += 1
        else:
            failed += 1
        
        # テスト間で少し待機
        await wait_for_response_delay(2.0)
    
    # 結果サマリー
    print(f"\n{'='*60}")
    print(f"📊 テスト結果サマリー")
    print(f"{'='*60}")
    print(f"✅ 成功: {passed}")
    print(f"❌ 失敗: {failed}")
    print(f"📊 合計: {passed + failed}")
    
    if failed == 0:
        print(f"\n🎉 全テストが成功しました！")
        return True
    else:
        print(f"\n⚠️ 一部のテストが失敗しました")
        return False
```

### フロントエンドテスト（手動確認項目）

**テストファイルの場所**: `/app/Morizo-aiv2/tests/makehelp/test_help_frontend_manual.md`（手動確認チェックリスト）

フロントエンドのプレースホルダー変更は手動確認が必要なため、チェックリスト形式で作成：

```markdown
# ヘルプ機能フロントエンド手動確認チェックリスト

## プレースホルダーの確認

- [ ] ChatInput.tsxの39行目のプレースホルダーが「メッセージを入力してください...または 使い方を教えて...」に変更されている
- [ ] プレースホルダーが正しく表示される（開発環境）
- [ ] プレースホルダーが正しく表示される（本番環境）
- [ ] 既存の機能に影響がない（チャット送信、ローディング表示等）

## 統合動作確認

- [ ] プレースホルダーを見て、ユーザーが「使い方を教えて」と入力できる
- [ ] ヘルプ機能が正常に動作する（バックエンドとの連携）
- [ ] 通常のチャット機能に影響がない
```

### テスト実行方法

```bash
# セッション2のテスト実行（サーバーが起動していることを確認）
cd /app/Morizo-aiv2
python tests/makehelp/test_help_integration_session2.py
```

### テストファイル作成の注意事項

1. **セッション1のテストとの統合**: セッション1のテストケースも含めて実行し、回帰テストとしても機能させます。

2. **誤検知防止テスト**: 誤検知を防ぐテストケースを充実させ、実際に誤検知が発生しないことを確認します。

3. **エッジケースのテスト**: 無効な入力、空白のみのメッセージなど、エッジケースの動作を確認します。

4. **E2Eシナリオテスト**: 実際のユーザー体験に近いシナリオでテストを実行し、エンドツーエンドでの動作を確認します。

5. **フロントエンドテスト**: フロントエンドの変更は手動確認が必要なため、チェックリスト形式で管理します。

