#!/usr/bin/env python3
"""
YFinance CLI ツール
コマンドラインから株式データを取得・分析する
"""

import argparse
import yfinance as yf
import pandas as pd
import sys
import json
from datetime import datetime

def get_stock_price(ticker):
    """現在の株価を取得"""
    try:
        stock = yf.Ticker(ticker)
        current_price = stock.info.get('currentPrice', stock.info.get('regularMarketPrice'))
        return current_price
    except Exception as e:
        print(f"エラー: {e}")
        return None

def get_stock_history(ticker, period="1mo"):
    """株価履歴を取得"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        return data
    except Exception as e:
        print(f"エラー: {e}")
        return None

def get_stock_info(ticker):
    """株式情報を取得"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 必要な情報だけを抽出
        result = {
            'symbol': ticker,
            'name': info.get('longName', 'N/A'),
            'currentPrice': info.get('currentPrice', 'N/A'),
            'previousClose': info.get('previousClose', 'N/A'),
            'marketCap': info.get('marketCap', 'N/A'),
            'dividendYield': info.get('dividendYield', 'N/A'),
            'trailingPE': info.get('trailingPE', 'N/A'),
            'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh', 'N/A'),
            'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow', 'N/A')
        }
        return result
    except Exception as e:
        print(f"エラー: {e}")
        return None

def display_stock_info(ticker):
    """株式情報を表示"""
    info = get_stock_info(ticker)
    if not info:
        return
    
    print(f"\n=== {ticker} の情報 ===")
    print(f"会社名: {info['name']}")
    print(f"現在価格: ${info['currentPrice']}")
    print(f"前日終値: ${info['previousClose']}")
    print(f"時価総額: ${info['marketCap']:,}" if isinstance(info['marketCap'], (int, float)) else f"時価総額: {info['marketCap']}")
    print(f"配当利回り: {info['dividendYield']}")
    print(f"P/E比率: {info['trailingPE']}")
    print(f"52週高値: ${info['fiftyTwoWeekHigh']}")
    print(f"52週安値: ${info['fiftyTwoWeekLow']}")

def main():
    parser = argparse.ArgumentParser(description='YFinance CLI ツール')
    parser.add_argument('ticker', help='ティッカーシンボル（例：AAPL, MSFT, 7203.T）')
    parser.add_argument('--price', action='store_true', help='現在の株価を表示')
    parser.add_argument('--info', action='store_true', help='詳細情報を表示')
    parser.add_argument('--history', action='store_true', help='株価履歴を表示')
    parser.add_argument('--period', default='1mo', 
                       choices=['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'],
                       help='履歴の期間（デフォルト: 1mo）')
    parser.add_argument('--json', action='store_true', help='結果をJSON形式で出力')
    
    args = parser.parse_args()
    
    if not any([args.price, args.info, args.history]):
        # デフォルトで現在価格と基本情報を表示
        args.price = True
        args.info = True
    
    result = {}
    
    if args.price:
        price = get_stock_price(args.ticker)
        if price:
            if args.json:
                result['price'] = price
            else:
                print(f"{args.ticker} の現在価格: ${price:.2f}")
    
    if args.info:
        info = get_stock_info(args.ticker)
        if info:
            if args.json:
                result['info'] = info
            else:
                display_stock_info(args.ticker)
    
    if args.history:
        data = get_stock_history(args.ticker, args.period)
        if data is not None and not data.empty:
            if args.json:
                # DataFrameをJSON形式に変換
                # 日付インデックスを文字列に変換
                data.index = data.index.strftime('%Y-%m-%d')
                result['history'] = json.loads(data.to_json(orient='index'))
            else:
                print(f"\n=== {args.ticker} の株価履歴（{args.period}） ===")
                print(data[['Open', 'High', 'Low', 'Close', 'Volume']].tail(10))
        else:
            if not args.json:
                print("履歴データを取得できませんでした")
    
    # JSON形式で出力
    if args.json:
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 