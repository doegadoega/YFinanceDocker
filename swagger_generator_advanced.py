#!/usr/bin/env python3
"""
高度なSwagger自動生成ツール
Lambda関数のコードから自動的にSwagger仕様書を生成

以下の場合に有用：
1. 動的なAPI開発: エンドポイントが頻繁に変更される
2. コードファースト: 設定よりもコードを重視
3. 自動化: 完全自動化を目指す場合
"""

import json
import re
import ast
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

class SwaggerGenerator:
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.endpoints = {}
        
    def parse_lambda_function(self, lambda_file: str):
        """Lambda関数ファイルを解析してエンドポイントを抽出"""
        try:
            with open(lambda_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # リソースパスのパターンを検索
            resource_patterns = [
                r"elif '/price' in resource:",
                r"elif '/info' in resource:",
                r"elif '/history' in resource:",
                r"elif '/news' in resource:",
                r"elif '/dividends' in resource:",
                r"elif '/options' in resource:",
                r"elif '/financials' in resource:",
                r"elif '/analysts' in resource:",
                r"if '/search' in resource:"
            ]
            
            # 関数呼び出しパターンを検索
            function_patterns = [
                r"get_stock_price_api\(ticker\)",
                r"get_stock_info_api\(ticker\)",
                r"get_stock_history_api\(ticker, period\)",
                r"get_stock_news_api\(ticker\)",
                r"get_stock_dividends_api\(ticker\)",
                r"get_stock_options_api\(ticker\)",
                r"get_stock_financials_api\(ticker\)",
                r"get_stock_analysts_api\(ticker\)",
                r"search_stocks_api\(query, query_parameters\)"
            ]
            
            # エンドポイント定義
            endpoint_definitions = {
                "/price": {
                    "function": "get_stock_price_api",
                    "summary": "株価取得",
                    "description": "指定されたティッカーシンボルの現在の株価を取得します",
                    "parameters": ["ticker"],
                    "optional_params": []
                },
                "/info": {
                    "function": "get_stock_info_api",
                    "summary": "詳細情報取得",
                    "description": "指定されたティッカーシンボルの詳細な企業情報を取得します",
                    "parameters": ["ticker"],
                    "optional_params": []
                },
                "/history": {
                    "function": "get_stock_history_api",
                    "summary": "株価履歴取得",
                    "description": "指定されたティッカーシンボルの株価履歴データを取得します",
                    "parameters": ["ticker"],
                    "optional_params": ["period"]
                },
                "/news": {
                    "function": "get_stock_news_api",
                    "summary": "ニュース取得",
                    "description": "指定されたティッカーシンボルに関連する最新ニュースを取得します",
                    "parameters": ["ticker"],
                    "optional_params": []
                },
                "/dividends": {
                    "function": "get_stock_dividends_api",
                    "summary": "配当情報取得",
                    "description": "指定されたティッカーシンボルの配当情報を取得します",
                    "parameters": ["ticker"],
                    "optional_params": []
                },
                "/options": {
                    "function": "get_stock_options_api",
                    "summary": "オプション情報取得",
                    "description": "指定されたティッカーシンボルのオプション情報を取得します",
                    "parameters": ["ticker"],
                    "optional_params": []
                },
                "/financials": {
                    "function": "get_stock_financials_api",
                    "summary": "財務情報取得",
                    "description": "指定されたティッカーシンボルの財務情報を取得します",
                    "parameters": ["ticker"],
                    "optional_params": []
                },
                "/analysts": {
                    "function": "get_stock_analysts_api",
                    "summary": "アナリスト予想取得",
                    "description": "指定されたティッカーシンボルのアナリスト予想情報を取得します",
                    "parameters": ["ticker"],
                    "optional_params": []
                },
                "/search": {
                    "function": "search_stocks_api",
                    "summary": "銘柄検索",
                    "description": "キーワードによる銘柄検索を実行します",
                    "parameters": ["q"],
                    "optional_params": ["limit", "region"]
                }
            }
            
            # 各エンドポイントの存在を確認
            for path, definition in endpoint_definitions.items():
                if any(pattern in content for pattern in resource_patterns if path in pattern):
                    self.endpoints[path] = definition
                    
        except Exception as e:
            print(f"Lambda関数の解析エラー: {e}")
    
    def generate_swagger(self) -> Dict[str, Any]:
        """Swagger仕様書を生成"""
        swagger = {
            "openapi": "3.0.0",
            "info": {
                "title": "YFinance API",
                "description": "YFinanceを使用した株式データ取得API",
                "version": "1.0.0",
                "contact": {
                    "name": "YFinance API Support"
                }
            },
            "servers": [
                {
                    "url": self.api_url,
                    "description": "Production server"
                }
            ],
            "paths": {},
            "components": {
                "schemas": {
                    "Error": {
                        "type": "object",
                        "properties": {
                            "error": {
                                "type": "string",
                                "example": "エラーメッセージ"
                            },
                            "status": {
                                "type": "string",
                                "example": "error"
                            },
                            "timestamp": {
                                "type": "string",
                                "format": "date-time",
                                "example": datetime.now().isoformat() + "Z"
                            }
                        }
                    }
                }
            }
        }
        
        # レスポンススキーマ定義
        response_schemas = {
            "/price": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "example": "AAPL"},
                    "price": {"type": "number", "example": 208.62},
                    "currency": {"type": "string", "example": "USD"},
                    "timestamp": {"type": "string", "format": "date-time"}
                }
            },
            "/info": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "example": "AAPL"},
                    "name": {"type": "string", "example": "Apple Inc."},
                    "currentPrice": {"type": "number", "example": 208.62},
                    "previousClose": {"type": "number", "example": 211.16},
                    "marketCap": {"type": "number", "example": 3115906498560},
                    "dividendYield": {"type": "number", "example": 0.51},
                    "trailingPE": {"type": "number", "example": 32.44}
                }
            },
            "/history": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "example": "AAPL"},
                    "period": {"type": "string", "example": "1mo"},
                    "data": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "Open": {"type": "number", "example": 209.93},
                                "High": {"type": "number", "example": 210.91},
                                "Low": {"type": "number", "example": 207.54},
                                "Close": {"type": "number", "example": 208.62},
                                "Volume": {"type": "number", "example": 38711400}
                            }
                        }
                    }
                }
            },
            "/search": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "example": "apple"},
                    "region": {"type": "string", "example": "US"},
                    "count": {"type": "integer", "example": 7},
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "symbol": {"type": "string", "example": "AAPL"},
                                "name": {"type": "string", "example": "Apple Inc."},
                                "exchange": {"type": "string", "example": "NMS"},
                                "type": {"type": "string", "example": "Equity"},
                                "score": {"type": "number", "example": 31292.0}
                            }
                        }
                    }
                }
            }
        }
        
        # 各エンドポイントのSwagger定義を生成
        for path, definition in self.endpoints.items():
            parameters = []
            
            # 必須パラメータ
            for param in definition["parameters"]:
                param_def = {
                    "name": param,
                    "in": "query",
                    "required": True,
                    "schema": {"type": "string"}
                }
                
                if param == "ticker":
                    param_def["description"] = "ティッカーシンボル（例: AAPL, MSFT, 7203.T）"
                elif param == "q":
                    param_def["description"] = "検索キーワード（例: apple, microsoft）"
                
                parameters.append(param_def)
            
            # オプションパラメータ
            for param in definition["optional_params"]:
                param_def = {
                    "name": param,
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"}
                }
                
                if param == "period":
                    param_def["description"] = "期間（デフォルト: 1mo）"
                    param_def["schema"] = {
                        "type": "string",
                        "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
                        "default": "1mo"
                    }
                elif param == "limit":
                    param_def["description"] = "検索結果件数（デフォルト: 10）"
                    param_def["schema"] = {"type": "integer", "default": 10}
                elif param == "region":
                    param_def["description"] = "検索リージョン（デフォルト: US）"
                    param_def["schema"] = {"type": "string", "enum": ["US", "JP"], "default": "US"}
                
                parameters.append(param_def)
            
            # エンドポイント定義
            endpoint = {
                "summary": definition["summary"],
                "description": definition["description"],
                "parameters": parameters,
                "responses": {
                    "200": {
                        "description": "成功",
                        "content": {
                            "application/json": {
                                "schema": response_schemas.get(path, {"type": "object"})
                            }
                        }
                    },
                    "400": {
                        "description": "バッドリクエスト",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        }
                    }
                }
            }
            
            swagger["paths"][path] = {"get": endpoint}
        
        return swagger

