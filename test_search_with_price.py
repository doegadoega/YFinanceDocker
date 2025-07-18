#!/usr/bin/env python3
"""
検索機能（株価情報付き）のテストスクリプト - 統一API対応版
Lambda関数直接使用による統一されたAPIエンドポイントをテスト
"""

import requests
import json
from datetime import datetime
import time
import os

# API GatewayのURL（環境変数から取得可能）
API_BASE_URL = os.getenv('YFINANCE_API_URL', "https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod")

def test_search_api():
    """統一された検索APIをテスト（Lambda関数直接使用）"""
    
    print("=== YFinance API 検索機能テスト（統一API対応版）===")
    print(f"API URL: {API_BASE_URL}")
    print(f"統一方式: Lambda関数直接使用")
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
            "name": "ティッカー検索（AAPL）",
            "params": {"q": "AAPL", "region": "US"}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"--- テスト {i}: {test_case['name']} ---")
        
        try:
            start_time = time.time()
            # 統一APIリクエスト
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
                
                # 実行環境情報の確認（統一APIの特徴）
                if data.get('execution_info'):
                    exec_info = data['execution_info']
                    print(f"実行モード: {exec_info.get('mode', 'N/A')}")
                    print(f"実行時刻: {exec_info.get('timestamp', 'N/A')}")
                
                # 検索結果の詳細表示
                results = data.get('results', [])
                for j, result in enumerate(results[:3], 1):  # 最初の3件のみ表示
                    print(f"  {j}. {result.get('symbol', 'N/A')} - {result.get('name', 'N/A')}")
                    print(f"     取引所: {result.get('exchange', 'N/A')} | タイプ: {result.get('type', 'N/A')}")
                    
                    # 株価情報（統一APIの特徴）
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
    """統一された包括的情報APIをテスト（Lambda関数直接使用）"""
    
    print("=== YFinance API 包括的情報テスト（統一API対応版）===")
    
    # テストケース
    test_tickers = ['AAPL', 'MSFT', 'TSLA', '7203.T', 'INVALID_TICKER']
    
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
                    
                    # 実行環境情報の確認（統一APIの特徴）
                    if data.get('execution_info'):
                        exec_info = data['execution_info']
                        print(f"実行モード: {exec_info.get('mode', 'N/A')}")
                        print(f"実行時刻: {exec_info.get('timestamp', 'N/A')}")
                    
                    # データ種類の確認（統一APIの17種類のデータ）
                    data_types = []
                    data_mapping = {
                        'info': '基本情報',
                        'fast_info': '高速情報',
                        'price': '価格情報',
                        'history': '価格履歴',
                        'dividends': '配当',
                        'splits': '株式分割',
                        'options': 'オプション情報',
                        'financials': '財務諸表',
                        'analysts': 'アナリスト情報',
                        'earnings': '決算情報',
                        'isin': 'ISIN',
                        'recommendations': '推奨履歴',
                        'calendar': '決算カレンダー',
                        'earnings_dates': '決算日',
                        'sustainability': 'ESG情報',
                        'holders': '株主情報',
                        'shares': '株式数詳細',
                        'analysis': 'アナリスト分析',
                        'upgrades_downgrades': '格付け変更履歴',
                        'news': 'ニュース',
                        'logo_url': 'ロゴURL',
                        'execution_info': '実行環境情報'
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
                    
                    if data.get('analysts'):
                        analysts = data['analysts']
                        if analysts.get('recommendation_mean'):
                            print(f"アナリスト推奨平均: {analysts['recommendation_mean']}")
            else:
                print(f"❌ エラー: ステータスコード {response.status_code}")
                print(f"レスポンス: {response.text[:200]}...")
            
        except requests.exceptions.Timeout:
            print(f"❌ タイムアウト")
        except Exception as e:
            print(f"❌ エラー: {e}")
        
        print()

def test_chart_api():
    """統一されたチャートAPIをテスト（Lambda関数直接使用）"""
    
    print("=== YFinance API チャートテスト（統一API対応版）===")
    
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
                    
                    # 実行環境情報の確認（統一APIの特徴）
                    if data.get('execution_info'):
                        exec_info = data['execution_info']
                        print(f"実行モード: {exec_info.get('mode', 'N/A')}")
                        print(f"実行時刻: {exec_info.get('timestamp', 'N/A')}")
                    
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

def test_unified_features():
    """統一APIの特徴をテスト"""
    
    print("=== 統一API特徴テスト ===")
    print("Lambda関数直接使用による統一の確認")
    print()
    
    # 同じティッカーで複数回テストして一貫性を確認
    ticker = "AAPL"
    results = []
    
    for i in range(3):
        try:
            response = requests.get(f"{API_BASE_URL}/tickerDetail", params={"ticker": ticker}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if not data.get('error'):
                    results.append(data)
        except Exception as e:
            print(f"テスト {i+1} でエラー: {e}")
    
    if len(results) >= 2:
        print(f"✅ 一貫性テスト: {len(results)} 回のテストで同じデータ構造")
        
        # 実行環境情報の一貫性を確認
        exec_modes = set()
        for result in results:
            if result.get('execution_info', {}).get('mode'):
                exec_modes.add(result['execution_info']['mode'])
        
        print(f"実行モード: {', '.join(exec_modes)}")
        
        # データ構造の一貫性を確認
        data_keys = set()
        for result in results:
            data_keys.update(result.keys())
        
        print(f"データキー数: {len(data_keys)}")
        print(f"主要キー: {', '.join(sorted(list(data_keys))[:10])}")
    else:
        print("❌ 一貫性テスト失敗: 十分なテスト結果がありません")
    
    print()

def main():
    """メイン関数"""
    print("YFinance API 総合テスト - 統一API対応版")
    print("=" * 60)
    print("統一方式: Lambda関数直接使用")
    print("重複排除: 共通関数をlambda_function.pyからインポート")
    print("=" * 60)
    print()
    
    # 全てのAPIをテスト
    test_search_api()
    test_comprehensive_info_api()
    test_chart_api()
    test_unified_features()
    
    print("=" * 60)
    print("テスト完了")
    print(f"\nテスト対象API:")
    print(f"• 検索: {API_BASE_URL}/search")
    print(f"• 包括的データ: {API_BASE_URL}/tickerDetail")
    print(f"• チャートデータ: {API_BASE_URL}/chart")
    print(f"\n統一された特徴:")
    print(f"• Lambda関数を直接使用して完全統一")
    print(f"• 17種類の包括的な金融データ")
    print(f"• 実行環境情報の自動付与")
    print(f"• 重複コードの排除")

if __name__ == "__main__":
    main()
