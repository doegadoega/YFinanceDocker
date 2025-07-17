import json
import yfinance as yfy
from datetime import datetime
import traceback
import os


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
        elif '/price' in resource:
            ticker = query_parameters.get('ticker', '').upper()
            if not ticker:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'ティッカーシンボルが必要です'})
                }
            result = get_stock_price_api(ticker)
        elif '/info' in resource:
            ticker = query_parameters.get('ticker', '').upper()
            if not ticker:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'ティッカーシンボルが必要です'})
                }
            result = get_stock_info_api(ticker)
        elif '/history' in resource:
            ticker = query_parameters.get('ticker', '').upper()
            if not ticker:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'ティッカーシンボルが必要です'})
                }
            period = query_parameters.get('period', '1mo')
            result = get_stock_history_api(ticker, period)
        elif '/news' in resource:
            ticker = query_parameters.get('ticker', '').upper()
            if not ticker:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'ティッカーシンボルが必要です'})
                }
            result = get_stock_news_api(ticker)
        elif '/dividends' in resource:
            ticker = query_parameters.get('ticker', '').upper()
            if not ticker:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'ティッカーシンボルが必要です'})
                }
            result = get_stock_dividends_api(ticker)
        elif '/options' in resource:
            ticker = query_parameters.get('ticker', '').upper()
            if not ticker:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'ティッカーシンボルが必要です'})
                }
            result = get_stock_options_api(ticker)
        elif '/financials' in resource:
            ticker = query_parameters.get('ticker', '').upper()
            if not ticker:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'ティッカーシンボルが必要です'})
                }
            result = get_stock_financials_api(ticker)
        elif '/analysts' in resource:
            ticker = query_parameters.get('ticker', '').upper()
            if not ticker:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'ティッカーシンボルが必要です'})
                }
            result = get_stock_analysts_api(ticker)
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
            'body': json.dumps(result)
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


def get_stock_price_api(ticker):
    """現在の株価を取得（API用）"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        current_price = info.get('currentPrice', info.get('regularMarketPrice'))
        
        if current_price is None:
            return {'error': f'株価データが取得できませんでした: {ticker}'}
        
        return {
            'ticker': ticker,
            'current_price': current_price,
            'currency': info.get('currency', 'USD'),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f'株価取得エラー: {str(e)}'}


def get_stock_info_api(ticker):
    """株式情報を取得（API用）"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        result = {
            'ticker': ticker,
            'name': info.get('longName', 'N/A'),
            'current_price': info.get('currentPrice', info.get('regularMarketPrice')),
            'previous_close': info.get('previousClose'),
            'market_cap': info.get('marketCap'),
            'dividend_yield': info.get('dividendYield'),
            'trailing_pe': info.get('trailingPE'),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
            'currency': info.get('currency', 'USD'),
            'exchange': info.get('exchange'),
            'sector': info.get('sector'),
            'industry': info.get('industry'),
            'timestamp': datetime.now().isoformat()
        }
        
        return result
    except Exception as e:
        return {'error': f'株式情報取得エラー: {str(e)}'}


def get_stock_history_api(ticker, period='1mo'):
    """株価履歴を取得（API用）"""
    try:
        # 期間の妥当性チェック
        valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
        if period not in valid_periods:
            period = '1mo'
        
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if len(hist) == 0:
            return {'error': f'履歴データが取得できませんでした: {ticker}'}
        
        # 履歴データを手動で変換
        history_data = []
        for i in range(len(hist)):
            date = hist.index[i]
            row = hist.iloc[i]
            history_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(float(row['Open']), 2),
                'high': round(float(row['High']), 2),
                'low': round(float(row['Low']), 2),
                'close': round(float(row['Close']), 2),
                'volume': int(row['Volume'])
            })
        
        return {
            'ticker': ticker,
            'period': period,
            'data': history_data,
            'count': len(history_data),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f'履歴データ取得エラー: {str(e)}'}


