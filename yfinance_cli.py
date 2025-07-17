#!/usr/bin/env python3
"""
YFinance CLI ツール - 包括的な金融データ取得
コマンドラインから株式データを取得・分析する

新機能:
- 最新のYFinance APIメソッド（17種類のデータ）
- ESG情報、ISIN、株主情報、財務諸表等
- 検索機能、チャート生成
- 豊富な出力オプション
"""

import argparse
import yfinance as yf
import json
import pandas as pd
import numpy as np
from datetime import datetime
import requests

def serialize_for_json(obj):
    """オブジェクトをJSON serializable に変換"""
    if pd.isna(obj) or obj is None:
        return None
    elif isinstance(obj, (pd.Timestamp, datetime)):
        return obj.strftime('%Y-%m-%d') if hasattr(obj, 'strftime') else str(obj)
    elif isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {str(k): serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_json(item) for item in obj]
    elif hasattr(obj, 'to_dict'):
        return serialize_for_json(obj.to_dict())
    else:
        return obj

def safe_dataframe_to_dict(df):
    """DataFrameを安全にdictに変換（JSON serializable）"""
    if df.empty:
        return {}
    try:
        df_copy = df.copy()
        if hasattr(df_copy.index, 'strftime'):
            df_copy.index = df_copy.index.strftime('%Y-%m-%d')
        else:
            df_copy.index = df_copy.index.astype(str)
        
        result = df_copy.to_dict()
        return serialize_for_json(result)
    except Exception as e:
        return f"DataFrame変換エラー: {str(e)}"

def safe_dataframe_to_records(df):
    """DataFrameを安全にrecordsに変換（JSON serializable）"""
    if df.empty:
        return []
    try:
        records = df.to_dict('records')
        return serialize_for_json(records)
    except Exception as e:
        return f"Records変換エラー: {str(e)}"

def search_stocks(query, limit=10, region='US'):
    """銘柄検索（株価情報付き）"""
    try:
        base_url = "https://query1.finance.yahoo.com/v1/finance/search"
        
        if region.upper() == 'JP':
            params = {
                'q': query,
                'quotesCount': limit,
                'newsCount': 0,
                'enableFuzzyQuery': True,
                'region': 'JP',
                'lang': 'ja-JP'
            }
        else:
            params = {
                'q': query,
                'quotesCount': limit,
                'newsCount': 0,
                'enableFuzzyQuery': True
            }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(base_url, params=params, headers=headers)
        data = response.json()
        
        if 'quotes' in data and data['quotes']:
            results = []
            for quote in data['quotes'][:limit]:
                symbol = quote.get('symbol', '')
                
                result = {
                    'symbol': symbol,
                    'name': quote.get('longname', quote.get('shortname', '')),
                    'exchange': quote.get('exchange', ''),
                    'type': quote.get('quoteType', ''),
                    'score': quote.get('score', 0)
                }
                
                # 株価情報を取得
                try:
                    stock = yf.Ticker(symbol)
                    info = stock.info
                    
                    current_price = info.get('currentPrice', info.get('regularMarketPrice'))
                    previous_close = info.get('previousClose')
                    
                    if current_price is not None:
                        result['current_price'] = round(float(current_price), 2)
                        result['currency'] = info.get('currency', 'USD')
                        
                        if previous_close is not None:
                            previous_close = float(previous_close)
                            price_change = current_price - previous_close
                            price_change_percent = (price_change / previous_close) * 100
                            
                            result['previous_close'] = round(previous_close, 2)
                            result['price_change'] = round(price_change, 2)
                            result['price_change_percent'] = round(price_change_percent, 2)
                            result['price_change_direction'] = 'up' if price_change > 0 else 'down' if price_change < 0 else 'unchanged'
                        
                        result['market_cap'] = info.get('marketCap')
                        result['volume'] = info.get('volume')
                        
                except Exception as e:
                    result['price_error'] = f'株価取得エラー: {str(e)}'
                
                results.append(result)
            
            return {
                'query': query,
                'region': region,
                'results': results,
                'count': len(results)
            }
        else:
            return {
                'query': query,
                'region': region,
                'results': [],
                'count': 0,
                'message': '検索結果が見つかりませんでした'
            }
    except Exception as e:
        return {'error': f'検索エラー: {str(e)}'}



