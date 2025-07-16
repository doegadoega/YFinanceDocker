#!/usr/bin/env python3
"""
YFinance API テストスクリプト
ローカルでLambda関数の動作をテスト
"""

import json
import sys
import os

# Lambda関数をインポート
from lambda_function import get_stock_price_api, get_stock_info_api, get_stock_history_api


def test_price_api():
    """株価取得APIのテスト"""
    print("=== 株価取得APIテスト ===")
    
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'INVALID']
    
    for ticker in test_tickers:
        print(f"\nテスト: {ticker}")
        result = get_stock_price_api(ticker)
        print(f"結果: {json.dumps(result, indent=2, ensure_ascii=False)}")


def test_info_api():
    """詳細情報APIのテスト"""
    print("\n=== 詳細情報APIテスト ===")
    
    test_tickers = ['AAPL', 'TSLA']
    
    for ticker in test_tickers:
        print(f"\nテスト: {ticker}")
        result = get_stock_info_api(ticker)
        print(f"結果: {json.dumps(result, indent=2, ensure_ascii=False)}")


def test_history_api():
    """履歴データAPIのテスト"""
    print("\n=== 履歴データAPIテスト ===")
    
    test_cases = [
        ('AAPL', '1mo'),
        ('MSFT', '1y'),
        ('GOOGL', '5d')
    ]
    
    for ticker, period in test_cases:
        print(f"\nテスト: {ticker} - {period}")
        result = get_stock_history_api(ticker, period)
        if not result.get('error'):
            # データが多いので最初の5件のみ表示
            if 'data' in result and len(result['data']) > 5:
                result['data'] = result['data'][:5]
                result['note'] = f"最初の5件のみ表示（全{result['count']}件）"
        print(f"結果: {json.dumps(result, indent=2, ensure_ascii=False)}")


def test_lambda_handler():
    """Lambda ハンドラーのテスト"""
    print("\n=== Lambda ハンドラーテスト ===")
    
    from lambda_function import lambda_handler
    
    # テストイベント
    test_events = [
        {
            'resource': '/price/{ticker}',
            'httpMethod': 'GET',
            'pathParameters': {'ticker': 'AAPL'},
            'queryStringParameters': None
        },
        {
            'resource': '/info/{ticker}',
            'httpMethod': 'GET',
            'pathParameters': {'ticker': 'MSFT'},
            'queryStringParameters': None
        },
        {
            'resource': '/history/{ticker}',
            'httpMethod': 'GET',
            'pathParameters': {'ticker': 'GOOGL'},
            'queryStringParameters': {'period': '1mo'}
        },
        {
            'resource': '/price/{ticker}',
            'httpMethod': 'OPTIONS',
            'pathParameters': {'ticker': 'AAPL'},
            'queryStringParameters': None
        }
    ]
    
    for i, event in enumerate(test_events):
        print(f"\nテストケース {i+1}: {event['httpMethod']} {event['resource']}")
        response = lambda_handler(event, {})
        print(f"ステータス: {response['statusCode']}")
        print(f"ヘッダー: {json.dumps(response['headers'], indent=2)}")
        
        # レスポンスボディをパース
        try:
            body = json.loads(response['body'])
            print(f"ボディ: {json.dumps(body, indent=2, ensure_ascii=False)}")
        except:
            print(f"ボディ: {response['body']}")


def main():
    """メイン関数"""
    print("YFinance API ローカルテスト")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == 'price':
            test_price_api()
        elif test_type == 'info':
            test_info_api()
        elif test_type == 'history':
            test_history_api()
        elif test_type == 'lambda':
            test_lambda_handler()
        else:
            print(f"不明なテストタイプ: {test_type}")
            print("使用可能なテストタイプ: price, info, history, lambda")
    else:
        # 全てのテストを実行
        test_price_api()
        test_info_api()
        test_history_api()
        test_lambda_handler()


if __name__ == "__main__":
    main()