#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APIロジック直接テストスクリプト
Webサーバーを使わず、lambda_function.pyの各関数を直接呼び出してテストします
"""

import json
import os
from datetime import datetime
from lambda_function import (
    get_stock_info_api,
    search_stocks_api,
    get_stock_basic_info_api,
    get_stock_price_api,
    get_stock_history_api,
    get_stock_financials_api,
    get_stock_analysts_api,
    get_stock_holders_api,
    get_stock_events_api,
    get_stock_news_api,
    get_stock_options_api,
    get_stock_sustainability_api,
    get_stock_home_api,
    get_stock_rankings_api,
    get_sector_rankings_api,
    get_crypto_rankings_api,
    get_markets_indices_api,
    get_markets_currencies_api,
    get_markets_commodities_api,
    get_markets_status_api,
    lamuda_get_rss_news_api
)

def save_result(name, data, testdir):
    """テスト結果をJSONファイルに保存"""
    try:
        with open(os.path.join(testdir, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"    保存エラー: {e}")
        return False

def test_function(name, func, save_dir):
    """個別関数のテスト実行"""
    print(f"Testing: {name:20s} ... ", end="", flush=True)
    
    try:
        # 関数実行
        data = func()
        
        # 結果保存
        if save_result(name, data, save_dir):
            # 成功判定
            if data and not data.get("error"):
                print("✓ SUCCESS")
                return True, "success"
            else:
                error_msg = data.get("error", "Unknown error") if data else "No data returned"
                print(f"✗ FAILED (API Error: {error_msg})")
                return False, f"api_error: {error_msg}"
        else:
            print("✗ FAILED (Save Error)")
            return False, "save_error"
            
    except Exception as e:
        print(f"✗ EXCEPTION: {e}")
        return False, f"exception: {e}"

def test_enhanced_home_features(save_dir):
    """拡張されたホーム機能の詳細テスト"""
    print(f"Testing: enhanced_home    ... ", end="", flush=True)
    
    try:
        # 拡張されたホーム情報取得
        home_data = get_stock_home_api()
        
        if not home_data or home_data.get("error"):
            print(f"✗ FAILED (Home API Error: {home_data.get('error', 'Unknown error')})")
            return False, "home_api_error"
        
        # 拡張機能の存在確認
        enhanced_features = home_data.get('enhanced_features', [])
        expected_features = [
            'news_rss_integration',
            'stock_rankings_integration', 
            'sector_rankings_integration',
            'major_indices_integration',
            'currency_rates_integration',
            'commodity_prices_integration',
            'market_status_integration'
        ]
        
        # 各セクションの詳細チェック
        sections_report = {
            'enhanced_features_count': len(enhanced_features),
            'expected_features_count': len(expected_features),
            'missing_features': [f for f in expected_features if f not in enhanced_features],
            'sections_status': {}
        }
        
        # 各セクションの状態をチェック
        sections = {
            'latest_news': home_data.get('latest_news', {}),
            'stock_rankings': home_data.get('stock_rankings', {}),
            'sector_rankings': home_data.get('sector_rankings', {}),
            'major_indices': home_data.get('major_indices', {}),
            'currency_rates': home_data.get('currency_rates', {}),
            'commodity_prices': home_data.get('commodity_prices', {}),
            'market_status': home_data.get('market_status', {})
        }
        
        for section_name, section_data in sections.items():
            if section_data.get('error'):
                sections_report['sections_status'][section_name] = f"ERROR: {section_data['error']}"
            elif not section_data:
                sections_report['sections_status'][section_name] = "MISSING"
            else:
                # データ数をカウント
                data_count = 0
                if section_name == 'latest_news':
                    data_count = section_data.get('count', 0)
                elif section_name == 'stock_rankings':
                    data_count = len(section_data.get('top_gainers', [])) + len(section_data.get('top_losers', []))
                elif section_name == 'sector_rankings':
                    data_count = len(section_data.get('top_sectors', []))
                elif section_name == 'major_indices':
                    data_count = len(section_data.get('indices', []))
                elif section_name == 'currency_rates':
                    data_count = len(section_data.get('major_pairs', []))
                elif section_name == 'commodity_prices':
                    data_count = len(section_data.get('commodities', []))
                elif section_name == 'market_status':
                    data_count = len(section_data.get('markets', []))
                
                sections_report['sections_status'][section_name] = f"OK ({data_count} items)"
        
        # 詳細レポートを作成
        detailed_report = {
            'original_home_data': home_data,
            'enhanced_features_analysis': sections_report,
            'test_timestamp': datetime.now().isoformat(),
            'overall_status': 'SUCCESS' if not sections_report['missing_features'] else 'PARTIAL'
        }
        
        # 結果保存
        if save_result("enhanced_home_detailed", detailed_report, save_dir):
            if sections_report['missing_features']:
                print(f"⚠ PARTIAL (missing: {len(sections_report['missing_features'])} features)")
                return True, f"partial_success: missing {sections_report['missing_features']}"
            else:
                print("✓ SUCCESS (all enhanced features working)")
                return True, "full_success"
        else:
            print("✗ FAILED (Save Error)")
            return False, "save_error"
            
    except Exception as e:
        print(f"✗ EXCEPTION: {e}")
        return False, f"exception: {e}"

def main():
    """メイン関数"""
    print("=" * 60)
    print("🚀 APIロジック直接テスト開始")
    print("=" * 60)
    
    # テスト結果保存ディレクトリ作成
    testdir = f"./test/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(testdir, exist_ok=True)
    print(f"📁 結果保存先: {testdir}")
    print()
    
    # テストケース定義
    tests = [
        # 検索系
        ("search", lambda: search_stocks_api("Apple", {"region": "US"})),
        
        # 個別銘柄系
        ("tickerDetail", lambda: get_stock_info_api("AAPL", "1mo")),
        ("basic", lambda: get_stock_basic_info_api("AAPL")),
        ("price", lambda: get_stock_price_api("AAPL")),
        ("history", lambda: get_stock_history_api("AAPL", "1mo")),
        ("financials", lambda: get_stock_financials_api("AAPL")),
        ("analysts", lambda: get_stock_analysts_api("AAPL")),
        ("holders", lambda: get_stock_holders_api("AAPL")),
        ("events", lambda: get_stock_events_api("AAPL")),
        ("news", lambda: get_stock_news_api("AAPL")),
        ("options", lambda: get_stock_options_api("AAPL")),
        ("sustainability", lambda: get_stock_sustainability_api("AAPL")),
        
        # ホーム・ニュース系
        ("home", get_stock_home_api),
        ("news_rss", lambda: lamuda_get_rss_news_api({'limit': '5'})),
        
        # ランキング系
        ("rankings_stocks", lambda: get_stock_rankings_api({'type': 'gainers', 'market': 'sp500', 'limit': '5'})),
        ("rankings_sectors", lambda: get_sector_rankings_api({'limit': '5'})),
        ("rankings_crypto", lambda: get_crypto_rankings_api({'limit': '5', 'sort': 'change'})),
        
        # マーケット系
        ("markets_indices", lambda: get_markets_indices_api({})),
        ("markets_currencies", lambda: get_markets_currencies_api({})),
        ("markets_commodities", lambda: get_markets_commodities_api({})),
        ("markets_status", lambda: get_markets_status_api({})),
    ]
    
    # テスト実行
    results = []
    total = len(tests)
    passed = 0
    failed = 0
    
    for name, func in tests:
        success, message = test_function(name, func, testdir)
        results.append((name, success, message))
        
        if success:
            passed += 1
        else:
            failed += 1
    
    # 🆕 拡張されたホーム機能の詳細テスト
    print("\n--- 拡張機能詳細テスト ---")
    enhanced_success, enhanced_message = test_enhanced_home_features(testdir)
    results.append(("enhanced_home", enhanced_success, enhanced_message))
    total += 1
    if enhanced_success:
        passed += 1
    else:
        failed += 1
    
    # 結果サマリー
    print()
    print("=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    print(f"🔢 総テスト数: {total}")
    print(f"✅ 成功: {passed}")
    print(f"❌ 失敗: {failed}")
    print(f"📈 成功率: {(passed/total*100):.1f}%")
    print()
    
    # 拡張機能の特別レポート
    if enhanced_success:
        if "partial_success" in enhanced_message:
            print("⚠️  拡張機能: 部分的成功 - 一部の機能に問題があります")
        else:
            print("🎉 拡張機能: 完全成功 - 全ての新機能が正常に動作しています！")
    else:
        print("❌拡張機能: 失敗 - 新機能に問題があります")
    print()
    
    # 失敗したテストの詳細
    if failed > 0:
        print("❌ 失敗したテスト:")
        for name, success, message in results:
            if not success:
                print(f"   - {name}: {message}")
        print()
    
    print(f"📁 詳細結果: {testdir}")
    print("=" * 60)
    print("✨ テスト完了")
    print("=" * 60)
    
    # 終了コード
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main()) 