#!/usr/bin/env python3
"""
YFinance CLI ツール - 新API対応版
コマンドラインから株式データを取得する（Lambda関数を直接使用して統一）
"""

import argparse
import sys
import os
import json
from typing import Optional, Dict, Any

# Lambda関数から直接インポート（統一のため）
from lambda_function import (
    get_stock_info_api,
    search_stocks_api,
    get_api_gateway_url,
    # 共通関数をインポート（重複回避）
    format_currency,
    get_execution_info,
    display_stock_info_local,
    display_comprehensive_info_api,
    display_search_results_api
)

# 実行モード設定
EXECUTION_MODE = os.getenv('EXECUTION_MODE', 'LOCAL')  # LOCAL, DOCKER, LAMBDA

# APIエンドポイント設定（環境変数から取得可能）
API_BASE_URL = os.getenv('YFINANCE_API_URL', "https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod")

def search_stocks_cli(query: str, region: str = "US") -> Optional[Dict[str, Any]]:
    """
    CLI用の株式検索（Lambda関数直接使用）
    
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

def get_stock_info_cli(ticker: str, period: str = "1mo") -> Optional[Dict[str, Any]]:
    """
    CLI用の包括的株式データ取得（Lambda関数直接使用）
    
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

def display_basic_info(ticker: str) -> None:
    """
    基本情報を表示（共通関数を使用）
    
    Args:
        ticker (str): ティッカーシンボル
    """
    display_stock_info_local(ticker)

def main():
    """メイン関数 - Lambda関数を直接使用して完全統一"""
    parser = argparse.ArgumentParser(
        description='YFinance CLI ツール - Lambda関数直接使用版',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s search apple US          # Appleを検索
  %(prog)s info AAPL 1mo            # AAPLの1ヶ月データ
  %(prog)s basic AAPL               # AAPLの基本情報
  %(prog)s search toyota JP         # トヨタを日本で検索
  %(prog)s search apple US --json   # JSON形式で出力
  %(prog)s info AAPL 1mo --json     # JSON形式で出力
        """
    )
    
    # グローバルオプション
    parser.add_argument('--json', action='store_true', 
                       help='JSON形式で出力（機械可読形式）')
    
    subparsers = parser.add_subparsers(dest='command', help='利用可能なコマンド')
    
    # 検索コマンド
    search_parser = subparsers.add_parser('search', help='株式を検索')
    search_parser.add_argument('query', help='検索クエリ')
    search_parser.add_argument('--region', default='US', 
                               choices=['US', 'JP', 'DE', 'CA', 'AU', 'GB', 'FR', 'IT', 'ES', 'KR', 'IN', 'HK', 'SG'],
                               help='検索地域（デフォルト: US）')
    
    # 包括的情報コマンド
    info_parser = subparsers.add_parser('info', help='包括的な株式情報を取得')
    info_parser.add_argument('ticker', help='ティッカーシンボル')
    info_parser.add_argument('--period', default='1mo',
                             choices=['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'],
                             help='取得期間（デフォルト: 1mo）')
    
    # 基本情報コマンド
    basic_parser = subparsers.add_parser('basic', help='基本情報を表示')
    basic_parser.add_argument('ticker', help='ティッカーシンボル')
    
    args = parser.parse_args()
    
    # JSON出力モードの場合はヘッダーを表示しない
    if not args.json:
        # 実行環境情報を表示
        exec_info = get_execution_info(EXECUTION_MODE)
        print("YFinance CLI ツール - Lambda関数直接使用版")
        print("=" * 50)
        print(f"実行モード: {exec_info['mode']}")
        print(f"API URL: {API_BASE_URL}")
        print(f"実行時刻: {exec_info['timestamp']}")
        print("=" * 50)
    
    if args.command == 'search':
        if not args.json:
            print(f"\n検索クエリ: '{args.query}' (地域: {args.region})")
            print("-" * 40)
        
        results = search_stocks_cli(args.query, args.region)
        if results:
            if args.json:
                # JSON形式で出力
                print(json.dumps(results, indent=2, ensure_ascii=False))
            else:
                # 人間可読形式で出力
                display_search_results_api(results)
    
    elif args.command == 'info':
        if not args.json:
            print(f"\n包括的情報取得: {args.ticker} (期間: {args.period})")
            print("-" * 45)
        
        data = get_stock_info_cli(args.ticker, args.period)
        if data:
            if args.json:
                # JSON形式で出力
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                # 人間可読形式で出力
                display_comprehensive_info_api(data)
    
    elif args.command == 'basic':
        if not args.json:
            print(f"\n基本情報取得: {args.ticker}")
            print("-" * 25)
        
        # 基本情報は現在JSON出力に対応していないため、通常表示
        display_basic_info(args.ticker)
    
    else:
        parser.print_help()
        return
    
    if not args.json:
        print("\n" + "=" * 50)
        print("実行完了")
        print("\n統一された特徴:")
        print("• Lambda関数を直接使用して完全統一")
        print("• 17種類の包括的な金融データ")
        print("• 高速な株式検索機能")
        print("• ESG情報、財務諸表、株主情報など")
        print("• 複数地域での検索対応")
        print("• 重複コードの排除")
        print(f"\n実行環境: {get_execution_info(EXECUTION_MODE)['mode']}")

if __name__ == "__main__":
    main() 