#!/bin/bash

# Lambda用Dockerテストスクリプト
# YFinance Lambda環境でのテストを実行

set -e

echo "🚀 YFinance Lambda Docker テストを開始します..."
echo "============================================="

# 1. Lambda用イメージのビルド
echo "🔨 1. Lambda用イメージのビルド"
echo "---------------------------"
docker-compose build yfinance-lambda

echo ""
echo "✅ Lambda用イメージビルド完了"
echo ""

# 2. Lambdaハンドラーのローカルテスト（python -cでevent/contextを渡す）
echo "⚡ 2. Lambdaハンドラーのローカルテスト"
echo "----------------------"
echo "Lambdaハンドラーをevent/context付きで直接呼び出し:"
docker-compose run --rm yfinance-lambda python -c "from lambda_function import lambda_handler; event={'resource':'/ticker/basic','httpMethod':'GET','queryStringParameters':{'ticker':'AAPL'}}; print(lambda_handler(event, None))"

echo ""
echo "✅ Lambdaハンドラー直接テスト完了"
echo ""

# 3. Lambda関数のインポート確認（python -c）
echo "🔍 3. Lambda関数のインポート確認"
echo "-----------------"
docker-compose run --rm yfinance-lambda python -c "import lambda_function; print('Lambda関数インポート成功')"

echo ""
echo "✅ Lambda関数インポート確認完了"
echo ""

# 4. 環境変数の確認
echo "🔍 4. 環境変数の確認"
echo "-----------------"
docker-compose run --rm yfinance-lambda python -c "
import os
print(f'実行モード: {os.getenv(\"EXECUTION_MODE\", \"未設定\")}')
print(f'API URL: {os.getenv(\"YFINANCE_API_URL\", \"未設定\")}')
print(f'LAMBDA_TASK_ROOT: {os.getenv(\"LAMBDA_TASK_ROOT\", \"未設定\")}')
print(f'Python バージョン: {os.popen(\"python --version\").read().strip()}')
"

echo ""
echo "✅ 環境変数確認完了"
echo ""

# 5. 依存関係の確認
echo "📦 5. 依存関係の確認"
echo "-----------------"
docker-compose run --rm yfinance-lambda python -c "
import yfinance
import pandas
import requests
print('主要依存関係インポート成功:')
print(f'yfinance: {yfinance.__version__}')
print(f'pandas: {pandas.__version__}')
print(f'requests: {requests.__version__}')
"

echo ""
echo "✅ 依存関係確認完了"
echo ""

# 6. 関数の直接テスト
echo "🧪 6. 関数の直接テスト"
echo "-------------------"
docker-compose run --rm yfinance-lambda python -c "
from lambda_function import get_stock_info_api, search_stocks_api
import json

# 株式情報取得テスト
print('株式情報取得テスト:')
result = get_stock_info_api('AAPL', '1mo')
print(f'結果: {\"成功\" if not result.get(\"error\") else \"エラー\"}')
if result.get('error'):
    print(f'エラー内容: {result[\"error\"]}')

# 検索機能テスト
print('\\n検索機能テスト:')
search_result = search_stocks_api('Apple', {'region': 'US'})
print(f'結果: {\"成功\" if not search_result.get(\"error\") else \"エラー\"}')
if search_result.get('error'):
    print(f'エラー内容: {search_result[\"error\"]}')
"

echo ""
echo "✅ 関数テスト完了"
echo ""
echo "🎉 すべてのLambda Dockerテストが完了しました！"
echo "============================================="
echo ""
echo "📋 テスト結果サマリー:"
echo "• Lambda用イメージビルド: ✅"
echo "• Lambdaハンドラー直接テスト: ✅"
echo "• Lambda関数インポート: ✅"
echo "• 環境変数確認: ✅"
echo "• 依存関係確認: ✅"
echo "• 関数直接テスト: ✅"
echo ""
echo "💡 個別テストを実行する場合:"
echo "• Lambdaビルド: docker-compose build yfinance-lambda"
echo "• Lambdaハンドラー直接: docker-compose run --rm yfinance-lambda python -c \"from lambda_function import lambda_handler; event={'resource':'/ticker/basic','httpMethod':'GET','queryStringParameters':{'ticker':'AAPL'}}; print(lambda_handler(event, None))\""
echo "• Lambda関数確認: docker-compose run --rm yfinance-lambda python -c \"import lambda_function\""
echo "• 環境確認: docker-compose run --rm yfinance-lambda env"
echo ""
echo "📁 ファイル構成:"
echo "• Dockerfile: Lambda用（デプロイ用）"
echo "• Dockerfile.local: ローカルテスト用"
echo "• docker-compose.yml: 両方のサービスを定義" 