def get_comprehensive_info(ticker, period='1mo'):
    """包括的な企業情報を取得（APIと同じ17種類のデータ）"""
    try:
        stock = yf.Ticker(ticker)
        
        # 新API: 詳細情報
        try:
            info = stock.get_info()
        except Exception as e:
            info = {}
            info_error = str(e)
        else:
            info_error = None

        # 高速基本情報
        try:
            fast_info = stock.get_fast_info()
            if hasattr(fast_info, '__dict__'):
                fast_info_dict = {}
                for key in dir(fast_info):
                    if not key.startswith('_') and not callable(getattr(fast_info, key)):
                        try:
                            value = getattr(fast_info, key)
                            if value is not None:
                                fast_info_dict[key] = float(value) if isinstance(value, (int, float)) else str(value)
                        except:
                            pass
                fast_info = fast_info_dict
            else:
                fast_info = {}
        except Exception as e:
            fast_info = {}

        # 株価情報
        current_price = fast_info.get('last_price') or info.get('currentPrice') if info else None
        previous_close = fast_info.get('previous_close') or info.get('previousClose') if info else None
        price = None
        if current_price is not None:
            price = {
                'current_price': round(float(current_price), 2),
                'currency': fast_info.get('financial_currency') or info.get('currency', 'USD') if info else 'USD',
                'timestamp': datetime.now().isoformat()
            }
            if previous_close is not None:
                previous_close = float(previous_close)
                diff = current_price - previous_close
                price['previous_close'] = round(previous_close, 2)
                price['price_change'] = round(diff, 2)
                price['price_change_percent'] = round(diff / previous_close * 100, 2)
                price['price_change_direction'] = 'up' if diff > 0 else 'down' if diff < 0 else 'unchanged'

        # 履歴データ
        try:
            valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
            if period not in valid_periods:
                period = '1mo'
            
            hist_df = stock.history(period=period)
            history = [{
                'date': idx.strftime('%Y-%m-%d'),
                'open': round(float(row['Open']), 2),
                'high': round(float(row['High']), 2),
                'low': round(float(row['Low']), 2),
                'close': round(float(row['Close']), 2),
                'volume': int(row['Volume'])
            } for idx, row in hist_df.iterrows()]
        except Exception as e:
            history = f'履歴データ取得エラー: {str(e)}'

        # ニュース
        try:
            news = stock.get_news() or []
        except Exception as e:
            news = f'ニュース取得エラー: {str(e)}'

        # 配当
        try:
            dividends_series = stock.get_dividends()
            dividends = [{
                'date': idx.strftime('%Y-%m-%d'),
                'amount': float(val)
            } for idx, val in dividends_series.items()] if not dividends_series.empty else []
        except Exception as e:
            dividends = f'配当情報取得エラー: {str(e)}'

        # === 新しいYFinanceメソッド群 ===
        
        # ISIN
        try:
            isin = stock.get_isin()
        except Exception as e:
            isin = f'ISIN取得エラー: {str(e)}'

        # 推奨履歴
        try:
            recommendations = stock.get_recommendations()
            if not recommendations.empty:
                recommendations_data = safe_dataframe_to_records(recommendations)
            else:
                recommendations_data = []
        except Exception as e:
            recommendations_data = f'推奨履歴取得エラー: {str(e)}'

        # ESG情報
        try:
            sustainability = stock.get_sustainability()
            if not sustainability.empty:
                sustainability_data = safe_dataframe_to_dict(sustainability)
            else:
                sustainability_data = {}
        except Exception as e:
            sustainability_data = f'ESG情報取得エラー: {str(e)}'

        # 株主情報
        try:
            major_holders = stock.get_major_holders()
            institutional_holders = stock.get_institutional_holders()
            
            holders_data = {
                'major_holders': safe_dataframe_to_records(major_holders) if not major_holders.empty else [],
                'institutional_holders': safe_dataframe_to_records(institutional_holders) if not institutional_holders.empty else []
            }
        except Exception as e:
            holders_data = f'株主情報取得エラー: {str(e)}'

        # 財務諸表
        try:
            income_stmt = stock.get_income_stmt()
            balance_sheet = stock.get_balance_sheet()
            cashflow = stock.get_cashflow()
                
            financials = {
                'income_statement': safe_dataframe_to_dict(income_stmt) if not income_stmt.empty else {},
                'balance_sheet': safe_dataframe_to_dict(balance_sheet) if not balance_sheet.empty else {},
                'cashflow': safe_dataframe_to_dict(cashflow) if not cashflow.empty else {}
            }
        except Exception as e:
            financials = f'財務情報取得エラー: {str(e)}'

        result = {
            'ticker': ticker,
            'info': info,
            'info_error': info_error,
            'fast_info': fast_info,
            'price': price,
            'history': history,
            'news': news,
            'dividends': dividends,
            'isin': isin,
            'recommendations': recommendations_data,
            'sustainability': sustainability_data,
            'holders': holders_data,
            'financials': financials,
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'銘柄情報取得エラー: {str(e)}'}



