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
    get_stock_basic_info_api,
    get_stock_price_api,
    get_stock_history_api,
    get_stock_financials_api,
    get_stock_analysts_api,
    get_stock_holders_api,
    get_stock_events_api,
    get_stock_news_api,
    get_stock_options_api,
    get_stock_sustainability_api,
    get_stock_home_api,
    get_stock_rankings_api,
    get_sector_rankings_api,
    get_crypto_rankings_api,
    get_markets_indices_api,
    get_markets_currencies_api,
    get_markets_commodities_api,
    get_markets_status_api,
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

def get_rankings_cli(ranking_type: str, market: str = "us", limit: int = 10) -> Optional[Dict[str, Any]]:
    """
    CLI用のランキング取得（Lambda関数直接使用）
    
    Args:
        ranking_type (str): ランキング種別
        market (str): 市場
        limit (int): 取得件数
    
    Returns:
        dict: ランキング結果
    """
    try:
        query_params = {
            'type': ranking_type,
            'market': market,
            'limit': str(limit)
        }
        result = get_stock_rankings_api(query_params)
        
        if not result.get('error'):
            result['execution_info'] = get_execution_info(EXECUTION_MODE)
        
        return result
            
    except Exception as e:
        print(f"予期しないエラー: {e}")
        return {'error': f'ランキング取得エラー: {e}'}

def get_sectors_cli(limit: int = 10) -> Optional[Dict[str, Any]]:
    """
    CLI用のセクターランキング取得（Lambda関数直接使用）
    
    Args:
        limit (int): 取得件数
    
    Returns:
        dict: セクターランキング結果
    """
    try:
        query_params = {'limit': str(limit)}
        result = get_sector_rankings_api(query_params)
        
        if not result.get('error'):
            result['execution_info'] = get_execution_info(EXECUTION_MODE)
        
        return result
            
    except Exception as e:
        print(f"予期しないエラー: {e}")
        return {'error': f'セクターランキング取得エラー: {e}'}

def get_crypto_cli(sort_by: str = "change", limit: int = 10) -> Optional[Dict[str, Any]]:
    """
    CLI用の暗号通貨ランキング取得（Lambda関数直接使用）
    
    Args:
        sort_by (str): ソート基準
        limit (int): 取得件数
    
    Returns:
        dict: 暗号通貨ランキング結果
    """
    try:
        query_params = {
            'sort': sort_by,
            'limit': str(limit)
        }
        result = get_crypto_rankings_api(query_params)
        
        if not result.get('error'):
            result['execution_info'] = get_execution_info(EXECUTION_MODE)
        
        return result
            
    except Exception as e:
        print(f"予期しないエラー: {e}")
        return {'error': f'暗号通貨ランキング取得エラー: {e}'}

def get_markets_indices_cli() -> Optional[Dict[str, Any]]:
    """
    CLI用の主要指数取得（Lambda関数直接使用）
    
    Returns:
        dict: 主要指数結果
    """
    try:
        query_params = {}
        result = get_markets_indices_api(query_params)
        
        if not result.get('error'):
            result['execution_info'] = get_execution_info(EXECUTION_MODE)
        
        return result
            
    except Exception as e:
        print(f"予期しないエラー: {e}")
        return {'error': f'主要指数取得エラー: {e}'}

def get_markets_currencies_cli() -> Optional[Dict[str, Any]]:
    """
    CLI用の為替レート取得（Lambda関数直接使用）
    
    Returns:
        dict: 為替レート結果
    """
    try:
        query_params = {}
        result = get_markets_currencies_api(query_params)
        
        if not result.get('error'):
            result['execution_info'] = get_execution_info(EXECUTION_MODE)
        
        return result
            
    except Exception as e:
        print(f"予期しないエラー: {e}")
        return {'error': f'為替レート取得エラー: {e}'}

def get_markets_commodities_cli() -> Optional[Dict[str, Any]]:
    """
    CLI用の商品価格取得（Lambda関数直接使用）
    
    Returns:
        dict: 商品価格結果
    """
    try:
        query_params = {}
        result = get_markets_commodities_api(query_params)
        
        if not result.get('error'):
            result['execution_info'] = get_execution_info(EXECUTION_MODE)
        
        return result
            
    except Exception as e:
        print(f"予期しないエラー: {e}")
        return {'error': f'商品価格取得エラー: {e}'}

def get_markets_status_cli() -> Optional[Dict[str, Any]]:
    """
    CLI用の市場開閉状況取得（Lambda関数直接使用）
    
    Returns:
        dict: 市場開閉状況結果
    """
    try:
        query_params = {}
        result = get_markets_status_api(query_params)
        
        if not result.get('error'):
            result['execution_info'] = get_execution_info(EXECUTION_MODE)
        
        return result
            
    except Exception as e:
        print(f"予期しないエラー: {e}")
        return {'error': f'市場開閉状況取得エラー: {e}'}

