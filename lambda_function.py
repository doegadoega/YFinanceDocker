import json
import yfinance as yf
from datetime import datetime
import traceback
import os
import pandas as pd
import numpy as np
from typing import Union, Dict, Any, Optional
import feedparser
import hashlib
import re

# ... 既存のimport文の下に追加 ...
BULLISH_THRESHOLD = 0.5
BEARISH_THRESHOLD = -0.5

# RSSフィードソース設定
RSS_SOURCES = [
    {
        'name': 'Yahoo Finance',
        'url': 'https://finance.yahoo.com/rss/2.0',
        'category': 'general'
    },
    {
        'name': 'MarketWatch Top Stories',
        'url': 'https://www.marketwatch.com/rss/topstories',
        'category': 'market'
    }
]

def get_price_change_direction(price_change):
    if price_change is None:
        return "unchanged"
    if price_change > 0:
        return "up"
    elif price_change < 0:
        return "down"
    else:
        return "unchanged"

def get_market_sentiment(avg_change):
    if avg_change > BULLISH_THRESHOLD:
        return "bullish"
    elif avg_change < BEARISH_THRESHOLD:
        return "bearish"
    else:
        return "neutral"

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
        # インデックスを文字列に変換してから辞書化
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

def format_currency(value: Union[int, float, str], currency: str = "USD") -> str:
    """
    通貨を適切にフォーマット（共通関数）
    
    Args:
        value: 数値
        currency: 通貨コード
    
    Returns:
        str: フォーマットされた通貨文字列
    """
    if value is None or value == "N/A":
        return "N/A"
    
    try:
        value = float(value)
        if currency == "JPY":
            return f"¥{value:,.0f}"
        elif currency == "USD":
            return f"${value:,.2f}"
        else:
            return f"{value:,.2f} {currency}"
    except (ValueError, TypeError):
        return str(value)

def get_execution_info(mode: str = "LAMBDA") -> Dict[str, str]:
    """実行環境の情報を取得（共通関数）"""
    return {
        'mode': mode,
        'timestamp': datetime.now().isoformat(),
        'server': 'lambda'
    }

def validate_ticker_parameter(query_parameters, headers):
    """ティッカーパラメータのバリデーション（共通化）"""
    ticker = query_parameters.get('ticker', '').upper()
    if not ticker:
        return None, {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': 'ティッカーシンボルが必要です'})
        }
    return ticker, None