def display_search_results(results):
    """検索結果を表示"""
    if 'error' in results:
        print(f"エラー: {results['error']}")
        return
    
    print(f"\n=== 検索結果: '{results['query']}' ({results['region']}) ===")
    print(f"件数: {results['count']}")
    
    for i, result in enumerate(results['results'], 1):
        print(f"\n{i}. {result['symbol']} - {result['name']}")
        print(f"   取引所: {result['exchange']} | タイプ: {result['type']}")
        
        if 'current_price' in result:
            price_info = f"   価格: {result['current_price']} {result['currency']}"
            if 'price_change' in result:
                direction = "↑" if result['price_change_direction'] == 'up' else "↓" if result['price_change_direction'] == 'down' else "→"
                price_info += f" ({result['price_change']:+.2f}, {result['price_change_percent']:+.2f}% {direction})"
            print(price_info)
        
        if 'market_cap' in result and result['market_cap']:
            print(f"   時価総額: {result['market_cap']:,}")

def display_comprehensive_info(data):
    """包括的な情報を表示"""
    if 'error' in data:
        print(f"エラー: {data['error']}")
        return
    
    print(f"\n=== {data['ticker']} の包括的情報 ===")
    
    # 基本情報
    if data['info']:
        info = data['info']
        print(f"会社名: {info.get('longName', 'N/A')}")
        print(f"業界: {info.get('industry', 'N/A')}")
        print(f"セクター: {info.get('sector', 'N/A')}")
    
    # 価格情報
    if data['price']:
        price = data['price']
        print(f"\n--- 価格情報 ---")
        print(f"現在価格: {price['current_price']} {price['currency']}")
        if 'price_change' in price:
            direction = "↑" if price['price_change_direction'] == 'up' else "↓" if price['price_change_direction'] == 'down' else "→"
            print(f"変化: {price['price_change']:+.2f} ({price['price_change_percent']:+.2f}%) {direction}")
    
    # ISIN
    if data['isin'] and not isinstance(data['isin'], str) or not data['isin'].startswith('ISIN'):
        print(f"\n--- 証券情報 ---")
        print(f"ISIN: {data['isin']}")
    
    # ESG情報
    if data['sustainability'] and isinstance(data['sustainability'], dict) and 'esgScores' in data['sustainability']:
        esg = data['sustainability']['esgScores']
        print(f"\n--- ESG情報 ---")
        print(f"ESG総合スコア: {esg.get('totalEsg', 'N/A')}")
        print(f"環境スコア: {esg.get('environmentScore', 'N/A')}")
        print(f"社会スコア: {esg.get('socialScore', 'N/A')}")
        print(f"ガバナンススコア: {esg.get('governanceScore', 'N/A')}")
        print(f"ESGパフォーマンス: {esg.get('esgPerformance', 'N/A')}")
    
    # 株主情報
    if data['holders'] and isinstance(data['holders'], dict):
        if data['holders']['major_holders']:
            print(f"\n--- 大株主情報 ---")
            for i, holder in enumerate(data['holders']['major_holders'][:5], 1):
                if isinstance(holder, dict):
                    print(f"{i}. {holder.get('Holder', 'N/A')}: {holder.get('Shares', 'N/A')}")
    
    # 財務情報の概要
    if data['financials'] and isinstance(data['financials'], dict):
        income = data['financials'].get('income_statement', {})
        if income and isinstance(income, dict):
            print(f"\n--- 財務情報（概要）---")
            # 売上高を探す
            revenue_keys = ['Total Revenue', 'Revenue', 'Net Sales']
            for key in revenue_keys:
                if key in income:
                    revenue_data = income[key]
                    if isinstance(revenue_data, dict):
                        latest_revenue = list(revenue_data.values())[0] if revenue_data.values() else None
                        if latest_revenue:
                            print(f"売上高: {latest_revenue:,.0f}" if isinstance(latest_revenue, (int, float)) else f"売上高: {latest_revenue}")
                    break
    
    # 履歴データの概要
    if data['history'] and isinstance(data['history'], list) and len(data['history']) > 0:
        print(f"\n--- 株価履歴（直近5日）---")
        recent_data = data['history'][-5:] if len(data['history']) >= 5 else data['history']
        for day in recent_data:
            print(f"{day['date']}: 終値 {day['close']} (出来高: {day['volume']:,})")

