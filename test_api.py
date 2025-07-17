#!/usr/bin/env python3
"""
YFinance API テストスクリプト - 新API対応版
ローカルでLambda関数の動作をテストし、新しいAPIエンドポイントもテスト
"""

import json
import sys
import os
import requests
import time

# Lambda関数をインポート
from lambda_function import lambda_handler, get_stock_info_api

# 新API設定
API_BASE_URL = "https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod"

def test_local_info_api():
    """包括的情報APIのローカルテスト"""
    print("=== 包括的情報APIローカルテスト ===")
    
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', '7203.T', 'INVALID']
    
    for ticker in test_tickers:
        print(f"\nテスト: {ticker}")
        try:
            result = get_stock_info_api(ticker)
            print(f"成功: データタイプ数 = {len([k for k, v in result.items() if v and k != 'ticker'])}")
            
            # 主要データの存在確認
            data_types = {
                'info': 'basic info',
                'price': 'price data', 
                'history': 'price history',
                'dividends': 'dividends',
                'splits': 'stock splits',
                'financials': 'financial statements',
                'sustainability': 'ESG data',
                'recommendations': 'analyst recommendations',
                'calendar': 'earnings calendar',
                'holders': 'holders info',
                'isin': 'ISIN code'
            }
            
            available_data = []
            for key, desc in data_types.items():
                if result.get(key):
                    available_data.append(desc)
            
            print(f"利用可能データ: {', '.join(available_data[:5])}{'...' if len(available_data) > 5 else ''}")
            
        except Exception as e:
            print(f"エラー: {e}")

def test_remote_api():
    """リモートAPIテスト"""
    print("\n=== リモートAPIテスト ===")
    
    # 検索APIテスト
    print("\n--- 検索APIテスト ---")
    test_search_queries = [
        ("Apple", "US"),
        ("Microsoft", "US"), 
        ("Toyota", "JP"),
        ("AAPL", "US")
    ]
    
    for query, region in test_search_queries:
        print(f"\n検索テスト: {query} ({region})")
        try:
            url = f"{API_BASE_URL}/search"
            params = {"q": query, "region": region}
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"成功: {data.get('count', 0)} 件の結果")
                if data.get('results'):
                    first_result = data['results'][0]
                    print(f"最初の結果: {first_result.get('symbol')} - {first_result.get('name')}")
            else:
                print(f"エラー: {response.status_code}")
                
        except Exception as e:
            print(f"エラー: {e}")
    
    # 包括的情報APIテスト
    print("\n--- 包括的情報APIテスト ---")
    test_tickers_remote = ['AAPL', 'MSFT', 'TSLA', '7203.T']
    
    for ticker in test_tickers_remote:
        print(f"\n包括的情報テスト: {ticker}")
        try:
            url = f"{API_BASE_URL}/info"
            params = {"ticker": ticker}
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'error' in data:
                    print(f"API エラー: {data['error']}")
                else:
                    data_count = len([k for k, v in data.items() if v and k != 'ticker'])
                    print(f"成功: {data_count} 種類のデータを取得")
                    
                    # 価格情報の確認
                    if data.get('price'):
                        price = data['price']
                        print(f"現在価格: {price.get('current_price')} {price.get('currency')}")
                    
                    # ESG情報の確認
                    if data.get('sustainability'):
                        esg = data['sustainability'].get('esgScores', {})
                        if esg:
                            print(f"ESG総合スコア: {esg.get('totalEsg')}")
            else:
                print(f"エラー: {response.status_code}")
                print(f"レスポンス: {response.text[:200]}...")
                
        except Exception as e:
            print(f"エラー: {e}")

