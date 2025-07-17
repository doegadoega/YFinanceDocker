#!/usr/bin/env python3
"""
YFinance 検索ツール - 新API対応版
株式の検索と基本情報の取得を行う（Lambda関数を直接使用して統一）
"""

import yfinance as yf
import requests
import os
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime

# Lambda関数から直接インポート（統一のため）
from lambda_function import (
    search_stocks_api,
    get_stock_info_api,
    get_api_gateway_url,
    # 共通関数をインポート（重複回避）
    format_currency,
    get_execution_info,
    display_search_results_api,
    display_comprehensive_info_api
)

# 実行モード設定
EXECUTION_MODE = os.getenv('EXECUTION_MODE', 'LOCAL')  # LOCAL, DOCKER, LAMBDA

# APIエンドポイント設定（環境変数から取得可能）
API_BASE_URL = os.getenv('YFINANCE_API_URL', "https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod")

def search_stocks_local(query: str, region: str = "US") -> Optional[List[Dict[str, Any]]]:
    """
    ローカルで株式を検索（yfinanceを使用）
    
    Args:
        query (str): 検索クエリ
        region (str): 検索地域
    
    Returns:
        list: 検索結果のリスト
    """
    try:
        # yfinanceの検索機能を使用
        search_results = yf.Tickers(query)
        results = []
        
        for ticker in search_results.tickers:
            try:
                info = ticker.info
                if info:
                    result = {
                        'symbol': info.get('symbol', 'N/A'),
                        'name': info.get('longName', info.get('shortName', 'N/A')),
                        'exchange': info.get('exchange', 'N/A'),
                        'type': info.get('quoteType', 'N/A'),
                        'current_price': info.get('currentPrice'),
                        'currency': info.get('currency', 'USD'),
                        'market_cap': info.get('marketCap')
                    }
                    results.append(result)
            except Exception as e:
                print(f"警告: {ticker} の情報取得に失敗 - {e}")
                continue
        
        return results
        
    except Exception as e:
        print(f"ローカル検索エラー: {e}")
        return None

def search_stocks_api_unified(query: str, region: str = "US") -> Optional[Dict[str, Any]]:
    """
    Lambda関数を直接使用して株式を検索（完全統一）
    
    Args:
        query (str): 検索クエリ
        region (str): 検索地域
    
    Returns:
        dict: 検索結果
    """
    try:
        # Lambda関数を直接呼び出し
        query_params = {'region': region}
        result = search_stocks_api(query, query_params)
        
        # 実行環境情報を追加
        if not result.get('error'):
            result['execution_info'] = get_execution_info(EXECUTION_MODE)
        
        return result
            
    except Exception as e:
        print(f"予期しないエラー: {e}")
        return {'error': f'検索エラー: {e}'}

def get_stock_info_api_unified(ticker: str, period: str = "1mo") -> Optional[Dict[str, Any]]:
    """
    Lambda関数を直接使用して包括的な株式データを取得（完全統一）
    
    Args:
        ticker (str): ティッカーシンボル
        period (str): 取得期間
    
    Returns:
        dict: 包括的な株式データ
    """
    try:
        # Lambda関数を直接呼び出し
        result = get_stock_info_api(ticker, period)
        
        # 実行環境情報を追加
        if not result.get('error'):
            result['execution_info'] = get_execution_info(EXECUTION_MODE)
        
        return result
            
    except Exception as e:
        print(f"予期しないエラー: {e}")
        return {'error': f'データ取得エラー: {e}'}

def main() -> None:
    """メイン関数 - Lambda関数を直接使用して完全統一"""
    # 実行環境情報を表示
    exec_info = get_execution_info(EXECUTION_MODE)
    print("YFinance 検索ツール - Lambda関数直接使用版")
    print("=" * 50)
    print(f"実行モード: {exec_info['mode']}")
    print(f"API URL: {API_BASE_URL}")
    print(f"実行時刻: {exec_info['timestamp']}")
    print("=" * 50)
    
    # コマンドライン引数の処理
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python yfinance_search.py <検索クエリ> [地域]")
        print("  例: python yfinance_search.py apple US")
        print("  例: python yfinance_search.py toyota JP")
        return
    
    query = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else "US"
    
    print(f"\n検索クエリ: '{query}' (地域: {region})")
    print("-" * 40)
    
    # 1. API検索（Lambda関数直接使用）
    print("\n1. API検索（Lambda関数直接使用）")
    print("-" * 30)
    
    api_results = search_stocks_api_unified(query, region)
    if api_results:
        display_search_results_api(api_results)
    
    # 2. ローカル検索（比較用）
    print("\n\n2. ローカル検索（比較用）")
    print("-" * 25)
    
    local_results = search_stocks_local(query, region)
    if local_results:
        print(f"\n=== ローカル検索結果: '{query}' ({region}) ===")
        print(f"件数: {len(local_results)}")
        
        for i, result in enumerate(local_results, 1):
            print(f"\n{i}. {result.get('symbol', 'N/A')} - {result.get('name', 'N/A')}")
            print(f"   取引所: {result.get('exchange', 'N/A')} | タイプ: {result.get('type', 'N/A')}")
            
            # 価格情報の安全な表示
            current_price = result.get('current_price')
            if current_price is not None:
                currency = result.get('currency', 'USD')
                print(f"   価格: {format_currency(current_price, currency)}")
            else:
                print("   価格: N/A")
    
    # 3. 最初の結果の詳細情報を取得
    if api_results and not api_results.get('error') and api_results.get('results'):
        first_result = api_results['results'][0]
        symbol = first_result.get('symbol')
        
        if symbol:
            print(f"\n\n3. 詳細情報取得: {symbol}")
            print("-" * 35)
            
            detailed_info = get_stock_info_api_unified(symbol, "1mo")
            if detailed_info:
                display_comprehensive_info_api(detailed_info)
    
    print("\n" + "=" * 50)
    print("検索完了")
    print("\n統一された特徴:")
    print("• Lambda関数を直接使用して完全統一")
    print("• 高速な株式検索機能")
    print("• 包括的な金融データ取得")
    print("• 複数地域での検索対応")
    print("• 重複コードの排除")
    print(f"\n実行環境: {exec_info['mode']}")

if __name__ == "__main__":
    main() 