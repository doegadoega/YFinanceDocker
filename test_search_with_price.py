#!/usr/bin/env python3
"""
検索機能（株価情報付き）のテストスクリプト
"""

import requests
import json
from datetime import datetime

# API GatewayのURL（実際のURLに変更してください）
API_BASE_URL = "https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod/"

def test_search_with_price():
    """株価情報付き検索機能をテスト"""
    
    print("=== YFinance API 検索機能テスト（株価情報付き）===")
    print(f"API URL: {API_BASE_URL}")
    print(f"テスト時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # テストケース
    test_cases = [
        {
            "name": "Apple検索（米国）",
            "params": {"q": "apple", "limit": 5, "region": "US"}
        },
        {
            "name": "Microsoft検索（米国）",
            "params": {"q": "microsoft", "limit": 3, "region": "US"}
        },
        {
            "name": "トヨタ検索（日本）",
            "params": {"q": "トヨタ", "limit": 5, "region": "JP"}
        },
        {
            "name": "Sony検索（日本）",
            "params": {"q": "sony", "limit": 3, "region": "JP"}
        },
        {
            "name": "Tesla検索（米国）",
            "params": {"q": "tesla", "limit": 10, "region": "US"}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"--- テスト {i}: {test_case['name']} ---")
        
        try:
            # APIリクエスト
            response = requests.get(f"{API_BASE_URL}/search", params=test_case['params'])
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ 成功")
                print(f"検索クエリ: {data.get('query', 'N/A')}")
                print(f"リージョン: {data.get('region', 'N/A')}")
                print(f"結果件数: {data.get('count', 0)}/{data.get('max_results', 10)}")
                print(f"取得時刻: {data.get('timestamp', 'N/A')}")
                print()
                
                # 結果の詳細表示
                results = data.get('results', [])
                for j, result in enumerate(results, 1):
                    print(f"  {j}. {result.get('symbol', 'N/A')} - {result.get('name', 'N/A')}")
                    
                    # 株価情報の表示
                    if 'current_price' in result:
                        price = result['current_price']
                        currency = result.get('currency', 'USD')
                        print(f"     株価: {price} {currency}")
                        
                        if 'price_change' in result:
                            change = result['price_change']
                            change_percent = result['price_change_percent']
                            direction = result['price_change_direction']
                            
                            direction_symbol = "📈" if direction == "up" else "📉" if direction == "down" else "➡️"
                            print(f"     変化: {direction_symbol} {change:+.2f} ({change_percent:+.2f}%)")
                        
                        if 'market_cap' in result and result['market_cap']:
                            market_cap = result['market_cap']
                            if market_cap > 1e12:
                                market_cap_str = f"{market_cap/1e12:.2f}T"
                            elif market_cap > 1e9:
                                market_cap_str = f"{market_cap/1e9:.2f}B"
                            elif market_cap > 1e6:
                                market_cap_str = f"{market_cap/1e6:.2f}M"
                            else:
                                market_cap_str = f"{market_cap:,.0f}"
                            print(f"     時価総額: {market_cap_str} {currency}")
                    
                    elif 'price_error' in result:
                        print(f"     ❌ 株価取得エラー: {result['price_error']}")
                    
                    print(f"     取引所: {result.get('exchange', 'N/A')}")
                    print(f"     スコア: {result.get('score', 'N/A')}")
                    print()
                
            else:
                print(f"❌ エラー: HTTP {response.status_code}")
                print(f"レスポンス: {response.text}")
                
        except Exception as e:
            print(f"❌ 例外エラー: {str(e)}")
        
        print("-" * 50)
        print()

def test_single_search():
    """単一検索の詳細テスト"""
    print("=== 単一検索詳細テスト ===")
    
    # Appleの詳細検索
    params = {"q": "apple", "limit": 10, "region": "US"}
    
    try:
        response = requests.get(f"{API_BASE_URL}/search", params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # JSONを整形して表示
            print("レスポンス（JSON形式）:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
        else:
            print(f"エラー: HTTP {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"例外エラー: {str(e)}")

if __name__ == "__main__":
    # 基本テスト
    test_search_with_price()
    
    # 詳細テスト（コメントアウトを外して実行）
    # test_single_search() 