def get_stock_news_api(ticker):
    """株式ニュースを取得（API用）"""
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        
        if not news:
            return {
                'ticker': ticker,
                'news': [],
                'count': 0,
                'message': f'{ticker}に関するニュースが見つかりませんでした',
                'timestamp': datetime.now().isoformat()
            }
        
        # ニュースデータを整理
        news_data = []
        for article in news:
            news_data.append({
                'title': article.get('title', ''),
                'summary': article.get('summary', ''),
                'link': article.get('link', ''),
                'publisher': article.get('publisher', ''),
                'published': article.get('providerPublishTime', ''),
                'type': article.get('type', ''),
                'uuid': article.get('uuid', '')
            })
        
        return {
            'ticker': ticker,
            'news': news_data,
            'count': len(news_data),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f'ニュース取得エラー: {str(e)}'}


def get_stock_dividends_api(ticker):
    """配当情報を取得（API用）"""
    try:
        stock = yf.Ticker(ticker)
        dividends = stock.dividends
        
        if len(dividends) == 0:
            return {
                'ticker': ticker,
                'dividends': [],
                'count': 0,
                'message': f'{ticker}の配当情報が見つかりませんでした',
                'timestamp': datetime.now().isoformat()
            }
        
        # 配当データを整理
        dividend_data = []
        for date, amount in dividends.items():
            dividend_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'amount': float(amount)
            })
        
        return {
            'ticker': ticker,
            'dividends': dividend_data,
            'count': len(dividend_data),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f'配当情報取得エラー: {str(e)}'}


def get_stock_options_api(ticker):
    """オプション情報を取得（API用）"""
    try:
        stock = yf.Ticker(ticker)
        
        # 次のオプション満期日を取得
        options = stock.options
        
        if not options:
            return {
                'ticker': ticker,
                'options': [],
                'count': 0,
                'message': f'{ticker}のオプション情報が見つかりませんでした',
                'timestamp': datetime.now().isoformat()
            }
        
        # 最新のオプション満期日の情報を取得
        latest_expiry = options[0]
        calls = stock.option_chain(latest_expiry).calls
        puts = stock.option_chain(latest_expiry).puts
        
        # コールオプションを整理
        calls_data = []
        for _, call in calls.iterrows():
            calls_data.append({
                'strike': float(call['strike']),
                'last_price': float(call['lastPrice']),
                'bid': float(call['bid']),
                'ask': float(call['ask']),
                'volume': int(call['volume']),
                'open_interest': int(call['openInterest'])
            })
        
        # プットオプションを整理
        puts_data = []
        for _, put in puts.iterrows():
            puts_data.append({
                'strike': float(put['strike']),
                'last_price': float(put['lastPrice']),
                'bid': float(put['bid']),
                'ask': float(put['ask']),
                'volume': int(put['volume']),
                'open_interest': int(put['openInterest'])
            })
        
        return {
            'ticker': ticker,
            'expiry_date': latest_expiry,
            'calls': calls_data,
            'puts': puts_data,
            'calls_count': len(calls_data),
            'puts_count': len(puts_data),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f'オプション情報取得エラー: {str(e)}'}


