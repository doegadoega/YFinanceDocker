#!/usr/bin/env python3
"""
YFinance サンプルコード - 新API対応版
株式データの取得と包括的な分析を行う（ローカル実行とAPI実行の両方をサポート）
"""

import yfinance as yf
import matplotlib.pyplot as plt
import requests
import json
from datetime import datetime, timedelta

# APIエンドポイント設定
API_BASE_URL = "https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod"

def get_stock_data_local(ticker, period="1y"):
    """
    指定されたティッカーシンボルの株式データをローカルで取得
    
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

def get_comprehensive_data_api(ticker):
    """
    新しいAPIから包括的な株式データを取得
    
    Args:
        ticker (str): ティッカーシンボル
    
    Returns:
        dict: 包括的な株式データ
    """
    try:
        url = f"{API_BASE_URL}/info"
        params = {"ticker": ticker}
        
        print(f"API呼び出し中: {url}")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"APIエラー: {response.status_code}")
            print(f"レスポンス: {response.text}")
            return None
            
    except Exception as e:
        print(f"API呼び出しエラー: {e}")
        return None

def search_stocks_api(query, region="US"):
    """
    新しいAPIで株式を検索
    
    Args:
        query (str): 検索クエリ
        region (str): 検索地域
    
    Returns:
        dict: 検索結果
    """
    try:
        url = f"{API_BASE_URL}/search"
        params = {"q": query, "region": region}
        
        print(f"株式検索中: {query} (地域: {region})")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"検索APIエラー: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"検索APIエラー: {e}")
        return None

def display_stock_info_local(ticker):
    """
    株式の基本情報をローカルで表示
    
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
        print(f"現在価格: ${info.get('currentPrice', 'N/A')}")
        print(f"時価総額: ${info.get('marketCap', 'N/A'):,}" if info.get('marketCap') else "時価総額: N/A")
        print(f"配当利回り: {info.get('dividendYield', 'N/A')}")
        
    except Exception as e:
        print(f"エラー: {e}")

def display_comprehensive_info_api(data):
    """
    APIから取得した包括的な株式情報を表示
    
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
        print(f"従業員数: {info.get('fullTimeEmployees', 'N/A'):,}" if info.get('fullTimeEmployees') else "従業員数: N/A")
    
    # 価格情報
    if data.get('price'):
        price = data['price']
        print(f"\n--- 価格情報 ---")
        print(f"現在価格: {price.get('current_price', 'N/A')} {price.get('currency', 'USD')}")
        if price.get('price_change'):
            direction = "↑" if price.get('price_change_direction') == 'up' else "↓" if price.get('price_change_direction') == 'down' else "→"
            print(f"変化: {price['price_change']:+.2f} ({price.get('price_change_percent', 0):+.2f}%) {direction}")
    
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
                        if latest_revenue:
                            print(f"売上高: {latest_revenue:,.0f}" if isinstance(latest_revenue, (int, float)) else f"売上高: {latest_revenue}")
                    break
    
    # 株価履歴
    if data.get('history') and isinstance(data['history'], list):
        print(f"\n--- 直近の株価履歴 ---")
        recent_data = data['history'][-5:] if len(data['history']) >= 5 else data['history']
        for day in recent_data:
            print(f"{day.get('date', 'N/A')}: 終値 {day.get('close', 'N/A')} (出来高: {day.get('volume', 0):,})")

def display_search_results_api(results):
    """
    API検索結果を表示
    
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
        
        if result.get('current_price'):
            price_info = f"   価格: {result['current_price']} {result.get('currency', 'USD')}"
            if result.get('price_change'):
                direction = "↑" if result.get('price_change_direction') == 'up' else "↓" if result.get('price_change_direction') == 'down' else "→"
                price_info += f" ({result['price_change']:+.2f}, {result.get('price_change_percent', 0):+.2f}% {direction})"
            print(price_info)

