import json
import yfinance as yf
from datetime import datetime
import traceback


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
    """銘柄検索（API用）"""
    try:
        import requests
        
        limit = int(query_parameters.get('limit', 10))
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
            for quote in data['quotes']:
                results.append({
                    'symbol': quote.get('symbol', ''),
                    'name': quote.get('longname', quote.get('shortname', '')),
                    'exchange': quote.get('exchange', ''),
                    'type': quote.get('quoteType', ''),
                    'score': quote.get('score', 0)
                })
            
            return {
                'query': query,
                'region': region,
                'results': results,
                'count': len(results),
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'query': query,
                'region': region,
                'results': [],
                'count': 0,
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