def display_stock_info_local(ticker: str) -> None:
    """
    株式の基本情報をローカルで表示（共通関数）
    
    Args:
        ticker (str): ティッカーシンボル
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        print(f"\n=== {ticker} の基本情報（ローカル取得）===")
        print(f"会社名: {info.get('longName', 'N/A')}")
        print(f"業界: {info.get('industry', 'N/A')}")
        print(f"セクター: {info.get('sector', 'N/A')}")
        
        # 価格情報の安全な表示
        current_price = info.get('currentPrice')
        if current_price is not None:
            currency = "JPY" if ticker.endswith('.T') else "USD"
            print(f"現在価格: {format_currency(current_price, currency)}")
        else:
            print("現在価格: N/A")
        
        # 時価総額の安全な表示
        market_cap = info.get('marketCap')
        if market_cap is not None:
            currency = "JPY" if ticker.endswith('.T') else "USD"
            print(f"時価総額: {format_currency(market_cap, currency)}")
        else:
            print("時価総額: N/A")
        
        # 配当利回りの安全な表示
        dividend_yield = info.get('dividendYield')
        if dividend_yield is not None:
            print(f"配当利回り: {dividend_yield:.2%}")
        else:
            print("配当利回り: N/A")
        
    except Exception as e:
        print(f"エラー: {ticker} の情報取得に失敗しました - {e}")

def display_comprehensive_info_api(data: Dict[str, Any]) -> None:
    """
    APIから取得した包括的な株式情報を表示（共通関数）
    
    Args:
        data (dict): API応答データ
    """
    if not data or 'error' in data:
        print(f"エラー: {data.get('error', '不明なエラー')}")
        return
    
    ticker = data.get('ticker', 'N/A')
    print(f"\n=== {ticker} の包括的情報（API取得）===")
    
    # 基本情報
    if data.get('info'):
        info = data['info']
        print(f"会社名: {info.get('longName', 'N/A')}")
        print(f"業界: {info.get('industry', 'N/A')}")
        print(f"セクター: {info.get('sector', 'N/A')}")
        
        # 従業員数の安全な表示
        employees = info.get('fullTimeEmployees')
        if employees is not None:
            print(f"従業員数: {employees:,}")
        else:
            print("従業員数: N/A")
    
    # 価格情報
    if data.get('price'):
        price = data['price']
        print(f"\n--- 価格情報 ---")
        
        current_price = price.get('current_price')
        currency = price.get('currency', 'USD')
        print(f"現在価格: {format_currency(current_price, currency)}")
        
        # 価格変化の安全な表示
        price_change = price.get('price_change')
        if price_change is not None and isinstance(price_change, (int, float)):
            direction = get_price_change_direction(price_change)
            price_change_percent = price.get('price_change_percent', 0)
            print(f"変化: {price_change:+.2f} ({price_change_percent:+.2f}%) {direction}")
    
    # ESG情報
    if data.get('sustainability') and isinstance(data['sustainability'], dict):
        esg = data['sustainability'].get('esgScores', {})
        if esg:
            print(f"\n--- ESG情報 ---")
            print(f"ESG総合スコア: {esg.get('totalEsg', 'N/A')}")
            print(f"環境スコア: {esg.get('environmentScore', 'N/A')}")
            print(f"社会スコア: {esg.get('socialScore', 'N/A')}")
            print(f"ガバナンススコア: {esg.get('governanceScore', 'N/A')}")
    
    # 財務情報
    if data.get('financials') and isinstance(data['financials'], dict):
        income = data['financials'].get('income_statement', {})
        if income:
            print(f"\n--- 財務情報 ---")
            # 売上高を探す
            revenue_keys = ['Total Revenue', 'Revenue', 'Net Sales']
            for key in revenue_keys:
                if key in income:
                    revenue_data = income[key]
                    if isinstance(revenue_data, dict) and revenue_data:
                        latest_revenue = list(revenue_data.values())[0]
                        if latest_revenue is not None:
                            if isinstance(latest_revenue, (int, float)):
                                currency = data.get('price', {}).get('currency', 'USD')
                                print(f"売上高: {format_currency(latest_revenue, currency)}")
                            else:
                                print(f"売上高: {latest_revenue}")
                    break
    
    # 決算情報
    if data.get('earnings') and isinstance(data['earnings'], dict):
        earnings = data['earnings']
        if earnings and not earnings.get('error'):
            print(f"\n--- 決算情報 ---")
            if 'trailingEps' in earnings:
                print(f"過去12ヶ月EPS: {earnings['trailingEps']}")
            if 'forwardEps' in earnings:
                print(f"予想EPS: {earnings['forwardEps']}")
            if 'trailingPE' in earnings:
                print(f"過去12ヶ月P/E比: {earnings['trailingPE']}")
            if 'forwardPE' in earnings:
                print(f"予想P/E比: {earnings['forwardPE']}")
            if 'pegRatio' in earnings:
                print(f"PEGレシオ: {earnings['pegRatio']}")
    
    # 株式分割
    if data.get('splits') and isinstance(data['splits'], list) and data['splits']:
        print(f"\n--- 株式分割履歴 ---")
        for split in data['splits'][:3]:  # 最新3件
            if isinstance(split, dict):
                print(f"日付: {split.get('date')}, 比率: {split.get('ratio')}")
    
    # 配当情報
    if data.get('dividends') and isinstance(data['dividends'], list) and data['dividends']:
        print(f"\n--- 配当履歴 ---")
        for dividend in data['dividends'][:3]:  # 最新3件
            if isinstance(dividend, dict):
                amount = dividend.get('amount', 'N/A')
                if isinstance(amount, (int, float)):
                    currency = data.get('price', {}).get('currency', 'USD')
                    print(f"日付: {dividend.get('date')}, 配当: {format_currency(amount, currency)}")
                else:
                    print(f"日付: {dividend.get('date')}, 配当: {amount}")
    
    # 株主情報
    if data.get('holders') and isinstance(data['holders'], dict):
        holders = data['holders']
        if holders and not holders.get('error'):
            print(f"\n--- 株主情報 ---")
            if holders.get('major_holders') and isinstance(holders['major_holders'], list):
                print("大株主:")
                for holder in holders['major_holders'][:3]:  # 上位3件
                    if isinstance(holder, dict):
                        print(f"  {holder.get('Holder', 'N/A')}: {holder.get('% of Shares', 'N/A')}%")
    
    # ESG情報
    if data.get('sustainability') and isinstance(data['sustainability'], dict):
        sustainability = data['sustainability']
        if sustainability and not sustainability.get('error'):
            esg = sustainability.get('esgScores', {})
            if esg:
                print(f"\n--- ESG情報 ---")
                print(f"ESG総合スコア: {esg.get('totalEsg', 'N/A')}")
                print(f"環境スコア: {esg.get('environmentScore', 'N/A')}")
                print(f"社会スコア: {esg.get('socialScore', 'N/A')}")
                print(f"ガバナンススコア: {esg.get('governanceScore', 'N/A')}")
    
    # アナリスト推奨履歴
    if data.get('recommendations') and isinstance(data['recommendations'], list) and data['recommendations']:
        print(f"\n--- アナリスト推奨履歴 ---")
        for rec in data['recommendations'][:3]:  # 最新3件
            if isinstance(rec, dict):
                print(f"日付: {rec.get('Date', 'N/A')}, 推奨: {rec.get('To Grade', 'N/A')}")
    
    # 決算日
    if data.get('earnings_dates') and isinstance(data['earnings_dates'], list) and data['earnings_dates']:
        print(f"\n--- 決算日 ---")
        for date_info in data['earnings_dates'][:3]:  # 最新3件
            if isinstance(date_info, dict):
                print(f"日付: {date_info.get('Earnings Date', 'N/A')}, EPS予想: {date_info.get('EPS Estimate', 'N/A')}")
    
    # 株価履歴
    if data.get('history') and isinstance(data['history'], list):
        print(f"\n--- 直近の株価履歴 ---")
        recent_data = data['history'][-5:] if len(data['history']) >= 5 else data['history']
        for day in recent_data:
            close_price = day.get('close', 'N/A')
            volume = day.get('volume', 0)
            if isinstance(volume, (int, float)):
                volume_str = f"{volume:,}"
            else:
                volume_str = str(volume)
            print(f"{day.get('date', 'N/A')}: 終値 {close_price} (出来高: {volume_str})")
    
    # アナリスト情報
    if data.get('analysts') and isinstance(data['analysts'], dict):
        analysts = data['analysts']
        print(f"\n--- アナリスト情報 ---")
        if analysts.get('recommendation_mean'):
            print(f"推奨平均: {analysts['recommendation_mean']}")
        if analysts.get('target_mean_price'):
            print(f"目標平均価格: {analysts['target_mean_price']}")
        if analysts.get('number_of_analysts'):
            print(f"アナリスト数: {analysts['number_of_analysts']}")
    
    # ニュース情報
    if data.get('news') and isinstance(data['news'], list) and len(data['news']) > 0:
        print(f"\n--- 最新ニュース ---")
        for i, news_item in enumerate(data['news'][:3], 1):  # 最新3件
            if isinstance(news_item, dict):
                title = news_item.get('title', 'N/A')
                print(f"{i}. {title}")
    
    # 実行環境情報
    if data.get('execution_info'):
        exec_info = data['execution_info']
        print(f"\n--- 実行環境情報 ---")
        print(f"実行モード: {exec_info.get('mode', 'N/A')}")
        print(f"実行時刻: {exec_info.get('timestamp', 'N/A')}")

def display_search_results_api(results: Dict[str, Any]) -> None:
    """
    API検索結果を表示（共通関数）
    
    Args:
        results (dict): 検索結果
    """
    if not results or 'error' in results:
        print(f"検索エラー: {results.get('error', '不明なエラー')}")
        return
    
    print(f"\n=== 検索結果: '{results.get('query', 'N/A')}' ({results.get('region', 'N/A')}) ===")
    print(f"件数: {results.get('count', 0)}")
    
    for i, result in enumerate(results.get('results', []), 1):
        print(f"\n{i}. {result.get('symbol', 'N/A')} - {result.get('name', 'N/A')}")
        print(f"   取引所: {result.get('exchange', 'N/A')} | タイプ: {result.get('type', 'N/A')}")
        
        # 価格情報の安全な表示
        current_price = result.get('current_price')
        if current_price is not None:
            currency = result.get('currency', 'USD')
            price_info = f"   価格: {format_currency(current_price, currency)}"
            
            # 価格変化の安全な表示
            price_change = result.get('price_change')
            if price_change is not None and isinstance(price_change, (int, float)):
                direction = get_price_change_direction(price_change)
                price_change_percent = result.get('price_change_percent', 0)
                price_info += f" ({price_change:+.2f}, {price_change_percent:+.2f}% {direction})"
            print(price_info)
        
        # エラー情報の表示
        if result.get('price_error'):
            print(f"   価格取得エラー: {result['price_error']}")
    
    # 実行環境情報
    if results.get('execution_info'):
        exec_info = results['execution_info']
        print(f"\n--- 実行環境情報 ---")
        print(f"実行モード: {exec_info.get('mode', 'N/A')}")
        print(f"実行時刻: {exec_info.get('timestamp', 'N/A')}")

def lambda_handler(event, context):
    """
    AWS Lambda メインハンドラー
    API Gateway からのリクエストを処理
    """
    try:
        # CORS ヘッダーを設定
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        
        # OPTIONSリクエスト（CORS プリフライト）への対応
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'OK'})
            }
        
        # パスとメソッドを取得
        resource = event.get('resource', '')
        method = event.get('httpMethod', '')
        path_parameters = event.get('pathParameters', {})
        query_parameters = event.get('queryStringParameters', {}) or {}
        
        # ベースURL（/）へのアクセス - Swagger UIを表示
        if resource == '/' or resource == '':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'text/html',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': generate_swagger_ui_html(event, context)
            }
        
        # リソースごとの処理
        if '/search' in resource:
            query = query_parameters.get('q', '')
            if not query:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': '検索クエリが必要です'})
                }
            result = search_stocks_api(query, query_parameters)
        elif '/tickerDetail' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            # periodパラメータも受け取る（history用）
            period = query_parameters.get('period', '1mo')
            result = get_stock_info_api(ticker, period)
        elif '/ticker/basic' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            result = get_stock_basic_info_api(ticker)
        elif '/ticker/price' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            result = get_stock_price_api(ticker)
        elif '/ticker/history' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            period = query_parameters.get('period', '1mo')
            result = get_stock_history_api(ticker, period)
        elif '/ticker/financials' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            result = get_stock_financials_api(ticker)
        elif '/ticker/analysts' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            result = get_stock_analysts_api(ticker)
        elif '/ticker/holders' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            result = get_stock_holders_api(ticker)
        elif '/ticker/events' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            result = get_stock_events_api(ticker)
        elif '/ticker/news' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            result = get_stock_news_api(ticker)
        elif '/ticker/options' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            result = get_stock_options_api(ticker)
        elif '/ticker/sustainability' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            result = get_stock_sustainability_api(ticker)
        elif '/chart' in resource:
            ticker = query_parameters.get('ticker', '').upper()
            if not ticker:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'ティッカーシンボルが必要です'})
                }
            period = query_parameters.get('period', '1mo')
            size = query_parameters.get('size', '800x400')
            chart_type = query_parameters.get('type', 'line')
            # 画像はBase64バイナリで返却
            chart_base64, err = get_stock_chart_api(ticker, period, size, chart_type)
            if err:
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': err})
                }
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'image/png',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': chart_base64,
                'isBase64Encoded': True
            }
        elif '/home' in resource:
            result = get_stock_home_api()
        elif '/news/rss' in resource:
            result = lamuda_get_rss_news_api(query_parameters)
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'リソースが見つかりません'})
            }
        
        if result.get('error'):
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps(result)
            }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(result, default=serialize_for_json)
        }
        
    except Exception as e:
        print(f"Lambda Error: {str(e)}")
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': '内部サーバーエラーが発生しました',
                'details': str(e)
            })
        }


def search_stocks_api(query, query_parameters):
    """銘柄検索（API用）- 株価情報付き"""
    try:
        import requests
        
        # 検索結果を10件に制限
        limit = min(int(query_parameters.get('limit', 10)), 10)
        region = query_parameters.get('region', 'US')
        
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
            for quote in data['quotes'][:10]:  # 最大10件に制限
                symbol = quote.get('symbol', '')
                
                # 基本情報
                result = {
                    'symbol': symbol,
                    'name': quote.get('longname', quote.get('shortname', '')),
                    'exchange': quote.get('exchange', ''),
                    'type': quote.get('quoteType', ''),
                    'score': quote.get('score', 0),
                    'timestamp': datetime.now().isoformat()
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
                        
                        # 前日との差分を計算
                        if previous_close is not None:
                            previous_close = float(previous_close)
                            price_change = current_price - previous_close
                            price_change_percent = (price_change / previous_close) * 100
                            
                            result['previous_close'] = round(previous_close, 2)
                            result['price_change'] = round(price_change, 2)
                            result['price_change_percent'] = round(price_change_percent, 2)
                            result['price_change_direction'] = get_price_change_direction(price_change)
                        
                        # 追加情報
                        result['market_cap'] = info.get('marketCap')
                        result['volume'] = info.get('volume')
                        result['avg_volume'] = info.get('averageVolume')
                        
                except Exception as e:
                    # 株価取得に失敗した場合でも基本情報は返す
                    result['price_error'] = f'株価取得エラー: {str(e)}'
                
                results.append(result)
            
            return {
                'query': query,
                'region': region,
                'results': results,
                'count': len(results),
                'max_results': 10,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'query': query,
                'region': region,
                'results': [],
                'count': 0,
                'max_results': 10,
                'message': '検索結果が見つかりませんでした',
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        return {'error': f'検索エラー: {str(e)}'}


def get_stock_info_api(ticker, period='1mo'):
    """包括的な株式情報取得API（統合版）- 各要素専用関数を呼び出し"""
    try:
        # 各要素専用の関数を呼び出して統合
        basic_info = get_stock_basic_info_api(ticker)
        price_info = get_stock_price_api(ticker)
        history_info = get_stock_history_api(ticker, period)
        financials_info = get_stock_financials_api(ticker)
        analysts_info = get_stock_analysts_api(ticker)
        holders_info = get_stock_holders_api(ticker)
        events_info = get_stock_events_api(ticker)
        news_info = get_stock_news_api(ticker)
        options_info = get_stock_options_api(ticker)
        sustainability_info = get_stock_sustainability_api(ticker)
        
        # 統合結果を作成
        result = {
            'ticker': ticker,
            'period': period,
            # 基本情報
            'info': basic_info.get('info', {}),
            'info_error': basic_info.get('info_error'),
            'fast_info': basic_info.get('fast_info', {}),
            'logo_url': basic_info.get('logo_url'),
            'isin': basic_info.get('isin'),
            # 株価情報
            'price': price_info.get('price'),
            # 履歴情報
            'history': history_info.get('history', []),
            # 財務情報
            'financials': financials_info.get('financials', {}),
            'earnings': financials_info.get('earnings', {}),
            # アナリスト情報
            'analysts': analysts_info.get('analysts', {}),
            'recommendations': analysts_info.get('recommendations', []),
            'analysis': analysts_info.get('analysis', {}),
            'upgrades_downgrades': analysts_info.get('upgrades_downgrades', []),
            # 株主情報
            'holders': holders_info.get('holders', {}),
            'shares': holders_info.get('shares', {}),
            # イベント情報
            'calendar': events_info.get('calendar', []),
            'earnings_dates': events_info.get('earnings_dates', []),
            'dividends': events_info.get('dividends', []),
            'splits': events_info.get('splits', []),
            # ニュース情報
            'news': news_info.get('news', []),
            # オプション情報
            'options': options_info.get('options', []),
            # ESG情報
            'sustainability': sustainability_info.get('sustainability', {}),
            # 実行情報
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        
        # エラーがある場合は統合
        errors = []
        for name, data in [
            ('基本情報', basic_info),
            ('株価情報', price_info),
            ('履歴情報', history_info),
            ('財務情報', financials_info),
            ('アナリスト情報', analysts_info),
            ('株主情報', holders_info),
            ('イベント情報', events_info),
            ('ニュース情報', news_info),
            ('オプション情報', options_info),
            ('ESG情報', sustainability_info)
        ]:
            if data.get('error'):
                errors.append(f"{name}: {data['error']}")
        
        if errors:
            result['partial_errors'] = errors
        
        return result
        
    except Exception as e:
        return {'error': f'銘柄情報取得エラー: {str(e)}'}

def get_stock_basic_info_api(ticker):
    """基本情報取得API"""
    try:
        stock = yf.Ticker(ticker)
        
        # 詳細情報
        try:
            info = stock.get_info()
            if not info or info.empty:
                info = {}
                info_error = "詳細情報が取得できませんでした"
            else:
                info_error = None
        except Exception as e:
            info = {}
            info_error = f"詳細情報取得エラー: {str(e)}"

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

        # ロゴURL
        logo_url = None
        try:
            logo_url = info.get('logo_url') if info else None
            if not logo_url:
                website = info.get('website') if info else None
                if website:
                    import re
                    m = re.search(r'https?://([^/]+)', website)
                    if m:
                        logo_url = f"https://logo.clearbit.com/{m.group(1)}"
        except Exception as e:
            logo_url = None

        # ISIN
        isin = None
        try:
            isin = stock.get_isin()
        except Exception as e:
            isin = {'error': f'ISIN取得エラー: {str(e)}'}

        result = {
            'ticker': ticker,
            'info': info,
            'info_error': info_error,
            'fast_info': fast_info,
            'logo_url': logo_url,
            'isin': isin,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'基本情報取得エラー: {str(e)}'}

def get_stock_price_api(ticker):
    """株価情報取得API"""
    try:
        stock = yf.Ticker(ticker)
        
        # 詳細情報と高速情報を取得
        try:
            info = stock.get_info()
        except:
            info = {}
        
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
        except:
            fast_info = {}

        # 株価情報
        price = None
        try:
            current_price = fast_info.get('last_price') or info.get('currentPrice') if info else None
            previous_close = fast_info.get('previous_close') or info.get('previousClose') if info else None
            
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
                    price['price_change_direction'] = get_price_change_direction(diff)
        except Exception as e:
            price = {'error': f'価格情報取得エラー: {str(e)}'}

        result = {
            'ticker': ticker,
            'price': price,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'株価情報取得エラー: {str(e)}'}

def get_stock_history_api(ticker, period='1mo'):
    """株価履歴取得API"""
    try:
        stock = yf.Ticker(ticker)
        
        # 履歴
        history = []
        try:
            valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
            if period not in valid_periods:
                period = '1mo'
            
            hist_df = stock.history(period=period)
            if not hist_df.empty:
                history = [{
                    'date': idx.strftime('%Y-%m-%d'),
                    'open': round(float(row['Open']), 2),
                    'high': round(float(row['High']), 2),
                    'low': round(float(row['Low']), 2),
                    'close': round(float(row['Close']), 2),
                    'volume': int(row['Volume'])
                } for idx, row in hist_df.iterrows()]
        except Exception as e:
            history = {'error': f'履歴データ取得エラー: {str(e)}'}

        result = {
            'ticker': ticker,
            'period': period,
            'history': history,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'株価履歴取得エラー: {str(e)}'}

def get_stock_financials_api(ticker):
    """財務情報取得API"""
    try:
        stock = yf.Ticker(ticker)
        
        # 財務諸表
        financials = {}
        try:
            # 損益計算書
            income_stmt = stock.get_income_stmt()
            if not income_stmt.empty:
                income_stmt_data = safe_dataframe_to_dict(income_stmt)
            else:
                income_stmt_data = {}
            
            # 貸借対照表
            balance_sheet = stock.get_balance_sheet()
            if not balance_sheet.empty:
                balance_sheet_data = safe_dataframe_to_dict(balance_sheet)
            else:
                balance_sheet_data = {}
            
            # キャッシュフロー
            cashflow = stock.get_cashflow()
            if not cashflow.empty:
                cashflow_data = safe_dataframe_to_dict(cashflow)
            else:
                cashflow_data = {}
                
            financials = {
                'income_statement': income_stmt_data,
                'balance_sheet': balance_sheet_data,
                'cashflow': cashflow_data
            }
        except Exception as e:
            financials = {'error': f'財務情報取得エラー: {str(e)}'}

        # 決算情報
        earnings = {}
        try:
            info = stock.get_info()
            if info:
                earnings_keys = ['trailingEps', 'forwardEps', 'trailingPE', 'forwardPE', 'pegRatio']
                for key in earnings_keys:
                    if key in info and info[key] is not None:
                        earnings[key] = info[key]
        except Exception as e:
            earnings = {'error': f'決算情報取得エラー: {str(e)}'}

        result = {
            'ticker': ticker,
            'financials': financials,
            'earnings': earnings,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'財務情報取得エラー: {str(e)}'}

def get_stock_analysts_api(ticker):
    """アナリスト情報取得API"""
    try:
        stock = yf.Ticker(ticker)
        
        # アナリスト予想
        analysts = {}
        try:
            info = stock.get_info()
            if info:
                if 'recommendationMean' in info:
                    analysts['recommendation_mean'] = info['recommendationMean']
                if 'targetMeanPrice' in info:
                    analysts['target_mean_price'] = info['targetMeanPrice']
                if 'numberOfAnalystOpinions' in info:
                    analysts['number_of_analysts'] = info['numberOfAnalystOpinions']
                keys = ['strongBuy', 'buy', 'hold', 'sell', 'strongSell']
                ratings = {k: info[k] for k in keys if k in info}
                if ratings:
                    analysts['rating_distribution'] = ratings
        except Exception as e:
            analysts = {'error': f'アナリスト予想取得エラー: {str(e)}'}

        # アナリスト推奨履歴
        recommendations_data = []
        try:
            recommendations = stock.get_recommendations()
            if not recommendations.empty:
                recommendations_data = safe_dataframe_to_records(recommendations)
        except Exception as e:
            recommendations_data = {'error': f'推奨履歴取得エラー: {str(e)}'}

        # アナリスト分析
        analysis_data = {}
        try:
            analysis = stock.get_analysis()
            if not analysis.empty:
                analysis_data = safe_dataframe_to_dict(analysis)
        except Exception as e:
            analysis_data = {'error': f'アナリスト分析取得エラー: {str(e)}'}

        # 格付け変更履歴
        upgrades_downgrades_data = []
        try:
            upgrades_downgrades = stock.get_upgrades_downgrades()
            if not upgrades_downgrades.empty:
                upgrades_downgrades_data = safe_dataframe_to_records(upgrades_downgrades)
        except Exception as e:
            upgrades_downgrades_data = {'error': f'格付け変更履歴取得エラー: {str(e)}'}

        result = {
            'ticker': ticker,
            'analysts': analysts,
            'recommendations': recommendations_data,
            'analysis': analysis_data,
            'upgrades_downgrades': upgrades_downgrades_data,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'アナリスト情報取得エラー: {str(e)}'}

def get_stock_holders_api(ticker):
    """株主情報取得API"""
    try:
        stock = yf.Ticker(ticker)
        
        # 株主情報
        holders_data = {}
        try:
            # 大株主
            major_holders = stock.get_major_holders()
            if not major_holders.empty:
                major_holders_data = safe_dataframe_to_records(major_holders)
            else:
                major_holders_data = []
                
            # 機関投資家
            institutional_holders = stock.get_institutional_holders()
            if not institutional_holders.empty:
                institutional_holders_data = safe_dataframe_to_records(institutional_holders)
            else:
                institutional_holders_data = []
                
            # 投資信託
            mutualfund_holders = stock.get_mutualfund_holders()
            if not mutualfund_holders.empty:
                mutualfund_holders_data = safe_dataframe_to_records(mutualfund_holders)
            else:
                mutualfund_holders_data = []
                
            holders_data = {
                'major_holders': major_holders_data,
                'institutional_holders': institutional_holders_data,
                'mutualfund_holders': mutualfund_holders_data
            }
        except Exception as e:
            holders_data = {'error': f'株主情報取得エラー: {str(e)}'}

        # 株式数詳細
        shares_data = {}
        try:
            shares = stock.get_shares()
            if not shares.empty:
                shares_data = safe_dataframe_to_dict(shares)
        except Exception as e:
            shares_data = {'error': f'株式数取得エラー: {str(e)}'}

        result = {
            'ticker': ticker,
            'holders': holders_data,
            'shares': shares_data,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'株主情報取得エラー: {str(e)}'}

def get_stock_events_api(ticker):
    """イベント情報取得API"""
    try:
        stock = yf.Ticker(ticker)
        
        # カレンダー（決算日など）
        calendar_data = []
        try:
            calendar = stock.get_calendar()
            if not calendar.empty:
                calendar_data = safe_dataframe_to_records(calendar)
        except Exception as e:
            calendar_data = {'error': f'カレンダー取得エラー: {str(e)}'}

        # 決算日
        earnings_dates_data = []
        try:
            earnings_dates = stock.get_earnings_dates()
            if not earnings_dates.empty:
                earnings_dates_data = safe_dataframe_to_records(earnings_dates)
        except Exception as e:
            earnings_dates_data = {'error': f'決算日取得エラー: {str(e)}'}

        # 配当
        dividends = []
        try:
            dividends_series = stock.get_dividends()
            if not dividends_series.empty:
                dividends = [{
                    'date': idx.strftime('%Y-%m-%d'),
                    'amount': float(val)
                } for idx, val in dividends_series.items()]
        except Exception as e:
            dividends = {'error': f'配当情報取得エラー: {str(e)}'}

        # 株式分割
        splits = []
        try:
            splits_series = stock.get_splits()
            if not splits_series.empty:
                splits = [{
                    'date': idx.strftime('%Y-%m-%d'),
                    'ratio': float(val)
                } for idx, val in splits_series.items()]
        except Exception as e:
            splits = {'error': f'株式分割取得エラー: {str(e)}'}

        result = {
            'ticker': ticker,
            'calendar': calendar_data,
            'earnings_dates': earnings_dates_data,
            'dividends': dividends,
            'splits': splits,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'イベント情報取得エラー: {str(e)}'}

def get_stock_news_api(ticker):
    """ニュース情報取得API"""
    try:
        stock = yf.Ticker(ticker)
        
        # ニュース
        news = []
        try:
            news_data = stock.get_news()
            if news_data and not news_data.empty:
                news = safe_dataframe_to_records(news_data)
            elif isinstance(news_data, list):
                news = news_data
        except Exception as e:
            news = {'error': f'ニュース取得エラー: {str(e)}'}

        result = {
            'ticker': ticker,
            'news': news,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'ニュース情報取得エラー: {str(e)}'}

def get_stock_options_api(ticker):
    """オプション情報取得API"""
    try:
        stock = yf.Ticker(ticker)
        
        # オプション
        options_data = []
        try:
            options_dates = stock.options
            if options_dates:
                expiry = options_dates[0]
                chain = stock.option_chain(expiry)
                calls_data = [{
                    'strike': float(r['strike']),
                    'last_price': float(r['lastPrice']),
                    'bid': float(r['bid']),
                    'ask': float(r['ask']),
                    'volume': int(r['volume']),
                    'open_interest': int(r['openInterest'])
                } for _, r in chain.calls.iterrows()]
                puts_data = [{
                    'strike': float(r['strike']),
                    'last_price': float(r['lastPrice']),
                    'bid': float(r['bid']),
                    'ask': float(r['ask']),
                    'volume': int(r['volume']),
                    'open_interest': int(r['openInterest'])
                } for _, r in chain.puts.iterrows()]
                options_data = {'expiry_date': expiry, 'calls': calls_data, 'puts': puts_data}
        except Exception as e:
            options_data = {'error': f'オプション情報取得エラー: {str(e)}'}

        result = {
            'ticker': ticker,
            'options': options_data,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'オプション情報取得エラー: {str(e)}'}

def get_stock_sustainability_api(ticker):
    """ESG情報取得API"""
    try:
        stock = yf.Ticker(ticker)
        
        # ESG情報
        sustainability_data = {}
        try:
            sustainability = stock.get_sustainability()
            if not sustainability.empty:
                sustainability_data = safe_dataframe_to_dict(sustainability)
        except Exception as e:
            sustainability_data = {'error': f'ESG情報取得エラー: {str(e)}'}

        result = {
            'ticker': ticker,
            'sustainability': sustainability_data,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'ESG情報取得エラー: {str(e)}'}

def get_stock_home_api():
    """ホーム画面用情報取得API - 株価指数、主要ETF、セクター情報"""
    try:
        # 主要な株価指数
        indices = {}
        try:
            index_symbols = {
                'SPY': 'S&P 500 ETF',
                'QQQ': 'NASDAQ-100 ETF', 
                'IWM': 'Russell 2000 ETF',
                'DIA': 'Dow Jones ETF',
                'VTI': 'Total Stock Market ETF',
                'VEA': 'Developed Markets ETF',
                'VWO': 'Emerging Markets ETF',
                'BND': 'Total Bond Market ETF',
                'GLD': 'Gold ETF',
                'USO': 'Crude Oil ETF'
            }
            
            for symbol, name in index_symbols.items():
                try:
                    stock = yf.Ticker(symbol)
                    info = stock.get_info()
                    fast_info = stock.get_fast_info()
                    
                    # 価格情報
                    current_price = None
                    previous_close = None
                    price_change = None
                    price_change_percent = None
                    
                    if hasattr(fast_info, 'last_price') and fast_info.last_price:
                        current_price = float(fast_info.last_price)
                    elif info and 'currentPrice' in info:
                        current_price = float(info['currentPrice'])
                    
                    if hasattr(fast_info, 'previous_close') and fast_info.previous_close:
                        previous_close = float(fast_info.previous_close)
                    elif info and 'previousClose' in info:
                        previous_close = float(info['previousClose'])
                    
                    if current_price and previous_close:
                        price_change = current_price - previous_close
                        price_change_percent = (price_change / previous_close) * 100
                    
                    indices[symbol] = {
                        'name': name,
                        'current_price': round(current_price, 2) if current_price else None,
                        'previous_close': round(previous_close, 2) if previous_close else None,
                        'price_change': round(price_change, 2) if price_change is not None else None,
                        'price_change_percent': round(price_change_percent, 2) if price_change_percent is not None else None,
                        'price_change_direction': get_price_change_direction(price_change),
                        'currency': 'USD'
                    }
                except Exception as e:
                    indices[symbol] = {
                        'name': name,
                        'error': f'データ取得エラー: {str(e)}'
                    }
        except Exception as e:
            indices = {'error': f'指数情報取得エラー: {str(e)}'}

        # セクター別ETF
        sectors = {}
        try:
            sector_etfs = {
                'XLK': {'name': 'Technology Select Sector ETF', 'sector': 'Technology'},
                'XLF': {'name': 'Financial Select Sector ETF', 'sector': 'Financial'},
                'XLE': {'name': 'Energy Select Sector ETF', 'sector': 'Energy'},
                'XLV': {'name': 'Health Care Select Sector ETF', 'sector': 'Healthcare'},
                'XLI': {'name': 'Industrial Select Sector ETF', 'sector': 'Industrial'},
                'XLP': {'name': 'Consumer Staples Select Sector ETF', 'sector': 'Consumer Staples'},
                'XLY': {'name': 'Consumer Discretionary Select Sector ETF', 'sector': 'Consumer Discretionary'},
                'XLU': {'name': 'Utilities Select Sector ETF', 'sector': 'Utilities'},
                'XLRE': {'name': 'Real Estate Select Sector ETF', 'sector': 'Real Estate'},
                'XLB': {'name': 'Materials Select Sector ETF', 'sector': 'Materials'},
                'XLC': {'name': 'Communication Services Select Sector ETF', 'sector': 'Communication Services'}
            }
            
            for symbol, info in sector_etfs.items():
                try:
                    stock = yf.Ticker(symbol)
                    stock_info = stock.get_info()
                    fast_info = stock.get_fast_info()
                    
                    # 価格情報
                    current_price = None
                    previous_close = None
                    price_change = None
                    price_change_percent = None
                    
                    if hasattr(fast_info, 'last_price') and fast_info.last_price:
                        current_price = float(fast_info.last_price)
                    elif stock_info and 'currentPrice' in stock_info:
                        current_price = float(stock_info['currentPrice'])
                    
                    if hasattr(fast_info, 'previous_close') and fast_info.previous_close:
                        previous_close = float(fast_info.previous_close)
                    elif stock_info and 'previousClose' in stock_info:
                        previous_close = float(stock_info['previousClose'])
                    
                    if current_price and previous_close:
                        price_change = current_price - previous_close
                        price_change_percent = (price_change / previous_close) * 100
                    
                    sectors[symbol] = {
                        'name': info['name'],
                        'sector': info['sector'],
                        'current_price': round(current_price, 2) if current_price else None,
                        'previous_close': round(previous_close, 2) if previous_close else None,
                        'price_change': round(price_change, 2) if price_change is not None else None,
                        'price_change_percent': round(price_change_percent, 2) if price_change_percent is not None else None,
                        'price_change_direction': get_price_change_direction(price_change),
                        'currency': 'USD'
                    }
                except Exception as e:
                    sectors[symbol] = {
                        'name': info['name'],
                        'sector': info['sector'],
                        'error': f'データ取得エラー: {str(e)}'
                    }
        except Exception as e:
            sectors = {'error': f'セクター情報取得エラー: {str(e)}'}

        # 市場概要（主要指数の集計）
        market_summary = {}
        try:
            if indices and not indices.get('error'):
                # 上昇・下降・変化なしのカウント
                up_count = sum(1 for data in indices.values() if isinstance(data, dict) and data.get('price_change_direction') == 'up')
                down_count = sum(1 for data in indices.values() if isinstance(data, dict) and data.get('price_change_direction') == 'down')
                unchanged_count = sum(1 for data in indices.values() if isinstance(data, dict) and data.get('price_change_direction') == 'unchanged')
                
                # 平均変化率
                changes = [data.get('price_change_percent', 0) for data in indices.values() 
                          if isinstance(data, dict) and data.get('price_change_percent') is not None]
                avg_change = sum(changes) / len(changes) if changes else 0
                
                market_summary = {
                    'total_indices': len(indices),
                    'up_count': up_count,
                    'down_count': down_count,
                    'unchanged_count': unchanged_count,
                    'average_change_percent': round(avg_change, 2),
                    'market_sentiment': get_market_sentiment(avg_change)
                }
        except Exception as e:
            market_summary = {'error': f'市場概要計算エラー: {str(e)}'}

        # セクター概要
        sector_summary = {}
        try:
            if sectors and not sectors.get('error'):
                sector_performance = {}
                for symbol, data in sectors.items():
                    if isinstance(data, dict) and 'sector' in data and 'price_change_percent' in data:
                        sector = data['sector']
                        change = data.get('price_change_percent', 0)
                        if sector not in sector_performance:
                            sector_performance[sector] = []
                        sector_performance[sector].append(change)
                
                # セクター別平均変化率
                sector_avg = {}
                for sector, changes in sector_performance.items():
                    if changes:
                        avg_change = sum(changes) / len(changes)
                        sector_avg[sector] = round(avg_change, 2)
                
                # ベスト・ワーストセクター
                if sector_avg:
                    best_sector = max(sector_avg.items(), key=lambda x: x[1])
                    worst_sector = min(sector_avg.items(), key=lambda x: x[1])
                    
                    sector_summary = {
                        'sector_averages': sector_avg,
                        'best_performing_sector': {
                            'sector': best_sector[0],
                            'change_percent': best_sector[1]
                        },
                        'worst_performing_sector': {
                            'sector': worst_sector[0],
                            'change_percent': worst_sector[1]
                        }
                    }
        except Exception as e:
            sector_summary = {'error': f'セクター概要計算エラー: {str(e)}'}

        result = {
            'indices': indices,
            'sectors': sectors,
            'market_summary': market_summary,
            'sector_summary': sector_summary,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        
        return result
        
    except Exception as e:
        return {'error': f'ホーム情報取得エラー: {str(e)}'}


def get_api_gateway_url(event=None, context=None):
    """API GatewayのURLを動的に取得する"""
    # 1. 環境変数から取得
    api_url = os.environ.get('API_GATEWAY_URL', '')
    if api_url:
        return api_url
    
    # 2. 代替環境変数から取得
    api_url = os.environ.get('AWS_API_GATEWAY_URL', '')
    if api_url:
        return api_url
    
    # 3. リクエストヘッダーから取得
    if event:
        headers = event.get('headers', {})
        host = headers.get('Host', '')
        if host:
            protocol = 'https' if headers.get('X-Forwarded-Proto') == 'https' else 'http'
            return f"{protocol}://{host}"
    
    # 4. Lambdaコンテキストから取得
    if context:
        try:
            function_arn = context.invoked_function_arn
            if function_arn:
                parts = function_arn.split(':')
                if len(parts) >= 4:
                    region = parts[3]
                    return f"https://execute-api.{region}.amazonaws.com/prod/"
        except:
            pass
    
    # 5. AWS SDKを使用してCloudFormationから取得
    try:
        import boto3
        cloudformation = boto3.client('cloudformation')
        response = cloudformation.describe_stacks(
            StackName='yfinance-api-stack'
        )
        for output in response['Stacks'][0]['Outputs']:
            if output['OutputKey'] == 'YFinanceApiUrl':
                return output['OutputValue']
    except:
        pass
    
    # 6. 最後の手段として固定URLを使用
    return 'https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod'

def generate_swagger_ui_html(event=None, context=None):
    """Swagger UIのHTMLを生成"""
    # API GatewayのベースURLを動的に取得
    api_url = get_api_gateway_url(event, context)
    
    # Swagger仕様書のJSON（簡略版）
    swagger_spec = {
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
                "url": api_url.rstrip('/'),
                "description": "Production server"
            }
        ],
        "paths": {
            "/search": {
                "get": {
                    "summary": "銘柄検索",
                    "description": "キーワードによる銘柄検索を実行します",
                    "parameters": [
                        {
                            "name": "q",
                            "in": "query",
                            "required": True,
                            "description": "検索キーワード（例: apple, microsoft）",
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "description": "検索結果件数（デフォルト: 10、最大: 10）",
                            "schema": {"type": "integer", "default": 10, "maximum": 10}
                        },
                        {
                            "name": "region",
                            "in": "query",
                            "required": False,
                            "description": "検索リージョン（デフォルト: US）",
                            "schema": {"type": "string", "enum": ["US", "JP"], "default": "US"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "query": {
                                                "type": "string", 
                                                "example": "apple",
                                                "description": "検索キーワード"
                                            },
                                            "region": {
                                                "type": "string", 
                                                "example": "US",
                                                "description": "検索リージョン"
                                            },
                                            "count": {
                                                "type": "integer", 
                                                "example": 7,
                                                "description": "検索結果件数"
                                            },
                                            "results": {
                                                "type": "array",
                                                "description": "検索結果の配列",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "symbol": {
                                                            "type": "string", 
                                                            "example": "AAPL",
                                                            "description": "ティッカーシンボル"
                                                        },
                                                        "name": {
                                                            "type": "string", 
                                                            "example": "Apple Inc.",
                                                            "description": "企業名"
                                                        },
                                                        "current_price": {
                                                            "type": "number", 
                                                            "example": 208.62,
                                                            "description": "現在の株価"
                                                        },
                                                        "price_change_direction": {
                                                            "type": "string", 
                                                            "example": "up",
                                                            "description": "価格変化の方向"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/tickerDetail": {
                "get": {
                    "summary": "詳細情報取得（統合版）",
                    "description": "指定されたティッカーシンボルの全ての情報を統合して取得します（価格、履歴、ニュース、配当、オプション、財務、ESG、株主情報など）",
                    "parameters": [
                        {
                            "name": "ticker",
                            "in": "query",
                            "required": True,
                            "description": "ティッカーシンボル（例: AAPL, MSFT, 7203.T）",
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "period",
                            "in": "query",
                            "required": False,
                            "description": "履歴期間（デフォルト: 1mo）",
                            "schema": {
                                "type": "string",
                                "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
                                "default": "1mo"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "ticker": {
                                                "type": "string", 
                                                "example": "AAPL",
                                                "description": "ティッカーシンボル"
                                            },
                                            "info": {
                                                "type": "object",
                                                "description": "企業基本情報"
                                            },
                                            "fast_info": {
                                                "type": "object",
                                                "description": "高速取得情報"
                                            },
                                            "price": {
                                                "type": "object",
                                                "description": "株価情報"
                                            },
                                            "history": {
                                                "type": "array",
                                                "description": "株価履歴"
                                            },
                                            "news": {
                                                "type": "array",
                                                "description": "関連ニュース"
                                            },
                                            "dividends": {
                                                "type": "array",
                                                "description": "配当履歴"
                                            },
                                            "options": {
                                                "type": "object",
                                                "description": "オプション情報"
                                            },
                                            "financials": {
                                                "type": "object",
                                                "description": "財務諸表（損益計算書、貸借対照表、キャッシュフロー）"
                                            },
                                            "analysts": {
                                                "type": "object",
                                                "description": "アナリスト予想"
                                            },
                                            "isin": {
                                                "type": "string",
                                                "description": "国際証券識別番号"
                                            },
                                            "recommendations": {
                                                "type": "array",
                                                "description": "アナリスト推奨履歴"
                                            },
                                            "calendar": {
                                                "type": "array",
                                                "description": "イベントカレンダー（決算日など）"
                                            },
                                            "earnings_dates": {
                                                "type": "array",
                                                "description": "過去/未来の決算日"
                                            },
                                            "sustainability": {
                                                "type": "object",
                                                "description": "ESG情報"
                                            },
                                            "holders": {
                                                "type": "object",
                                                "description": "株主情報（大株主、機関投資家、投資信託）"
                                            },
                                            "shares": {
                                                "type": "object",
                                                "description": "株式数詳細"
                                            },
                                            "analysis": {
                                                "type": "object",
                                                "description": "アナリスト分析"
                                            },
                                            "splits": {
                                                "type": "array",
                                                "description": "株式分割履歴"
                                            },
                                            "earnings": {
                                                "type": "object",
                                                "description": "決算情報（EPS、P/E比など）"
                                            },
                                            "upgrades_downgrades": {
                                                "type": "array",
                                                "description": "格付け変更履歴"
                                            },
                                            "execution_info": {
                                                "type": "object",
                                                "description": "実行環境情報"
                                            },
                                            "timestamp": {
                                                "type": "string", 
                                                "format": "date-time",
                                                "description": "データ取得時刻"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/chart": {
                "get": {
                    "summary": "チャート画像生成",
                    "description": "指定されたティッカーシンボルの株価チャートを画像で生成します",
                    "parameters": [
                        {
                            "name": "ticker",
                            "in": "query",
                            "required": True,
                            "description": "ティッカーシンボル（例: AAPL, MSFT, 7203.T）",
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "period",
                            "in": "query",
                            "required": False,
                            "description": "期間（デフォルト: 1mo）",
                            "schema": {
                                "type": "string",
                                "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
                                "default": "1mo"
                            }
                        },
                        {
                            "name": "type",
                            "in": "query",
                            "required": False,
                            "description": "チャートタイプ（デフォルト: line）",
                            "schema": {
                                "type": "string",
                                "enum": ["line", "candle"],
                                "default": "line"
                            }
                        },
                        {
                            "name": "size",
                            "in": "query",
                            "required": False,
                            "description": "画像サイズ（デフォルト: 800x400）",
                            "schema": {
                                "type": "string",
                                "default": "800x400"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "成功",
                            "content": {
                                "image/png": {
                                    "schema": {
                                        "type": "string",
                                        "format": "binary"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/ticker/basic": {
                "get": {
                    "summary": "基本情報取得",
                    "description": "指定されたティッカーシンボルの基本情報を取得します",
                    "parameters": [
                        {"name": "ticker", "in": "query", "required": True, "description": "ティッカーシンボル（例: AAPL, MSFT, 7203.T）", "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"ticker": {"type": "string"}, "info": {"type": "object"}, "fast_info": {"type": "object"}, "logo_url": {"type": "string"}, "isin": {"type": "string"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/ticker/price": {
                "get": {
                    "summary": "株価情報取得",
                    "description": "指定されたティッカーシンボルの現在の株価情報を取得します",
                    "parameters": [
                        {"name": "ticker", "in": "query", "required": True, "description": "ティッカーシンボル", "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"ticker": {"type": "string"}, "price": {"type": "object"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/ticker/history": {
                "get": {
                    "summary": "株価履歴取得",
                    "description": "指定されたティッカーシンボルの株価履歴を取得します",
                    "parameters": [
                        {"name": "ticker", "in": "query", "required": True, "description": "ティッカーシンボル", "schema": {"type": "string"}},
                        {"name": "period", "in": "query", "required": False, "description": "履歴期間（デフォルト: 1mo）", "schema": {"type": "string", "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"], "default": "1mo"}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"ticker": {"type": "string"}, "period": {"type": "string"}, "history": {"type": "array"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/ticker/financials": {
                "get": {
                    "summary": "財務情報取得",
                    "description": "指定されたティッカーシンボルの財務諸表・決算情報を取得します",
                    "parameters": [
                        {"name": "ticker", "in": "query", "required": True, "description": "ティッカーシンボル", "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"ticker": {"type": "string"}, "financials": {"type": "object"}, "earnings": {"type": "object"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/ticker/analysts": {
                "get": {
                    "summary": "アナリスト情報取得",
                    "description": "指定されたティッカーシンボルのアナリスト予想・分析情報を取得します",
                    "parameters": [
                        {"name": "ticker", "in": "query", "required": True, "description": "ティッカーシンボル", "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"ticker": {"type": "string"}, "analysts": {"type": "object"}, "recommendations": {"type": "array"}, "analysis": {"type": "object"}, "upgrades_downgrades": {"type": "array"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/ticker/holders": {
                "get": {
                    "summary": "株主情報取得",
                    "description": "指定されたティッカーシンボルの株主情報を取得します",
                    "parameters": [
                        {"name": "ticker", "in": "query", "required": True, "description": "ティッカーシンボル", "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"ticker": {"type": "string"}, "holders": {"type": "object"}, "shares": {"type": "object"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/ticker/events": {
                "get": {
                    "summary": "イベント情報取得",
                    "description": "指定されたティッカーシンボルのイベント情報（決算日、配当、分割など）を取得します",
                    "parameters": [
                        {"name": "ticker", "in": "query", "required": True, "description": "ティッカーシンボル", "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"ticker": {"type": "string"}, "calendar": {"type": "array"}, "earnings_dates": {"type": "array"}, "dividends": {"type": "array"}, "splits": {"type": "array"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/ticker/news": {
                "get": {
                    "summary": "ニュース情報取得",
                    "description": "指定されたティッカーシンボルの関連ニュースを取得します",
                    "parameters": [
                        {"name": "ticker", "in": "query", "required": True, "description": "ティッカーシンボル", "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"ticker": {"type": "string"}, "news": {"type": "array"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/ticker/options": {
                "get": {
                    "summary": "オプション情報取得",
                    "description": "指定されたティッカーシンボルのオプション情報を取得します",
                    "parameters": [
                        {"name": "ticker", "in": "query", "required": True, "description": "ティッカーシンボル", "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"ticker": {"type": "string"}, "options": {"type": "array"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/ticker/sustainability": {
                "get": {
                    "summary": "ESG情報取得",
                    "description": "指定されたティッカーシンボルのESG（環境・社会・ガバナンス）情報を取得します",
                    "parameters": [
                        {"name": "ticker", "in": "query", "required": True, "description": "ティッカーシンボル", "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"ticker": {"type": "string"}, "sustainability": {"type": "object"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/home": {
                "get": {
                    "summary": "ホーム画面情報取得",
                    "description": "株価指数、主要ETF、セクター情報などのホーム画面用情報を取得します",
                    "parameters": [],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"indices": {"type": "object"}, "etfs": {"type": "object"}, "sectors": {"type": "object"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/news/rss": {
                "get": {
                    "summary": "Yahoo Finance RSSニュース取得",
                    "description": "Yahoo FinanceのRSSフィードから最新ニュースを取得します",
                    "parameters": [
                        {"name": "limit", "in": "query", "required": False, "description": "取得件数（デフォルト10）", "schema": {"type": "integer", "default": 10}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"status": {"type": "string"}, "data": {"type": "array"}, "count": {"type": "integer"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            }
        }
    }
    
    # Swagger UIのHTML
    html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YFinance API - Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}
        *, *:before, *:after {{
            box-sizing: inherit;
        }}
        body {{
            margin:0;
            background: #fafafa;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                spec: {json.dumps(swagger_spec)},
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            }});
        }};
    </script>
</body>
</html>
"""
    return html