def test_lambda_handler_local():
    """Lambda ハンドラーのローカルテスト"""
    print("\n=== Lambda ハンドラーローカルテスト ===")
    
    test_events = [
        {
            "httpMethod": "GET",
            "path": "/search",
            "queryStringParameters": {"q": "Apple", "region": "US"}
        },
        {
            "httpMethod": "GET", 
            "path": "/info",
            "queryStringParameters": {"ticker": "AAPL"}
        },
        {
            "httpMethod": "GET",
            "path": "/chart",
            "queryStringParameters": {"ticker": "AAPL", "period": "1mo"}
        }
    ]
    
    for i, event in enumerate(test_events, 1):
        print(f"\nテスト {i}: {event['path']}")
        try:
            context = {}  # 簡易コンテキスト
            response = lambda_handler(event, context)
            
            print(f"ステータス: {response['statusCode']}")
            
            # レスポンスボディをパース
            try:
                body = json.loads(response['body'])
                if event['path'] == '/search':
                    print(f"検索結果: {body.get('count', 0)} 件")
                elif event['path'] == '/info':
                    if 'error' in body:
                        print(f"エラー: {body['error']}")
                    else:
                        data_count = len([k for k, v in body.items() if v and k != 'ticker'])
                        print(f"データ種類: {data_count}")
                elif event['path'] == '/chart':
                    if 'error' in body:
                        print(f"エラー: {body['error']}")
                    else:
                        print(f"チャートデータ: {len(body.get('data', []))} ポイント")
            except Exception as parse_error:
                print(f"レスポンス解析エラー: {parse_error}")
                print(f"生レスポンス: {response['body'][:200]}...")
                
        except Exception as e:
            print(f"Lambda実行エラー: {e}")

def test_performance_comparison():
    """ローカルとリモートAPIのパフォーマンス比較"""
    print("\n=== パフォーマンス比較テスト ===")
    
    test_ticker = "AAPL"
    
    # ローカル実行時間測定
    print(f"\nローカル実行テスト: {test_ticker}")
    start_time = time.time()
    try:
        local_result = get_stock_info_api(test_ticker)
        local_time = time.time() - start_time
        local_data_types = len([k for k, v in local_result.items() if v and k != 'ticker'])
        print(f"ローカル実行時間: {local_time:.2f}秒")
        print(f"取得データ種類: {local_data_types}")
    except Exception as e:
        print(f"ローカル実行エラー: {e}")
        local_time = None
    
    # リモート実行時間測定
    print(f"\nリモート実行テスト: {test_ticker}")
    start_time = time.time()
    try:
        url = f"{API_BASE_URL}/info"
        params = {"ticker": test_ticker}
        response = requests.get(url, params=params, timeout=30)
        remote_time = time.time() - start_time
        
        if response.status_code == 200:
            remote_result = response.json()
            if 'error' not in remote_result:
                remote_data_types = len([k for k, v in remote_result.items() if v and k != 'ticker'])
                print(f"リモート実行時間: {remote_time:.2f}秒")
                print(f"取得データ種類: {remote_data_types}")
            else:
                print(f"リモートAPIエラー: {remote_result['error']}")
                remote_time = None
        else:
            print(f"リモートAPI HTTPエラー: {response.status_code}")
            remote_time = None
    except Exception as e:
        print(f"リモート実行エラー: {e}")
        remote_time = None
    
    # 比較結果
    if local_time and remote_time:
        print(f"\n--- パフォーマンス比較結果 ---")
        print(f"ローカル: {local_time:.2f}秒")
        print(f"リモート: {remote_time:.2f}秒")
        if local_time < remote_time:
            print(f"ローカルが {remote_time/local_time:.1f}倍高速")
        else:
            print(f"リモートが {local_time/remote_time:.1f}倍高速")

def main():
    """メイン関数"""
    print("YFinance API 総合テスト - 新API対応版")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == 'local':
            test_local_info_api()
        elif test_type == 'remote':
            test_remote_api()
        elif test_type == 'lambda':
            test_lambda_handler_local()
        elif test_type == 'performance':
            test_performance_comparison()
        else:
            print(f"不明なテストタイプ: {test_type}")
            print("使用可能なテストタイプ: local, remote, lambda, performance")
    else:
        # 全てのテストを実行
        test_local_info_api()
        test_remote_api()
        test_lambda_handler_local()
        test_performance_comparison()
    
    print("\n" + "=" * 60)
    print("テスト完了")
    print(f"\nAPI エンドポイント:")
    print(f"• 検索: {API_BASE_URL}/search")
    print(f"• 包括的データ: {API_BASE_URL}/info")
    print(f"• チャートデータ: {API_BASE_URL}/chart")

if __name__ == "__main__":
    main()
