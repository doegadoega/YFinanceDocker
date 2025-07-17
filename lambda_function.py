import json
import yfinance as yf
# import pandas as pd
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
        
        # ティッカーシンボルを取得
        ticker = path_parameters.get('ticker', '').upper()
        if not ticker:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'ティッカーシンボルが必要です'})
            }
        
        # リソースごとの処理
        if '/price/' in resource:
            result = get_stock_price_api(ticker)
        elif '/info/' in resource:
            result = get_stock_info_api(ticker)
        elif '/history/' in resource:
            period = query_parameters.get('period', '1mo')
            result = get_stock_history_api(ticker, period)
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
        
        # DataFrameを直接処理せずに、yfinanceから返されるデータを変換
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