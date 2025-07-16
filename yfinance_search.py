#!/usr/bin/env python3
"""
YFinance 銘柄検索ツール
キーワードで株式銘柄を検索する
"""

import argparse
import requests
import json
import pandas as pd
import sys


def search_stocks(query, limit=10, region='US'):
    """
    Yahoo Financeの検索APIを使用して銘柄を検索する
    
    Args:
        query (str): 検索キーワード
        limit (int): 結果の最大件数
        region (str): 検索リージョン（US, JP, など）
    
    Returns:
        list: 検索結果のリスト
    """
    base_url = "https://query1.finance.yahoo.com/v1/finance/search"
    
    # 地域に基づいてクエリパラメータを調整
    if region.upper() == 'JP':
        query_params = {
            'q': query,
            'quotesCount': limit,
            'newsCount': 0,
            'enableFuzzyQuery': True,
            'quotesQueryId': 'tss_match_phrase_query',
            'multiQuoteQueryId': 'multi_quote_single_token_query',
            'enableCb': True,
            'region': 'JP',
            'lang': 'ja-JP'
        }
    else:
        query_params = {
            'q': query,
            'quotesCount': limit,
            'newsCount': 0,
            'enableFuzzyQuery': True,
            'quotesQueryId': 'tss_match_phrase_query',
            'multiQuoteQueryId': 'multi_quote_single_token_query',
            'enableCb': True
        }
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36'
        }
        response = requests.get(base_url, params=query_params, headers=headers)
        data = response.json()
        
        if 'quotes' in data and data['quotes']:
            return data['quotes']
        else:
            return []
    except Exception as e:
        print(f"検索エラー: {e}")
        return []


def display_search_results(results):
    """
    検索結果を表形式で表示する
    
    Args:
        results (list): 検索結果のリスト
    """
    if not results:
        print("検索結果がありません")
        return
    
    # 表示するデータを整形
    data = []
    for item in results:
        symbol = item.get('symbol', 'N/A')
        name = item.get('shortname', item.get('longname', 'N/A'))
        exchange = item.get('exchange', 'N/A')
        type_disp = item.get('typeDisp', 'N/A')
        
        data.append({
            'シンボル': symbol,
            '名称': name,
            '取引所': exchange,
            '種類': type_disp
        })
    
    # DataFrameに変換して表示
    df = pd.DataFrame(data)
    print(df.to_string(index=False))


def format_results_for_json(results):
    """
    検索結果をJSON用に整形する
    
    Args:
        results (list): 検索結果のリスト
    
    Returns:
        list: 整形された結果のリスト
    """
    formatted = []
    for item in results:
        # 利用可能なすべての情報を抽出
        result = {
            'symbol': item.get('symbol', 'N/A'),
            'name': item.get('shortname', item.get('longname', 'N/A')),
            'exchange': item.get('exchange', 'N/A'),
            'exchange_display_name': item.get('exchDisp', 'N/A'),
            'type': item.get('typeDisp', 'N/A'),
            'quoteType': item.get('quoteType', 'N/A'),
            'score': item.get('score', 0),
            'isYahooFinance': item.get('isYahooFinance', False)
        }
        
        # 追加情報があれば追加
        if 'sector' in item:
            result['sector'] = item['sector']
        if 'industry' in item:
            result['industry'] = item['industry']
        if 'market' in item:
            result['market'] = item['market']
        
        formatted.append(result)
    return formatted


def main():
    parser = argparse.ArgumentParser(description='YFinance 銘柄検索ツール')
    parser.add_argument('query', help='検索キーワード')
    parser.add_argument('--limit', type=int, default=10, help='結果の最大件数（デフォルト: 10）')
    parser.add_argument('--region', default='US', choices=['US', 'JP'], help='検索リージョン（デフォルト: US）')
    parser.add_argument('--json', action='store_true', help='結果をJSON形式で出力')
    parser.add_argument('--pretty', action='store_true', help='JSONを整形して出力（--jsonと併用）')
    
    args = parser.parse_args()
    
    results = search_stocks(args.query, args.limit, args.region)
    
    if args.json:
        # JSON形式で出力
        output = {
            'query': args.query,
            'region': args.region,
            'count': len(results),
            'timestamp': pd.Timestamp.now().isoformat(),
            'results': format_results_for_json(results)
        }
        
        # 整形オプションの処理
        indent = 2 if args.pretty else None
        print(json.dumps(output, indent=indent))
    else:
        # 通常の表示
        print(f"「{args.query}」の検索結果（リージョン: {args.region}）:")
        display_search_results(results)


if __name__ == "__main__":
    main() 