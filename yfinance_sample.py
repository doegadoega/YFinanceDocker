#!/usr/bin/env python3
"""
YFinance サンプルコード
株式データの取得と基本的な分析を行う
"""

import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def get_stock_data(ticker, period="1y"):
    """
    指定されたティッカーシンボルの株式データを取得
    
    Args:
        ticker (str): ティッカーシンボル（例：AAPL, MSFT, 7203.T）
        period (str): 取得期間（1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max）
    
    Returns:
        pandas.DataFrame: 株式データ
    """
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        return data
    except Exception as e:
        print(f"エラー: {e}")
        return None

def display_stock_info(ticker):
    """
    株式の基本情報を表示
    
    Args:
        ticker (str): ティッカーシンボル
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        print(f"\n=== {ticker} の基本情報 ===")
        print(f"会社名: {info.get('longName', 'N/A')}")
        print(f"業界: {info.get('industry', 'N/A')}")
        print(f"セクター: {info.get('sector', 'N/A')}")
        print(f"現在価格: ${info.get('currentPrice', 'N/A')}")
        print(f"時価総額: ${info.get('marketCap', 'N/A'):,}" if info.get('marketCap') else "時価総額: N/A")
        print(f"配当利回り: {info.get('dividendYield', 'N/A')}")
        
    except Exception as e:
        print(f"エラー: {e}")

def plot_stock_price(data, ticker):
    """
    株式価格の推移をプロット
    
    Args:
        data (pandas.DataFrame): 株式データ
        ticker (str): ティッカーシンボル
    """
    if data is None or data.empty:
        print("データがありません")
        return
    
    plt.figure(figsize=(12, 6))
    plt.plot(data.index, data['Close'], label='終値')
    plt.title(f'{ticker} の株価推移')
    plt.xlabel('日付')
    plt.ylabel('価格 ($)')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def calculate_returns(data):
    """
    リターンを計算
    
    Args:
        data (pandas.DataFrame): 株式データ
    
    Returns:
        dict: 各種リターン情報
    """
    if data is None or data.empty:
        return None
    
    # 日次リターン
    daily_returns = data['Close'].pct_change()
    
    # 累積リターン
    cumulative_returns = (1 + daily_returns).cumprod() - 1
    
    # 年率リターン（252営業日を想定）
    annual_return = (1 + cumulative_returns.iloc[-1]) ** (252 / len(data)) - 1
    
    # ボラティリティ（年率）
    volatility = daily_returns.std() * (252 ** 0.5)
    
    return {
        'daily_returns': daily_returns,
        'cumulative_returns': cumulative_returns,
        'annual_return': annual_return,
        'volatility': volatility
    }

def main():
    """メイン関数"""
    print("YFinance サンプルプログラム")
    print("=" * 50)
    
    # 使用例1: アップルの株式データを取得
    print("\n1. アップル（AAPL）の株式データを取得中...")
    aapl_data = get_stock_data("AAPL", "1y")
    
    if aapl_data is not None:
        print(f"取得完了: {len(aapl_data)} 日分のデータ")
        print(f"最新の終値: ${aapl_data['Close'].iloc[-1]:.2f}")
        
        # 基本情報を表示
        display_stock_info("AAPL")
        
        # リターンを計算
        returns = calculate_returns(aapl_data)
        if returns:
            print(f"\n=== リターン分析 ===")
            print(f"年率リターン: {returns['annual_return']:.2%}")
            print(f"年率ボラティリティ: {returns['volatility']:.2%}")
        
        # プロット（コメントアウト - インタラクティブ環境で実行）
        # plot_stock_price(aapl_data, "AAPL")
    
    # 使用例2: 日本の株式（トヨタ自動車）
    print("\n2. トヨタ自動車（7203.T）の株式データを取得中...")
    toyota_data = get_stock_data("7203.T", "1y")
    
    if toyota_data is not None:
        print(f"取得完了: {len(toyota_data)} 日分のデータ")
        print(f"最新の終値: ¥{toyota_data['Close'].iloc[-1]:.2f}")
        
        # 基本情報を表示
        display_stock_info("7203.T")
    
    print("\nプログラム終了")

if __name__ == "__main__":
    main() 