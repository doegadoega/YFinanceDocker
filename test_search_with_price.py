#!/usr/bin/env python3
"""
検索機能（株価情報付き）のテストスクリプト - 新API対応版
新しいAPIエンドポイントをテストし、包括的な機能を検証
"""

import requests
import json
from datetime import datetime
import time

# 新API GatewayのURL
API_BASE_URL = "https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod"

def test_search_api():
    """新しい検索APIをテスト"""
    
    print("=== YFinance API 検索機能テスト（新API対応版）===")
    print(f"API URL: {API_BASE_URL}")
    print(f"テスト時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # テストケース
    test_cases = [
        {
            "name": "Apple検索（米国）",
            "params": {"q": "Apple", "region": "US"}
        },
        {
            "name": "Microsoft検索（米国）",
            "params": {"q": "Microsoft", "region": "US"}
        },
        {
            "name": "Tesla検索（米国）",
            "params": {"q": "Tesla", "region": "US"}
        },
        {
            "name": "トヨタ検索（日本）",
            "params": {"q": "Toyota", "region": "JP"}
        },
        {
            "name": "ソニー検索（日本）",
            "params": {"q": "Sony", "region": "JP"}
        },
        {
            "name": "SAP検索（ドイツ）",
            "params": {"q": "SAP", "region": "DE"}
        },
        {
            "name": "ティッカー検索（AAPL）",
            "params": {"q": "AAPL", "region": "US"}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"--- テスト {i}: {test_case['name']} ---")
        
        try:
            start_time = time.time()
            # 新APIリクエスト
            response = requests.get(f"{API_BASE_URL}/search", params=test_case['params'], timeout=30)
            response_time = time.time() - start_time
            
            print(f"レスポンス時間: {response_time:.2f}秒")
            print(f"ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功")
                print(f"検索クエリ: {data.get('query', 'N/A')}")
                print(f"検索地域: {data.get('region', 'N/A')}")
                print(f"検索結果数: {data.get('count', 0)}")
                
                # 検索結果の詳細表示
                results = data.get('results', [])
                for j, result in enumerate(results[:3], 1):  # 最初の3件のみ表示
                    print(f"  {j}. {result.get('symbol', 'N/A')} - {result.get('name', 'N/A')}")
                    print(f"     取引所: {result.get('exchange', 'N/A')} | タイプ: {result.get('type', 'N/A')}")
                    
                    # 株価情報（新APIの特徴）
                    if result.get('current_price'):
                        price_info = f"     価格: {result['current_price']} {result.get('currency', 'USD')}"
                        if result.get('price_change'):
                            direction = "↑" if result.get('price_change_direction') == 'up' else "↓" if result.get('price_change_direction') == 'down' else "→"
                            price_info += f" ({result['price_change']:+.2f}, {result.get('price_change_percent', 0):+.2f}% {direction})"
                        print(price_info)
                    
                    if result.get('market_cap'):
                        print(f"     時価総額: {result['market_cap']:,}")
                
                if len(results) > 3:
                    print(f"  ... 他 {len(results) - 3} 件")
                    
            else:
                print(f"❌ エラー: ステータスコード {response.status_code}")
                print(f"レスポンス: {response.text[:200]}...")
            
        except requests.exceptions.Timeout:
            print(f"❌ タイムアウト")
        except requests.exceptions.RequestException as e:
            print(f"❌ リクエストエラー: {e}")
        except json.JSONDecodeError as e:
            print(f"❌ JSONデコードエラー: {e}")
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")
        
        print()

def test_comprehensive_info_api():
    """包括的情報APIをテスト"""
    
    print("=== YFinance API 包括的情報テスト ===")
    
    # テストケース
    test_tickers = ['AAPL', 'MSFT', 'TSLA', 'GOOGL', '7203.T', 'INVALID_TICKER']
    
    for i, ticker in enumerate(test_tickers, 1):
        print(f"--- テスト {i}: {ticker} ---")
        
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE_URL}/info", params={"ticker": ticker}, timeout=30)
            response_time = time.time() - start_time
            
            print(f"レスポンス時間: {response_time:.2f}秒")
            print(f"ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if 'error' in data:
                    print(f"❌ APIエラー: {data['error']}")
                else:
                    print(f"✅ 成功")
                    
                    # データ種類の確認
                    data_types = []
                    data_mapping = {
                        'info': '基本情報',
                        'price': '価格情報',
                        'history': '価格履歴',
                        'dividends': '配当',
                        'splits': '株式分割',
                        'financials': '財務諸表',
                        'sustainability': 'ESG情報',
                        'recommendations': 'アナリスト推奨',
                        'calendar': '決算カレンダー',
                        'holders': '株主情報',
                        'isin': 'ISIN',
                        'news': 'ニュース'
                    }
                    
                    for key, label in data_mapping.items():
                        if data.get(key):
                            data_types.append(label)
                    
                    print(f"取得データ種類数: {len(data_types)}")
                    print(f"データ種類: {', '.join(data_types[:5])}{'...' if len(data_types) > 5 else ''}")
                    
                    # 主要情報の表示
                    if data.get('info'):
                        info = data['info']
                        print(f"会社名: {info.get('longName', 'N/A')}")
                        print(f"業界: {info.get('industry', 'N/A')}")
                    
                    if data.get('price'):
                        price = data['price']
                        print(f"現在価格: {price.get('current_price')} {price.get('currency', 'USD')}")
                    
                    if data.get('sustainability'):
                        esg = data['sustainability'].get('esgScores', {})
                        if esg:
                            print(f"ESG総合スコア: {esg.get('totalEsg', 'N/A')}")
            else:
                print(f"❌ エラー: ステータスコード {response.status_code}")
                print(f"レスポンス: {response.text[:200]}...")
            
        except requests.exceptions.Timeout:
            print(f"❌ タイムアウト")
        except Exception as e:
            print(f"❌ エラー: {e}")
        
        print()

def test_chart_api():
    """チャートAPIをテスト"""
    
    print("=== YFinance API チャートテスト ===")
    
    test_cases = [
        {"ticker": "AAPL", "period": "1d"},
        {"ticker": "MSFT", "period": "1mo"},
        {"ticker": "TSLA", "period": "1y"}
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"--- テスト {i}: {case['ticker']} ({case['period']}) ---")
        
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE_URL}/chart", params=case, timeout=30)
            response_time = time.time() - start_time
            
            print(f"レスポンス時間: {response_time:.2f}秒")
            print(f"ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if 'error' in data:
                    print(f"❌ APIエラー: {data['error']}")
                else:
                    print(f"✅ 成功")
                    print(f"データポイント数: {len(data.get('data', []))}")
                    
                    if data.get('data'):
                        first_point = data['data'][0]
                        last_point = data['data'][-1]
                        print(f"開始日: {first_point.get('date')}")
                        print(f"終了日: {last_point.get('date')}")
                        print(f"開始価格: {first_point.get('close')}")
                        print(f"終了価格: {last_point.get('close')}")
            else:
                print(f"❌ エラー: ステータスコード {response.status_code}")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
        
        print()

def main():
    """メイン関数"""
    print("YFinance API 総合テスト - 新API対応版")
    print("=" * 60)
    print()
    
    # 全てのAPIをテスト
    test_search_api()
    test_comprehensive_info_api()
    test_chart_api()
    
    print("=" * 60)
    print("テスト完了")
    print(f"\nテスト対象API:")
    print(f"• 検索: {API_BASE_URL}/search")
    print(f"• 包括的データ: {API_BASE_URL}/info")
    print(f"• チャートデータ: {API_BASE_URL}/chart")

if __name__ == "__main__":
    main()