def get_stock_chart_api(ticker, period='1mo', size='800x400', chart_type='line'):
    """株価チャート画像を生成し base64 文字列で返却する。エラー時は (None, error) を返す"""
    try:
        import matplotlib
        matplotlib.use('Agg')  # バックエンドを非GUIに
        import matplotlib.pyplot as plt
        from io import BytesIO
        import base64

        # サイズ解析
        try:
            width, height = map(int, size.lower().split('x'))
        except Exception:
            width, height = 800, 400

        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty:
            return None, f'履歴データが取得できませんでした: {ticker}'

        plt.figure(figsize=(width/100, height/100))

        if chart_type == 'candle' and 'Open' in hist.columns:
            # ローソク足（簡易）
            try:
                from mplfinance.original_flavor import candlestick_ohlc
                import matplotlib.dates as mdates
                ohlc = hist[['Open', 'High', 'Low', 'Close']].copy()
                ohlc.reset_index(inplace=True)
                ohlc['Date'] = ohlc['Date'].map(mdates.date2num)
                ax = plt.gca()
                candlestick_ohlc(ax, ohlc.values, width=0.6, colorup='g', colordown='r')
                ax.xaxis_date()
                plt.title(f'{ticker} {period} candlestick')
            except Exception:
                plt.plot(hist.index, hist['Close'], label='Close')
        else:
            # 折れ線
            plt.plot(hist.index, hist['Close'], label='Close')
            plt.title(f'{ticker} {period} close price')

        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.tight_layout()

        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return img_base64, None
    except Exception as e:
        return None, str(e)

