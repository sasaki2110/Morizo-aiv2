#!/usr/bin/env python3
"""
OCRService - レシートOCRサービス

レシート画像を解析して在庫情報を抽出するサービス
"""

import os
import base64
import json
import re
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv
from config.loggers import GenericLogger

load_dotenv()


class OCRService:
    """レシートOCRサービス"""
    
    def __init__(self):
        """初期化"""
        self.logger = GenericLogger("service", "ocr")
        self.ocr_model = os.getenv("OPENAI_OCR_MODEL", "gpt-4o")
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEYが設定されていません")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.logger.info(f"✅ [OCR] OCRService initialized with model: {self.ocr_model}")
    
    async def analyze_receipt_image(
        self,
        image_bytes: bytes
    ) -> Dict[str, Any]:
        """レシート画像を解析して在庫情報を抽出"""
        try:
            self.logger.info("🔍 [OCR] Starting receipt image analysis")
            
            # 画像をbase64エンコード
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            # OpenAI Vision APIで解析
            try:
                response = await self.client.chat.completions.create(
                    model=self.ocr_model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """このレシート画像から、在庫管理に必要な情報を抽出してください。

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

日本語のレシートを正確に解析してください。商品名は正確に、数量と単位も正しく抽出してください。"""
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=2000,
                    temperature=0.3
                )
            except Exception as api_error:
                # OpenAI APIのエラーを適切に処理
                error_message = str(api_error)
                if "image_parse_error" in error_message or "unsupported image" in error_message.lower():
                    self.logger.error(f"❌ [OCR] 画像解析エラー（画像形式が不正）: {error_message}")
                    return {
                        "success": False,
                        "error": "画像ファイルが正しく解析できませんでした。有効なJPEGまたはPNG画像をアップロードしてください。",
                        "items": []
                    }
                elif "invalid_request_error" in error_message:
                    self.logger.error(f"❌ [OCR] リクエストエラー: {error_message}")
                    return {
                        "success": False,
                        "error": "OCR解析リクエストが無効です。画像ファイルを確認してください。",
                        "items": []
                    }
                else:
                    self.logger.error(f"❌ [OCR] OpenAI APIエラー: {error_message}")
                    return {
                        "success": False,
                        "error": f"OCR解析中にエラーが発生しました: {error_message}",
                        "items": []
                    }
            
            content = response.choices[0].message.content
            self.logger.info(f"✅ [OCR] OCR analysis completed: {len(content)} characters")
            
            # JSONを抽出（Markdownコードブロックから）
            # JSONコードブロックを抽出
            json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # コードブロックがない場合、直接JSONとして解析を試みる
                json_str = content.strip()
            
            # JSON解析
            items = json.loads(json_str)
            
            if not isinstance(items, list):
                raise ValueError("OCR結果が配列形式ではありません")
            
            self.logger.info(f"✅ [OCR] Extracted {len(items)} items from receipt")
            
            return {
                "success": True,
                "items": items,
                "raw_response": content
            }
            
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ [OCR] JSON解析エラー: {e}")
            self.logger.error(f"   レスポンス内容: {content[:500]}")
            return {
                "success": False,
                "error": f"JSON解析エラー: {str(e)}",
                "items": []
            }
        except Exception as e:
            self.logger.error(f"❌ [OCR] OCR解析エラー: {e}")
            return {
                "success": False,
                "error": str(e),
                "items": []
            }
    
    async def extract_inventory_items(
        self,
        image_bytes: bytes
    ) -> List[Dict[str, Any]]:
        """レシート画像から在庫アイテムのリストを抽出"""
        result = await self.analyze_receipt_image(image_bytes)
        
        if result.get("success"):
            return result.get("items", [])
        else:
            raise Exception(result.get("error", "OCR解析に失敗しました"))

