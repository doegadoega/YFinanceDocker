#!/usr/bin/env python3
"""
YFinance 銘柄検索ツール - 新API対応版
キーワードで株式銘柄を検索する（ローカル実行とAPI実行の両方をサポート）
"""

import argparse
import requests
import json
import pandas as pd
import sys

# 新API設定
API_BASE_URL = "https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod"

def search_stocks_api(query, region='US'):
    """
    新しいAPIを使用して銘柄を検索する
    
    Args:
        query (str): 検索キーワード
        region (str): 検索リージョン（US, JP, DE, CA, AU, GB, FR, IT, ES, KR, IN, HK, SG）
    
    Returns:
        dict: API応答データ
    """
    try:
        url = f"{API_BASE_URL}/search"
        params = {"q": query, "region": region}
        
        print(f"新API検索中: {query} (地域: {region})")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"APIエラー: {response.status_code}")
            print(f"レスポンス: {response.text}")
            return {"error": f"APIエラー: {response.status_code}"}
            
    except Exception as e:
        print(f"API呼び出しエラー: {e}")
        return {"error": str(e)}

def search_stocks_local(query, limit=10, region='US'):
    """
    Yahoo Financeの検索APIを直接使用して銘柄を検索する（ローカル実行）
    
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
        response = requests.get(base_url, params=query_params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        quotes = data.get('quotes', [])
        return quotes
    except requests.RequestException as e:
        print(f"検索APIエラー: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSONデコードエラー: {e}")
        return []

def display_search_results_api(data):
    """
    新API検索結果を表示
    
    Args:
        data (dict): API応答データ
    """
    if not data or 'error' in data:
        print(f"検索エラー: {data.get('error', '不明なエラー')}")
        return
    
    print(f"\n=== 検索結果: '{data.get('query', 'N/A')}' ({data.get('region', 'N/A')}) ===")
    print(f"件数: {data.get('count', 0)}")
    
    for i, result in enumerate(data.get('results', []), 1):
        print(f"\n{i}. {result.get('symbol', 'N/A')} - {result.get('name', 'N/A')}")
        print(f"   取引所: {result.get('exchange', 'N/A')} | タイプ: {result.get('type', 'N/A')}")
        
        if result.get('current_price'):
            price_info = f"   価格: {result['current_price']} {result.get('currency', 'USD')}"
            if result.get('price_change'):
                direction = "↑" if result.get('price_change_direction') == 'up' else "↓" if result.get('price_change_direction') == 'down' else "→"
                price_info += f" ({result['price_change']:+.2f}, {result.get('price_change_percent', 0):+.2f}% {direction})"
            print(price_info)
        
        if result.get('market_cap'):
            print(f"   時価総額: {result['market_cap']:,}")

def display_search_results_local(results):
    """
    ローカル検索結果を表示
    
    Args:
        results (list): 検索結果のリスト
    """
    if not results:
        print("検索結果が見つかりませんでした。")
        return
    
    print(f"\n件数: {len(results)}")
    print("-" * 80)
    
    for i, item in enumerate(results, 1):
        print(f"{i}. {item.get('symbol', 'N/A')} - {item.get('shortname', item.get('longname', 'N/A'))}")
        print(f"   取引所: {item.get('exchange', 'N/A')} ({item.get('exchDisp', 'N/A')})")
        print(f"   タイプ: {item.get('typeDisp', 'N/A')}")
        
        # 追加情報があれば表示
        if item.get('sector'):
            print(f"   セクター: {item['sector']}")
        if item.get('industry'):
            print(f"   業界: {item['industry']}")
        
        print()

# 後方互換性のための関数
def search_stocks(query, limit=10, region='US'):
    """後方互換性のための関数"""
    return search_stocks_local(query, limit, region)

def display_search_results(results):
    """後方互換性のための関数"""
    return display_search_results_local(results)
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
    parser = argparse.ArgumentParser(description='YFinance 銘柄検索ツール - 新API対応版')
    parser.add_argument('query', help='検索キーワード')
    parser.add_argument('--limit', type=int, default=10, help='結果の最大件数（ローカル検索のみ、デフォルト: 10）')
    parser.add_argument('--region', default='US', 
                       choices=['US', 'CA', 'AU', 'DE', 'FR', 'GB', 'IT', 'ES', 'KR', 'JP', 'IN', 'HK', 'SG'],
                       help='検索リージョン（デフォルト: US）')
    parser.add_argument('--json', action='store_true', help='結果をJSON形式で出力')
    parser.add_argument('--pretty', action='store_true', help='JSONを整形して出力（--jsonと併用）')
    parser.add_argument('--api', action='store_true', help='新APIを使用（デフォルト）')
    parser.add_argument('--local', action='store_true', help='ローカル検索を使用')
    parser.add_argument('--both', action='store_true', help='両方の方法で検索して比較')
    
    args = parser.parse_args()
    
    # デフォルトは新API使用
    use_api = not args.local
    if args.both:
        use_api = True
    
    print(f"YFinance 銘柄検索ツール - 新API対応版")
    print("=" * 50)
    
    if args.both:
        # 両方の方法で検索
        print(f"\n【新API検索】")
        print("-" * 20)
        api_results = search_stocks_api(args.query, args.region)
        
        if args.json:
            print("=== 新API結果（JSON）===")
            indent = 2 if args.pretty else None
            print(json.dumps(api_results, indent=indent, ensure_ascii=False))
        else:
            display_search_results_api(api_results)
        
        print(f"\n【ローカル検索】")
        print("-" * 20)
        local_results = search_stocks_local(args.query, args.limit, args.region)
        
        if args.json:
            print("=== ローカル結果（JSON）===")
            local_output = {
                'query': args.query,
                'region': args.region,
                'count': len(local_results),
                'timestamp': pd.Timestamp.now().isoformat(),
                'results': format_results_for_json(local_results)
            }
            indent = 2 if args.pretty else None
            print(json.dumps(local_output, indent=indent, ensure_ascii=False))
        else:
            print(f"「{args.query}」の検索結果（リージョン: {args.region}）:")
            display_search_results_local(local_results)
    
    elif use_api:
        # 新API検索
        print(f"新APIで検索中...")
        results = search_stocks_api(args.query, args.region)
        
        if args.json:
            indent = 2 if args.pretty else None
            print(json.dumps(results, indent=indent, ensure_ascii=False))
        else:
            display_search_results_api(results)
    
    else:
        # ローカル検索
        print(f"ローカル検索中...")
        results = search_stocks_local(args.query, args.limit, args.region)
        
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
            print(json.dumps(output, indent=indent, ensure_ascii=False))
        else:
            # 通常の表示
            print(f"「{args.query}」の検索結果（リージョン: {args.region}）:")
            display_search_results_local(results)
    
    print(f"\n検索完了")
    if not args.both and use_api:
        print(f"使用API: {API_BASE_URL}/search")

if __name__ == "__main__":
    main() 