def main():
    """メイン関数 - Lambda関数を直接使用して完全統一"""
    parser = argparse.ArgumentParser(
        description='YFinance CLI ツール - Lambda関数直接使用版',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s search apple US          # Appleを検索
  %(prog)s info AAPL 1mo            # AAPLの1ヶ月データ（統合版）
  %(prog)s basic AAPL               # AAPLの基本情報
  %(prog)s price AAPL               # AAPLの株価情報
  %(prog)s history AAPL 1y          # AAPLの1年履歴
  %(prog)s financials AAPL          # AAPLの財務情報
  %(prog)s analysts AAPL            # AAPLのアナリスト情報
  %(prog)s holders AAPL             # AAPLの株主情報
  %(prog)s events AAPL              # AAPLのイベント情報
  %(prog)s news AAPL                # AAPLのニュース情報
  %(prog)s options AAPL             # AAPLのオプション情報
  %(prog)s sustainability AAPL      # AAPLのESG情報
  %(prog)s home                     # ホーム画面情報（株価指数、セクター情報）
  %(prog)s rankings gainers --limit 10    # 上昇率TOP10
  %(prog)s rankings losers --limit 10     # 下落率TOP10
  %(prog)s rankings volume --limit 20     # 出来高TOP20
  %(prog)s rankings market-cap --limit 20 # 時価総額TOP20
  %(prog)s sectors --limit 10             # セクターランキングTOP10
  %(prog)s crypto --sort change --limit 10 # 暗号通貨ランキング
  %(prog)s indices                    # 主要指数一覧
  %(prog)s currencies                 # 為替レート
  %(prog)s commodities                # 商品価格
  %(prog)s status                     # 市場開閉状況
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
    
    # 株価情報コマンド
    price_parser = subparsers.add_parser('price', help='株価情報を取得')
    price_parser.add_argument('ticker', help='ティッカーシンボル')
    
    # 履歴情報コマンド
    history_parser = subparsers.add_parser('history', help='株価履歴を取得')
    history_parser.add_argument('ticker', help='ティッカーシンボル')
    history_parser.add_argument('--period', default='1mo',
                               choices=['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'],
                               help='取得期間（デフォルト: 1mo）')
    
    # 財務情報コマンド
    financials_parser = subparsers.add_parser('financials', help='財務情報を取得')
    financials_parser.add_argument('ticker', help='ティッカーシンボル')
    
    # アナリスト情報コマンド
    analysts_parser = subparsers.add_parser('analysts', help='アナリスト情報を取得')
    analysts_parser.add_argument('ticker', help='ティッカーシンボル')
    
    # 株主情報コマンド
    holders_parser = subparsers.add_parser('holders', help='株主情報を取得')
    holders_parser.add_argument('ticker', help='ティッカーシンボル')
    
    # イベント情報コマンド
    events_parser = subparsers.add_parser('events', help='イベント情報を取得')
    events_parser.add_argument('ticker', help='ティッカーシンボル')
    
    # ニュース情報コマンド
    news_parser = subparsers.add_parser('news', help='ニュース情報を取得')
    news_parser.add_argument('ticker', help='ティッカーシンボル')
    
    # オプション情報コマンド
    options_parser = subparsers.add_parser('options', help='オプション情報を取得')
    options_parser.add_argument('ticker', help='ティッカーシンボル')
    
    # ESG情報コマンド
    sustainability_parser = subparsers.add_parser('sustainability', help='ESG情報を取得')
    sustainability_parser.add_argument('ticker', help='ティッカーシンボル')
    
    # ホーム情報コマンド
    home_parser = subparsers.add_parser('home', help='ホーム画面用情報（株価指数、セクター情報）を取得')
    
    # ランキング系コマンド
    rankings_parser = subparsers.add_parser('rankings', help='株価関連ランキングを取得')
    rankings_parser.add_argument('type', choices=['gainers', 'losers', 'volume', 'market-cap'],
                                help='ランキング種別')
    rankings_parser.add_argument('--market', default='us', choices=['us'],
                                help='市場（デフォルト: us）')
    rankings_parser.add_argument('--limit', type=int, default=10,
                                help='取得件数（デフォルト: 10）')
    
    # セクターランキングコマンド
    sectors_parser = subparsers.add_parser('sectors', help='セクター・業界ランキングを取得')
    sectors_parser.add_argument('--limit', type=int, default=10,
                               help='取得件数（デフォルト: 10）')
    
    # 暗号通貨ランキングコマンド
    crypto_parser = subparsers.add_parser('crypto', help='暗号通貨ランキングを取得')
    crypto_parser.add_argument('--sort', default='change', 
                              choices=['change', 'price', 'volume', 'market_cap'],
                              help='ソート基準（デフォルト: change）')
    crypto_parser.add_argument('--limit', type=int, default=10,
                              help='取得件数（デフォルト: 10）')
    
    # 市場情報系コマンド
    indices_parser = subparsers.add_parser('indices', help='主要指数一覧を取得')
    
    currencies_parser = subparsers.add_parser('currencies', help='為替レートを取得')
    
    commodities_parser = subparsers.add_parser('commodities', help='商品価格を取得')
    
    status_parser = subparsers.add_parser('status', help='市場開閉状況を取得')
    
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
        
        data = get_stock_basic_info_api(args.ticker)
        if data:
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                display_comprehensive_info_api(data)
    
    elif args.command == 'price':
        if not args.json:
            print(f"\n株価情報取得: {args.ticker}")
            print("-" * 25)
        
        data = get_stock_price_api(args.ticker)
        if data:
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                display_comprehensive_info_api(data)
    
    elif args.command == 'history':
        if not args.json:
            print(f"\n履歴情報取得: {args.ticker} (期間: {args.period})")
            print("-" * 35)
        
        data = get_stock_history_api(args.ticker, args.period)
        if data:
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                display_comprehensive_info_api(data)
    
    elif args.command == 'financials':
        if not args.json:
            print(f"\n財務情報取得: {args.ticker}")
            print("-" * 25)
        
        data = get_stock_financials_api(args.ticker)
        if data:
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                display_comprehensive_info_api(data)
    
    elif args.command == 'analysts':
        if not args.json:
            print(f"\nアナリスト情報取得: {args.ticker}")
            print("-" * 30)
        
        data = get_stock_analysts_api(args.ticker)
        if data:
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                display_comprehensive_info_api(data)
    
    elif args.command == 'holders':
        if not args.json:
            print(f"\n株主情報取得: {args.ticker}")
            print("-" * 25)
        
        data = get_stock_holders_api(args.ticker)
        if data:
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                display_comprehensive_info_api(data)
    
    elif args.command == 'events':
        if not args.json:
            print(f"\nイベント情報取得: {args.ticker}")
            print("-" * 30)
        
        data = get_stock_events_api(args.ticker)
        if data:
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                display_comprehensive_info_api(data)
    
    elif args.command == 'news':
        if not args.json:
            print(f"\nニュース情報取得: {args.ticker}")
            print("-" * 30)
        
        data = get_stock_news_api(args.ticker)
        if data:
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                display_comprehensive_info_api(data)
    
    elif args.command == 'options':
        if not args.json:
            print(f"\nオプション情報取得: {args.ticker}")
            print("-" * 30)
        
        data = get_stock_options_api(args.ticker)
        if data:
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                display_comprehensive_info_api(data)
    
    elif args.command == 'sustainability':
        if not args.json:
            print(f"\nESG情報取得: {args.ticker}")
            print("-" * 25)
        
        data = get_stock_sustainability_api(args.ticker)
        if data:
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                display_comprehensive_info_api(data)
    
    elif args.command == 'home':
        if not args.json:
            print(f"\nホーム画面情報取得")
            print("-" * 25)
        
        data = get_stock_home_api()
        if data:
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                display_comprehensive_info_api(data)
    
    elif args.command == 'rankings':
        if not args.json:
            print(f"\nランキング取得: {args.type} (市場: {args.market}, 件数: {args.limit})")
            print("-" * 50)
        
        data = get_rankings_cli(args.type, args.market, args.limit)
        if data:
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                display_comprehensive_info_api(data)
    
    elif args.command == 'sectors':
        if not args.json:
            print(f"\nセクターランキング取得 (件数: {args.limit})")
            print("-" * 35)
        
        data = get_sectors_cli(args.limit)
        if data:
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                display_comprehensive_info_api(data)
    
    elif args.command == 'crypto':
        if not args.json:
            print(f"\n暗号通貨ランキング取得 (ソート: {args.sort}, 件数: {args.limit})")
            print("-" * 45)
        
        data = get_crypto_cli(args.sort, args.limit)
        if data:
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                display_comprehensive_info_api(data)
    
    elif args.command == 'indices':
        if not args.json:
            print(f"\n主要指数一覧取得")
            print("-" * 25)
        
        data = get_markets_indices_cli()
        if data:
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                display_comprehensive_info_api(data)
    
    elif args.command == 'currencies':
        if not args.json:
            print(f"\n為替レート取得")
            print("-" * 20)
        
        data = get_markets_currencies_cli()
        if data:
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                display_comprehensive_info_api(data)
    
    elif args.command == 'commodities':
        if not args.json:
            print(f"\n商品価格取得")
            print("-" * 20)
        
        data = get_markets_commodities_cli()
        if data:
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                display_comprehensive_info_api(data)
    
    elif args.command == 'status':
        if not args.json:
            print(f"\n市場開閉状況取得")
            print("-" * 25)
        
        data = get_markets_status_cli()
        if data:
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                display_comprehensive_info_api(data)
    
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