def get_stock_financials_api(ticker):
    """財務情報を取得（API用）"""
    try:
        stock = yf.Ticker(ticker)
        
        # 財務諸表を取得
        income_stmt = stock.income_stmt
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow
        
        result = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat()
        }
        
        # 損益計算書の最新データ
        if not income_stmt.empty:
            latest_income = income_stmt.iloc[:, 0]  # 最新の年度
            result['income_statement'] = {
                'total_revenue': float(latest_income.get('Total Revenue', 0)),
                'gross_profit': float(latest_income.get('Gross Profit', 0)),
                'operating_income': float(latest_income.get('Operating Income', 0)),
                'net_income': float(latest_income.get('Net Income', 0)),
                'eps': float(latest_income.get('Basic EPS', 0))
            }
        
        # 貸借対照表の最新データ
        if not balance_sheet.empty:
            latest_balance = balance_sheet.iloc[:, 0]  # 最新の年度
            result['balance_sheet'] = {
                'total_assets': float(latest_balance.get('Total Assets', 0)),
                'total_liabilities': float(latest_balance.get('Total Liabilities Net Minority Interest', 0)),
                'total_equity': float(latest_balance.get('Total Equity Gross Minority Interest', 0)),
                'cash': float(latest_balance.get('Cash and Cash Equivalents', 0)),
                'debt': float(latest_balance.get('Total Debt', 0))
            }
        
        # キャッシュフロー計算書の最新データ
        if not cash_flow.empty:
            latest_cashflow = cash_flow.iloc[:, 0]  # 最新の年度
            result['cash_flow'] = {
                'operating_cash_flow': float(latest_cashflow.get('Operating Cash Flow', 0)),
                'investing_cash_flow': float(latest_cashflow.get('Investing Cash Flow', 0)),
                'financing_cash_flow': float(latest_cashflow.get('Financing Cash Flow', 0)),
                'free_cash_flow': float(latest_cashflow.get('Free Cash Flow', 0))
            }
        
        return result
    except Exception as e:
        return {'error': f'財務情報取得エラー: {str(e)}'}