# 従来の関数（後方互換性のため）
def get_stock_data(ticker, period="1y"):
    """後方互換性のための関数"""
    return get_stock_data_local(ticker, period)

def display_stock_info(ticker):
    """後方互換性のための関数"""
    return display_stock_info_local(ticker)

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
    """メイン関数 - 新API機能のデモ"""
    print("YFinance サンプルプログラム - 新API対応版")
    print("=" * 60)
    
    # 1. 株式検索のデモ
    print("\n1. 株式検索機能のデモ")
    print("-" * 30)
    
    # Apple を検索
    search_results = search_stocks_api("Apple", "US")
    if search_results:
        display_search_results_api(search_results)
    
    # 日本株を検索
    search_results_jp = search_stocks_api("Toyota", "JP")
    if search_results_jp:
        display_search_results_api(search_results_jp)
    
    # 2. 包括的データ取得のデモ（API）
    print("\n\n2. 包括的データ取得のデモ（新API）")
    print("-" * 40)
    
    # Apple の包括的データを取得
    print("\nApple (AAPL) の包括的データを取得中...")
    comprehensive_data = get_comprehensive_data_api("AAPL")
    if comprehensive_data:
        display_comprehensive_info_api(comprehensive_data)
    
    # Microsoft の包括的データを取得
    print("\nMicrosoft (MSFT) の包括的データを取得中...")
    comprehensive_data_msft = get_comprehensive_data_api("MSFT")
    if comprehensive_data_msft:
        display_comprehensive_info_api(comprehensive_data_msft)
    
    # 3. 従来のローカル実行との比較
    print("\n\n3. 従来のローカル実行（比較用）")
    print("-" * 35)
    
    # ローカルでのAppleデータ取得
    print("\nアップル（AAPL）のローカルデータを取得中...")
    aapl_data = get_stock_data_local("AAPL", "1y")
    
    if aapl_data is not None:
        print(f"取得完了: {len(aapl_data)} 日分のデータ")
        print(f"最新の終値: ${aapl_data['Close'].iloc[-1]:.2f}")
        
        # 基本情報を表示
        display_stock_info_local("AAPL")
        
        # リターンを計算
        returns = calculate_returns(aapl_data)
        if returns:
            print(f"\n=== リターン分析 ===")
            print(f"年率リターン: {returns['annual_return']:.2%}")
            print(f"年率ボラティリティ: {returns['volatility']:.2%}")
    
    # 4. 日本株のデモ
    print("\n\n4. 日本株のデモ")
    print("-" * 20)
    
    # トヨタ自動車の包括的データ（API）
    print("\nトヨタ自動車（7203.T）の包括的データを取得中...")
    toyota_comprehensive = get_comprehensive_data_api("7203.T")
    if toyota_comprehensive:
        display_comprehensive_info_api(toyota_comprehensive)
    
    # ローカルでのトヨタデータ取得
    print("\nトヨタ自動車（7203.T）のローカルデータを取得中...")
    toyota_data = get_stock_data_local("7203.T", "1y")
    
    if toyota_data is not None:
        print(f"取得完了: {len(toyota_data)} 日分のデータ")
        print(f"最新の終値: ¥{toyota_data['Close'].iloc[-1]:.2f}")
        
        # 基本情報を表示
        display_stock_info_local("7203.T")
    
    print("\n" + "=" * 60)
    print("デモ完了")
    print("\n新API の特徴:")
    print("• 17種類の包括的な金融データ")
    print("• 高速な株式検索機能")
    print("• ESG情報、財務諸表、株主情報など")
    print("• JSON形式でのデータ取得")
    print("• 複数地域での検索対応")
    print("\nAPI エンドポイント:")
    print(f"• 検索: {API_BASE_URL}/search")
    print(f"• 包括的データ: {API_BASE_URL}/info")
    print(f"• チャートデータ: {API_BASE_URL}/chart")

if __name__ == "__main__":
    main() 