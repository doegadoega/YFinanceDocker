#!/usr/bin/env python3
"""
YFinance サンプルコード - 新API対応版
株式データの取得と包括的な分析を行う（Lambda関数を直接使用して統一）
"""

import yfinance as yf
import matplotlib.pyplot as plt
import requests
import os
import sys
from typing import Optional, Dict, Any, Union
from datetime import datetime
import pandas as pd

# Lambda関数から直接インポート（統一のため）
from lambda_function import (
    get_stock_info_api, 
    search_stocks_api, 
    serialize_for_json,
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

def get_stock_data_local(ticker: str, period: str = "1y") -> Optional[yf.Ticker]:
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
        if data.empty:
            print(f"警告: {ticker} のデータが見つかりませんでした")
            return None
        return data
    except Exception as e:
        print(f"エラー: {ticker} のデータ取得に失敗しました - {e}")
        return None

def get_comprehensive_data_api(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Lambda関数を直接使用して包括的な株式データを取得（完全統一）
    
    Args:
        ticker (str): ティッカーシンボル
    
    Returns:
        dict: 包括的な株式データ
    """
    try:
        # Lambda関数を直接呼び出し
        result = get_stock_info_api(ticker, '1mo')
        
        # 実行環境情報を追加
        if not result.get('error'):
            result['execution_info'] = get_execution_info(EXECUTION_MODE)
        
        return result
            
    except Exception as e:
        print(f"予期しないエラー: {e}")
        return {'error': f'データ取得エラー: {e}'}

def search_stocks_api_unified(query: str, region: str = "US") -> Optional[Dict[str, Any]]:
    """
    Lambda関数を直接使用して株式を検索（完全統一）
    
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

# 従来の関数（後方互換性のため）
def get_stock_data(ticker: str, period: str = "1y") -> Optional[yf.Ticker]:
    """後方互換性のための関数"""
    return get_stock_data_local(ticker, period)

def display_stock_info(ticker: str) -> None:
    """後方互換性のための関数"""
    return display_stock_info_local(ticker)

def plot_stock_price(data: yf.Ticker, ticker: str) -> None:
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
    
    # 通貨に応じたラベル設定
    if ticker.endswith('.T'):
        plt.ylabel('価格 (¥)')
    else:
        plt.ylabel('価格 ($)')
    
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def calculate_returns(data: yf.Ticker) -> Optional[Dict[str, Any]]:
    """
    リターンを計算
    
    Args:
        data (pandas.DataFrame): 株式データ
    
    Returns:
        dict: 各種リターン情報
    """
    if data is None or data.empty:
        return None
    
    try:
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
    except Exception as e:
        print(f"リターン計算エラー: {e}")
        return None

def main() -> None:
    """メイン関数 - Lambda関数を直接使用して完全統一"""
    # 実行環境情報を表示
    exec_info = get_execution_info(EXECUTION_MODE)
    print("YFinance サンプルプログラム - Lambda関数直接使用版")
    print("=" * 60)
    print(f"実行モード: {exec_info['mode']}")
    print(f"API URL: {API_BASE_URL}")
    print(f"実行時刻: {exec_info['timestamp']}")
    print("=" * 60)
    
    # 1. 株式検索のデモ（Lambda関数直接使用）
    print("\n1. 株式検索機能のデモ（Lambda関数直接使用）")
    print("-" * 50)
    
    # Apple を検索
    search_results = search_stocks_api_unified("Apple", "US")
    if search_results:
        display_search_results_api(search_results)
    
    # 日本株を検索
    search_results_jp = search_stocks_api_unified("Toyota", "JP")
    if search_results_jp:
        display_search_results_api(search_results_jp)
    
    # 2. 包括的データ取得のデモ（Lambda関数直接使用）
    print("\n\n2. 包括的データ取得のデモ（Lambda関数直接使用）")
    print("-" * 55)
    
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
        latest_close = aapl_data['Close'].iloc[-1]
        print(f"最新の終値: {format_currency(latest_close, 'USD')}")
        
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
    
    # トヨタ自動車の包括的データ（Lambda関数直接使用）
    print("\nトヨタ自動車（7203.T）の包括的データを取得中...")
    toyota_comprehensive = get_comprehensive_data_api("7203.T")
    if toyota_comprehensive:
        display_comprehensive_info_api(toyota_comprehensive)
    
    # ローカルでのトヨタデータ取得
    print("\nトヨタ自動車（7203.T）のローカルデータを取得中...")
    toyota_data = get_stock_data_local("7203.T", "1y")
    
    if toyota_data is not None:
        print(f"取得完了: {len(toyota_data)} 日分のデータ")
        latest_close = toyota_data['Close'].iloc[-1]
        print(f"最新の終値: {format_currency(latest_close, 'JPY')}")
        
        # 基本情報を表示
        display_stock_info_local("7203.T")
    
    print("\n" + "=" * 60)
    print("デモ完了")
    print("\n統一された特徴:")
    print("• Lambda関数を直接使用して完全統一")
    print("• 17種類の包括的な金融データ")
    print("• 高速な株式検索機能")
    print("• ESG情報、財務諸表、株主情報など")
    print("• JSON形式でのデータ取得")
    print("• 複数地域での検索対応")
    print("• 実行環境情報の自動付与")
    print("• 重複コードの排除")
    print(f"\n実行環境: {exec_info['mode']}")

if __name__ == "__main__":
    main() 