def display_basic_info(ticker):
    """基本的な株式情報を表示（包括的データから抽出）"""
    data = get_comprehensive_info(ticker)
    if 'error' in data:
        print(f"エラー: {data['error']}")
        return
    
    print(f"\n=== {ticker} の基本情報 ===")
    
    # 基本情報
    if data['info']:
        info = data['info']
        print(f"会社名: {info.get('longName', 'N/A')}")
        print(f"業界: {info.get('industry', 'N/A')}")
        print(f"セクター: {info.get('sector', 'N/A')}")
    
    # 価格情報
    if data['price']:
        price = data['price']
        print(f"現在価格: {price['current_price']} {price['currency']}")
        if 'previous_close' in price:
            print(f"前日終値: {price['previous_close']} {price['currency']}")
    
    # 基本的な財務指標
    if data['info']:
        info = data['info']
        market_cap = info.get('marketCap', 'N/A')
        if isinstance(market_cap, (int, float)):
            print(f"時価総額: {market_cap:,}")
        else:
            print(f"時価総額: {market_cap}")
        
        print(f"配当利回り: {info.get('dividendYield', 'N/A')}")
        print(f"P/E比率: {info.get('trailingPE', 'N/A')}")
        print(f"52週高値: {info.get('fiftyTwoWeekHigh', 'N/A')}")
        print(f"52週安値: {info.get('fiftyTwoWeekLow', 'N/A')}")

def get_basic_info_json(ticker):
    """基本情報をJSON形式で取得"""
    data = get_comprehensive_info(ticker)
    if 'error' in data:
        return {'error': data['error']}
    
    # 基本情報のみを抽出
    result = {
        'symbol': ticker,
        'name': data['info'].get('longName', 'N/A') if data['info'] else 'N/A',
        'currentPrice': data['price']['current_price'] if data['price'] else 'N/A',
        'currency': data['price']['currency'] if data['price'] else 'N/A',
        'previousClose': data['price'].get('previous_close', 'N/A') if data['price'] else 'N/A',
        'marketCap': data['info'].get('marketCap', 'N/A') if data['info'] else 'N/A',
        'dividendYield': data['info'].get('dividendYield', 'N/A') if data['info'] else 'N/A',
        'trailingPE': data['info'].get('trailingPE', 'N/A') if data['info'] else 'N/A',
        'fiftyTwoWeekHigh': data['info'].get('fiftyTwoWeekHigh', 'N/A') if data['info'] else 'N/A',
        'fiftyTwoWeekLow': data['info'].get('fiftyTwoWeekLow', 'N/A') if data['info'] else 'N/A'
    }
    return result

def main():
    parser = argparse.ArgumentParser(description='YFinance CLI Tool - 金融データの取得と表示')
    parser.add_argument('ticker', nargs='?', help='株式のティッカーシンボル（例：AAPL, MSFT, 7203.T）')
    
    # アクションのオプション
    parser.add_argument('-s', '--search', type=str, metavar='QUERY', 
                       help='株式を検索（例：-s Apple, -s AAPL）')
    parser.add_argument('-c', '--comprehensive', action='store_true',
                       help='包括的な情報を取得（価格、ESG、財務諸表、株主情報など全17種類のデータ）')
    
    # 地域オプション
    parser.add_argument('-r', '--region', type=str, default='US',
                       choices=['US', 'CA', 'AU', 'DE', 'FR', 'GB', 'IT', 'ES', 'KR', 'JP', 'IN', 'HK', 'SG'],
                       help='検索地域を指定（デフォルト：US）')
    
    # 出力オプション
    parser.add_argument('-j', '--json', action='store_true',
                       help='JSON形式で出力')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='詳細な出力')
    
    args = parser.parse_args()
    
    # 引数の検証 - 検索モードの場合はtickerは不要
    if not args.search and not args.ticker:
        parser.print_help()
        print("\n使用例:")
        print("  基本情報取得:        python yfinance_cli.py AAPL")
        print("  包括的情報取得:      python yfinance_cli.py AAPL -c")
        print("  株式検索:           python yfinance_cli.py -s Apple")
        print("  地域指定検索:        python yfinance_cli.py -s Toyota -r JP")
        print("  JSON出力:           python yfinance_cli.py AAPL -c -j")
        return
    
    try:
        # 検索モード
        if args.search:
            if args.verbose:
                print(f"検索中: '{args.search}' (地域: {args.region})")
            
            results = search_stocks(args.search, region=args.region)
            
            if args.json:
                print(json.dumps(results, ensure_ascii=False, indent=2))
            else:
                display_search_results(results)
        
        # 株式情報取得モード
        elif args.ticker:
            ticker = args.ticker.upper()
            
            if args.comprehensive:
                if args.verbose:
                    print(f"包括的情報を取得中: {ticker}")
                
                data = get_comprehensive_info(ticker)
                
                if args.json:
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                else:
                    display_comprehensive_info(data)
            
            else:  # デフォルトは基本情報
                if args.verbose:
                    print(f"基本情報を取得中: {ticker}")
                
                if args.json:
                    info = get_basic_info_json(ticker)
                    print(json.dumps(info, ensure_ascii=False, indent=2))
                else:
                    display_basic_info(ticker)
    
    except KeyboardInterrupt:
        print("\n操作がキャンセルされました。")
    except Exception as e:
        if args.verbose:
            import traceback
            traceback.print_exc()
        else:
            print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main() 