def clean_html(text):
    if not text:
        return ""
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    text = ' '.join(text.split())
    return text

def generate_news_id(title, url):
    content = f"{title}_{url}".encode('utf-8')
    return hashlib.md5(content).hexdigest()[:12]

def parse_published_date(entry):
    published_date = None
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        try:
            published_date = datetime(*entry.published_parsed[:6])
        except:
            pass
    if not published_date and hasattr(entry, 'published'):
        try:
            published_date = entry.published
        except:
            pass
    if not published_date and hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        try:
            published_date = datetime(*entry.updated_parsed[:6])
        except:
            pass
    return published_date

def fetch_rss_feed(source):
    try:
        feed = feedparser.parse(source['url'])
        articles = []
        for entry in feed.entries:
            title = clean_html(entry.get('title', ''))
            if not title:
                continue
            url = entry.get('link', '')
            summary = clean_html(entry.get('summary', entry.get('description', '')))
            published_date = parse_published_date(entry)
            author = entry.get('author', '')
            image_url = None
            if hasattr(entry, 'media_content'):
                for media in entry.media_content:
                    if media.get('type', '').startswith('image'):
                        image_url = media.get('url')
                        break
            if not image_url and hasattr(entry, 'enclosures'):
                for enclosure in entry.enclosures:
                    if enclosure.type.startswith('image'):
                        image_url = enclosure.href
                        break
            tags = []
            if hasattr(entry, 'tags'):
                tags = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
            article = {
                'id': generate_news_id(title, url),
                'title': title,
                'summary': summary[:500] + '...' if len(summary) > 500 else summary,
                'url': url,
                'source': source['name'],
                'category': source['category'],
                'published_at': published_date.isoformat() if isinstance(published_date, datetime) else published_date,
                'author': author,
                'image_url': image_url,
                'tags': tags
            }
            articles.append(article)
        return articles
    except Exception as e:
        return []