def main():
    """メイン関数"""
    if len(sys.argv) < 3:
        print("使用方法: python swagger_generator_advanced.py <lambda_function.py> <api_url>")
        print("例: python swagger_generator_advanced.py lambda_function.py https://api.example.com/prod/")
        sys.exit(1)
    
    lambda_file = sys.argv[1]
    api_url = sys.argv[2]
    
    if not os.path.exists(lambda_file):
        print(f"エラー: Lambda関数ファイル {lambda_file} が見つかりません")
        sys.exit(1)
    
    try:
        # Swagger生成器を初期化
        generator = SwaggerGenerator(api_url)
        
        # Lambda関数を解析
        generator.parse_lambda_function(lambda_file)
        
        # Swagger仕様書を生成
        swagger = generator.generate_swagger()
        
        # ファイルに保存
        output_file = "swagger_auto.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(swagger, f, indent=2, ensure_ascii=False)
        
        print(f"自動生成されたSwagger仕様書を {output_file} に保存しました")
        print(f"検出されたエンドポイント数: {len(generator.endpoints)}")
        print(f"エンドポイント: {list(generator.endpoints.keys())}")
        
        # # コンソールにも表示
        # print("\n=== 自動生成されたSwagger仕様書 ===")
        # print(json.dumps(swagger, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 