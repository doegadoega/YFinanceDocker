import json
import yfinance as yf
from datetime import datetime
import traceback
import os
import pandas as pd
import numpy as np

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
        elif '/info' in resource:
            ticker = query_parameters.get('ticker', '').upper()
            if not ticker:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'ティッカーシンボルが必要です'})
                }
            # periodパラメータも受け取る（history用）
            period = query_parameters.get('period', '1mo')
            result = get_stock_info_api(ticker, period)
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
                            result['price_change_direction'] = 'up' if price_change > 0 else 'down' if price_change < 0 else 'unchanged'
                        
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
    """銘柄の全情報をまとめて返すAPI（新yfinance API使用）"""
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
            # FastInfoオブジェクトを辞書に変換
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
        logo_url = info.get('logo_url') if info else None
        if not logo_url:
            website = info.get('website') if info else None
            if website:
                import re
                m = re.search(r'https?://([^/]+)', website)
                if m:
                    logo_url = f"https://logo.clearbit.com/{m.group(1)}"

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

        # 履歴（期間をパラメータで指定可能）
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

        # オプション（従来通り）
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
            else:
                options_data = []
        except Exception as e:
            options_data = f'オプション情報取得エラー: {str(e)}'

        # === 新しいYFinanceメソッド群 ===
        
        # ISIN（国際証券識別番号）
        try:
            isin = stock.get_isin()
        except Exception as e:
            isin = f'ISIN取得エラー: {str(e)}'

        # アナリスト推奨履歴
        try:
            recommendations = stock.get_recommendations()
            if not recommendations.empty:
                recommendations_data = safe_dataframe_to_records(recommendations)
            else:
                recommendations_data = []
        except Exception as e:
            recommendations_data = f'推奨履歴取得エラー: {str(e)}'

        # カレンダー（決算日など）
        try:
            calendar = stock.get_calendar()
            if not calendar.empty:
                calendar_data = safe_dataframe_to_records(calendar)
            else:
                calendar_data = []
        except Exception as e:
            calendar_data = f'カレンダー取得エラー: {str(e)}'

        # 決算日
        try:
            earnings_dates = stock.get_earnings_dates()
            if not earnings_dates.empty:
                earnings_dates_data = safe_dataframe_to_records(earnings_dates)
            else:
                earnings_dates_data = []
        except Exception as e:
            earnings_dates_data = f'決算日取得エラー: {str(e)}'

        # 財務諸表（新メソッド使用）
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
            financials = f'財務情報取得エラー: {str(e)}'

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
            holders_data = f'株主情報取得エラー: {str(e)}'

        # 株式数詳細
        try:
            shares = stock.get_shares()
            if not shares.empty:
                shares_data = safe_dataframe_to_dict(shares)
            else:
                shares_data = {}
        except Exception as e:
            shares_data = f'株式数取得エラー: {str(e)}'

        # アナリスト分析
        try:
            analysis = stock.get_analysis()
            if not analysis.empty:
                analysis_data = safe_dataframe_to_dict(analysis)
            else:
                analysis_data = {}
        except Exception as e:
            analysis_data = f'アナリスト分析取得エラー: {str(e)}'

        # 格付け変更履歴
        try:
            upgrades_downgrades = stock.get_upgrades_downgrades()
            if not upgrades_downgrades.empty:
                upgrades_downgrades_data = safe_dataframe_to_records(upgrades_downgrades)
            else:
                upgrades_downgrades_data = []
        except Exception as e:
            upgrades_downgrades_data = f'格付け変更履歴取得エラー: {str(e)}'

        # アナリスト予想（従来）
        try:
            analysts = {}
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
            analysts = f'アナリスト予想取得エラー: {str(e)}'

        result = {
            'ticker': ticker,
            'info': info,
            'info_error': info_error,
            'fast_info': fast_info,
            'logo_url': logo_url,
            'price': price,
            'history': history,
            'news': news,
            'dividends': dividends,
            'options': options_data,
            'financials': financials,
            'analysts': analysts,
            # 新しいYFinanceメソッド
            'isin': isin,
            'recommendations': recommendations_data,
            'calendar': calendar_data,
            'earnings_dates': earnings_dates_data,
            'sustainability': sustainability_data,
            'holders': holders_data,
            'shares': shares_data,
            'analysis': analysis_data,
            'upgrades_downgrades': upgrades_downgrades_data,
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'銘柄情報取得エラー: {str(e)}'}



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
    return 'https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod/'

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
            "/info": {
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
                                            "upgrades_downgrades": {
                                                "type": "array",
                                                "description": "格付け変更履歴"
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