def lamuda_get_rss_news_api(query_parameters):
    category = query_parameters.get('category', 'all')
    source_filter = query_parameters.get('source', '')
    limit = min(int(query_parameters.get('limit', 50)), 200)
    sort = query_parameters.get('sort', 'published_desc')
    target_sources = RSS_SOURCES
    if category != 'all':
        target_sources = [s for s in target_sources if s['category'] == category]
    if source_filter:
        target_sources = [s for s in target_sources if source_filter.lower() in s['name'].lower()]
    all_articles = []
    for source in target_sources:
        all_articles.extend(fetch_rss_feed(source))
    unique_articles = {}
    for article in all_articles:
        title_key = article['title'].lower().strip()
        if title_key not in unique_articles:
            unique_articles[title_key] = article
        else:
            existing = unique_articles[title_key]
            if article['published_at'] and existing['published_at']:
                try:
                    if isinstance(article['published_at'], str):
                        article_date = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))
                    else:
                        article_date = article['published_at']
                    if isinstance(existing['published_at'], str):
                        existing_date = datetime.fromisoformat(existing['published_at'].replace('Z', '+00:00'))
                    else:
                        existing_date = existing['published_at']
                    if article_date > existing_date:
                        unique_articles[title_key] = article
                except:
                    pass
    final_articles = list(unique_articles.values())
    try:
        if sort == 'published_desc':
            final_articles.sort(key=lambda x: x['published_at'] or '', reverse=True)
        elif sort == 'published_asc':
            final_articles.sort(key=lambda x: x['published_at'] or '')
        elif sort == 'title_asc':
            final_articles.sort(key=lambda x: x['title'].lower())
    except Exception:
        pass
    final_articles = final_articles[:limit]
    return {
        'status': 'success',
        'data': final_articles,
        'metadata': {
            'total_sources': len(target_sources),
            'total_articles': len(final_articles),
            'sources_used': [s['name'] for s in target_sources],
            'category_filter': category,
            'source_filter': source_filter,
            'sort': sort,
            'last_updated': datetime.now().isoformat()
        },
        'timestamp': datetime.now().isoformat()
    }