def get_stock_analysts_api(ticker):
    """アナリスト予想を取得（API用）"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # アナリスト予想情報を抽出
        analyst_info = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat()
        }
        
        # 推奨レーティング
        if 'recommendationMean' in info:
            analyst_info['recommendation_mean'] = info['recommendationMean']
        
        # 目標株価
        if 'targetMeanPrice' in info:
            analyst_info['target_mean_price'] = info['targetMeanPrice']
        
        # アナリスト数
        if 'numberOfAnalystOpinions' in info:
            analyst_info['number_of_analysts'] = info['numberOfAnalystOpinions']
        
        # 推奨レーティング分布
        rating_keys = ['strongBuy', 'buy', 'hold', 'sell', 'strongSell']
        ratings = {}
        for key in rating_keys:
            if key in info:
                ratings[key] = info[key]
        
        if ratings:
            analyst_info['rating_distribution'] = ratings
        
        return analyst_info
    except Exception as e:
        return {'error': f'アナリスト予想取得エラー: {str(e)}'}


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
            "/price": {
                "get": {
                    "summary": "株価取得",
                    "description": "指定されたティッカーシンボルの現在の株価を取得します",
                    "parameters": [
                        {
                            "name": "ticker",
                            "in": "query",
                            "required": True,
                            "description": "ティッカーシンボル（例: AAPL, MSFT, 7203.T）",
                            "schema": {"type": "string"}
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
                                            "symbol": {
                                                "type": "string", 
                                                "example": "AAPL",
                                                "description": "ティッカーシンボル"
                                            },
                                            "price": {
                                                "type": "number", 
                                                "example": 208.62,
                                                "description": "現在の株価"
                                            },
                                            "currency": {
                                                "type": "string", 
                                                "example": "USD",
                                                "description": "通貨単位（USD: 米ドル, JPY: 日本円）"
                                            },
                                            "timestamp": {
                                                "type": "string", 
                                                "format": "date-time",
                                                "description": "データ取得時刻（ISO 8601形式）"
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
                    "summary": "詳細情報取得",
                    "description": "指定されたティッカーシンボルの詳細な企業情報を取得します",
                    "parameters": [
                        {
                            "name": "ticker",
                            "in": "query",
                            "required": True,
                            "description": "ティッカーシンボル（例: AAPL, MSFT, 7203.T）",
                            "schema": {"type": "string"}
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
                                            "symbol": {
                                                "type": "string", 
                                                "example": "AAPL",
                                                "description": "ティッカーシンボル"
                                            },
                                            "name": {
                                                "type": "string", 
                                                "example": "Apple Inc.",
                                                "description": "企業の正式名称"
                                            },
                                            "currentPrice": {
                                                "type": "number", 
                                                "example": 208.62,
                                                "description": "現在の株価"
                                            },
                                            "previousClose": {
                                                "type": "number", 
                                                "example": 211.16,
                                                "description": "前営業日の終値"
                                            },
                                            "marketCap": {
                                                "type": "number", 
                                                "example": 3115906498560,
                                                "description": "時価総額（発行済み株式総数 × 株価）"
                                            },
                                            "dividendYield": {
                                                "type": "number", 
                                                "example": 0.51,
                                                "description": "配当利回り（年間配当金 ÷ 株価 × 100）"
                                            },
                                            "trailingPE": {
                                                "type": "number", 
                                                "example": 32.44,
                                                "description": "P/E比率（株価収益率 = 株価 ÷ 1株当たり利益）"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/history": {
                "get": {
                    "summary": "株価履歴取得",
                    "description": "指定されたティッカーシンボルの株価履歴データを取得します",
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
                                            "symbol": {
                                                "type": "string", 
                                                "example": "AAPL",
                                                "description": "ティッカーシンボル"
                                            },
                                            "period": {
                                                "type": "string", 
                                                "example": "1mo",
                                                "description": "取得期間（1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max）"
                                            },
                                            "data": {
                                                "type": "object",
                                                "description": "日別の株価データ（日付をキーとするオブジェクト）",
                                                "additionalProperties": {
                                                    "type": "object",
                                                    "properties": {
                                                        "Open": {
                                                            "type": "number", 
                                                            "example": 209.93,
                                                            "description": "始値（その日の最初の取引価格）"
                                                        },
                                                        "High": {
                                                            "type": "number", 
                                                            "example": 210.91,
                                                            "description": "高値（その日の最高取引価格）"
                                                        },
                                                        "Low": {
                                                            "type": "number", 
                                                            "example": 207.54,
                                                            "description": "安値（その日の最低取引価格）"
                                                        },
                                                        "Close": {
                                                            "type": "number", 
                                                            "example": 208.62,
                                                            "description": "終値（その日の最後の取引価格）"
                                                        },
                                                        "Volume": {
                                                            "type": "number", 
                                                            "example": 38711400,
                                                            "description": "出来高（その日の取引量）"
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
                            "description": "検索結果件数（最大10件、デフォルト: 10）",
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
                                                "description": "検索リージョン（US: 米国, JP: 日本）"
                                            },
                                            "count": {
                                                "type": "integer", 
                                                "example": 7,
                                                "description": "検索結果件数"
                                            },
                                            "max_results": {
                                                "type": "integer", 
                                                "example": 10,
                                                "description": "最大検索結果件数"
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
                                                        "exchange": {
                                                            "type": "string", 
                                                            "example": "NMS",
                                                            "description": "取引所（NMS: NASDAQ, NYQ: NYSE, TYO: 東京証券取引所）"
                                                        },
                                                        "type": {
                                                            "type": "string", 
                                                            "example": "Equity",
                                                            "description": "証券の種類（Equity: 株式）"
                                                        },
                                                        "score": {
                                                            "type": "number", 
                                                            "example": 31292.0,
                                                            "description": "検索スコア（関連度、数値が高いほど関連性が高い）"
                                                        },
                                                        "current_price": {
                                                            "type": "number", 
                                                            "example": 208.62,
                                                            "description": "現在の株価"
                                                        },
                                                        "previous_close": {
                                                            "type": "number", 
                                                            "example": 211.16,
                                                            "description": "前営業日の終値"
                                                        },
                                                        "price_change": {
                                                            "type": "number", 
                                                            "example": -2.54,
                                                            "description": "前日との価格差"
                                                        },
                                                        "price_change_percent": {
                                                            "type": "number", 
                                                            "example": -1.20,
                                                            "description": "前日との価格変化率（%）"
                                                        },
                                                        "price_change_direction": {
                                                            "type": "string", 
                                                            "example": "down",
                                                            "description": "価格変化の方向（up: 上昇, down: 下落, unchanged: 変化なし）"
                                                        },
                                                        "currency": {
                                                            "type": "string", 
                                                            "example": "USD",
                                                            "description": "通貨単位"
                                                        },
                                                        "market_cap": {
                                                            "type": "number", 
                                                            "example": 3115906498560,
                                                            "description": "時価総額"
                                                        },
                                                        "volume": {
                                                            "type": "number", 
                                                            "example": 38711400,
                                                            "description": "当日の出来高"
                                                        },
                                                        "avg_volume": {
                                                            "type": "number", 
                                                            "example": 45678900,
                                                            "description": "平均出来高"
                                                        },
                                                        "timestamp": {
                                                            "type": "string", 
                                                            "format": "date-time",
                                                            "example": "2024-01-15T10:30:00",
                                                            "description": "データ取得時刻"
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
            "/news": {
                "get": {
                    "summary": "ニュース取得",
                    "description": "指定されたティッカーシンボルに関連する最新ニュースを取得します",
                    "parameters": [
                        {
                            "name": "ticker",
                            "in": "query",
                            "required": True,
                            "description": "ティッカーシンボル（例: AAPL, MSFT, 7203.T）",
                            "schema": {"type": "string"}
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
                                            "symbol": {
                                                "type": "string", 
                                                "example": "AAPL",
                                                "description": "ティッカーシンボル"
                                            },
                                            "news": {
                                                "type": "array",
                                                "description": "ニュース記事の配列",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "title": {
                                                            "type": "string", 
                                                            "example": "Apple Reports Record Q4 Earnings",
                                                            "description": "ニュース記事のタイトル"
                                                        },
                                                        "link": {
                                                            "type": "string", 
                                                            "example": "https://example.com/news/1",
                                                            "description": "ニュース記事のURL"
                                                        },
                                                        "publisher": {
                                                            "type": "string", 
                                                            "example": "Reuters",
                                                            "description": "ニュース配信元"
                                                        },
                                                        "published": {
                                                            "type": "string", 
                                                            "format": "date-time",
                                                            "description": "配信日時"
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
            "/dividends": {
                "get": {
                    "summary": "配当情報取得",
                    "description": "指定されたティッカーシンボルの配当情報を取得します",
                    "parameters": [
                        {
                            "name": "ticker",
                            "in": "query",
                            "required": True,
                            "description": "ティッカーシンボル（例: AAPL, MSFT, 7203.T）",
                            "schema": {"type": "string"}
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
                                            "symbol": {
                                                "type": "string", 
                                                "example": "AAPL",
                                                "description": "ティッカーシンボル"
                                            },
                                            "dividendYield": {
                                                "type": "number", 
                                                "example": 0.51,
                                                "description": "配当利回り（%）"
                                            },
                                            "dividendRate": {
                                                "type": "number", 
                                                "example": 0.96,
                                                "description": "年間配当金"
                                            },
                                            "payoutRatio": {
                                                "type": "number", 
                                                "example": 0.16,
                                                "description": "配当性向（利益に対する配当の割合）"
                                            },
                                            "exDividendDate": {
                                                "type": "string", 
                                                "format": "date",
                                                "example": "2024-11-08",
                                                "description": "配当権利確定日"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/options": {
                "get": {
                    "summary": "オプション情報取得",
                    "description": "指定されたティッカーシンボルのオプション情報を取得します",
                    "parameters": [
                        {
                            "name": "ticker",
                            "in": "query",
                            "required": True,
                            "description": "ティッカーシンボル（例: AAPL, MSFT, 7203.T）",
                            "schema": {"type": "string"}
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
                                            "symbol": {
                                                "type": "string", 
                                                "example": "AAPL",
                                                "description": "ティッカーシンボル"
                                            },
                                            "currentPrice": {
                                                "type": "number", 
                                                "example": 208.62,
                                                "description": "現在の株価"
                                            },
                                            "options": {
                                                "type": "object",
                                                "description": "オプション情報",
                                                "properties": {
                                                    "calls": {
                                                        "type": "array",
                                                        "description": "コールオプション情報",
                                                        "items": {
                                                            "type": "object",
                                                            "properties": {
                                                                "strike": {
                                                                    "type": "number", 
                                                                    "example": 200,
                                                                    "description": "行使価格"
                                                                },
                                                                "lastPrice": {
                                                                    "type": "number", 
                                                                    "example": 12.50,
                                                                    "description": "最終価格"
                                                                },
                                                                "volume": {
                                                                    "type": "number", 
                                                                    "example": 1500,
                                                                    "description": "取引量"
                                                                }
                                                            }
                                                        }
                                                    },
                                                    "puts": {
                                                        "type": "array",
                                                        "description": "プットオプション情報",
                                                        "items": {
                                                            "type": "object",
                                                            "properties": {
                                                                "strike": {
                                                                    "type": "number", 
                                                                    "example": 200,
                                                                    "description": "行使価格"
                                                                },
                                                                "lastPrice": {
                                                                    "type": "number", 
                                                                    "example": 4.20,
                                                                    "description": "最終価格"
                                                                },
                                                                "volume": {
                                                                    "type": "number", 
                                                                    "example": 800,
                                                                    "description": "取引量"
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
                    }
                }
            },
            "/financials": {
                "get": {
                    "summary": "財務情報取得",
                    "description": "指定されたティッカーシンボルの財務情報を取得します",
                    "parameters": [
                        {
                            "name": "ticker",
                            "in": "query",
                            "required": True,
                            "description": "ティッカーシンボル（例: AAPL, MSFT, 7203.T）",
                            "schema": {"type": "string"}
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
                                            "symbol": {
                                                "type": "string", 
                                                "example": "AAPL",
                                                "description": "ティッカーシンボル"
                                            },
                                            "financials": {
                                                "type": "object",
                                                "description": "財務情報",
                                                "properties": {
                                                    "incomeStatement": {
                                                        "type": "object",
                                                        "description": "損益計算書",
                                                        "properties": {
                                                            "revenue": {
                                                                "type": "number", 
                                                                "example": 394328000000,
                                                                "description": "売上高"
                                                            },
                                                            "grossProfit": {
                                                                "type": "number", 
                                                                "example": 170782000000,
                                                                "description": "売上総利益"
                                                            },
                                                            "netIncome": {
                                                                "type": "number", 
                                                                "example": 96995000000,
                                                                "description": "純利益"
                                                            }
                                                        }
                                                    },
                                                    "balanceSheet": {
                                                        "type": "object",
                                                        "description": "貸借対照表",
                                                        "properties": {
                                                            "totalAssets": {
                                                                "type": "number", 
                                                                "example": 352755000000,
                                                                "description": "総資産"
                                                            },
                                                            "totalLiabilities": {
                                                                "type": "number", 
                                                                "example": 287912000000,
                                                                "description": "総負債"
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
                }
            },
            "/analysts": {
                "get": {
                    "summary": "アナリスト予想取得",
                    "description": "指定されたティッカーシンボルのアナリスト予想情報を取得します",
                    "parameters": [
                        {
                            "name": "ticker",
                            "in": "query",
                            "required": True,
                            "description": "ティッカーシンボル（例: AAPL, MSFT, 7203.T）",
                            "schema": {"type": "string"}
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
                                            "symbol": {
                                                "type": "string", 
                                                "example": "AAPL",
                                                "description": "ティッカーシンボル"
                                            },
                                            "analystRecommendations": {
                                                "type": "object",
                                                "description": "アナリスト推奨情報",
                                                "properties": {
                                                    "strongBuy": {
                                                        "type": "number", 
                                                        "example": 15,
                                                        "description": "強力買い推奨数"
                                                    },
                                                    "buy": {
                                                        "type": "number", 
                                                        "example": 20,
                                                        "description": "買い推奨数"
                                                    },
                                                    "hold": {
                                                        "type": "number", 
                                                        "example": 8,
                                                        "description": "ホールド推奨数"
                                                    },
                                                    "meanRecommendation": {
                                                        "type": "string", 
                                                        "example": "Buy",
                                                        "description": "平均推奨（Strong Buy, Buy, Hold, Underperform, Sell）"
                                                    },
                                                    "targetMean": {
                                                        "type": "number", 
                                                        "example": 225.50,
                                                        "description": "平均目標株価"
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