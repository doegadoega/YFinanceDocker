#!/bin/bash

# Dockerテスト実行スクリプト
# YFinance Docker環境でのテストを実行（ローカルテスト用）

set -e

echo "🐳 YFinance Docker ローカルテストを開始します..."
echo "=============================================="

# 1. 基本的なサンプル実行
echo "📊 1. 基本的なサンプル実行"
echo "------------------------"
docker-compose run --rm yfinance-local python yfinance_sample.py

echo ""
echo "✅ 基本的なテスト完了"
echo ""

# 2. CLIツールのテスト
echo "🔧 2. CLIツールのテスト"
echo "---------------------"
echo "ヘルプ表示:"
docker-compose run --rm yfinance-local python yfinance_cli.py --help

echo ""
echo "Apple株の情報取得:"
docker-compose run --rm yfinance-local python yfinance_cli.py AAPL --price --info

echo ""
echo "✅ CLIツールテスト完了"
echo ""

# 3. 検索機能のテスト
echo "🔍 3. 検索機能のテスト"
echo "-------------------"
echo "Apple検索:"
docker-compose run --rm yfinance-local python yfinance_search.py Apple

echo ""
echo "✅ 検索機能テスト完了"
echo ""

# 4. ローカルテストの実行
echo "🧪 4. ローカルテストの実行"
echo "----------------------"
docker-compose run --rm yfinance-local python local_test.py

echo ""
echo "✅ ローカルテスト完了"
echo ""

# 5. 環境情報の確認
echo "🔍 5. 環境情報の確認"
echo "-----------------"
docker-compose run --rm yfinance-local python -c "
import os
print(f'実行モード: {os.getenv(\"EXECUTION_MODE\", \"未設定\")}')
print(f'API URL: {os.getenv(\"YFINANCE_API_URL\", \"未設定\")}')
print(f'Python バージョン: {os.popen(\"python --version\").read().strip()}')
"

echo ""
echo "🎉 すべてのDockerローカルテストが完了しました！"
echo "=============================================="
echo ""
echo "📋 テスト結果サマリー:"
echo "• 基本的なサンプル実行: ✅"
echo "• CLIツール機能: ✅"
echo "• 検索機能: ✅"
echo "• ローカルテスト: ✅"
echo "• 環境設定確認: ✅"
echo ""
echo "💡 個別テストを実行する場合:"
echo "• サンプル実行: docker-compose run --rm yfinance-local python yfinance_sample.py"
echo "• CLIツール: docker-compose run --rm yfinance-local python yfinance_cli.py AAPL --price --info"
echo "• 検索機能: docker-compose run --rm yfinance-local python yfinance_search.py Apple"
echo "• ローカルテスト: docker-compose run --rm yfinance-local python local_test.py"
echo ""
echo "📁 ファイル構成:"
echo "• Dockerfile: Lambda用（デプロイ用）"
echo "• Dockerfile.local: ローカルテスト用"
echo "• docker-compose.yml: 両方のサービスを定義" 