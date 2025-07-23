#!/bin/bash

# ローカルテスト用Dockerスクリプト
# Dockerfile.local + yfinance-localサービスでLambdaハンドラーを直接テスト

set -e

echo "🐳 YFinance Docker ローカルテストを開始します..."
docker-compose build yfinance-local

echo "Lambdaハンドラー直接テスト:"
docker-compose run --rm yfinance-local python -c "from lambda_function import lambda_handler; event = {'resource': '/ticker/basic', 'httpMethod': 'GET', 'queryStringParameters': {'ticker': 'AAPL'}}; print(lambda_handler(event, None))"

echo "✅ ローカルテスト完了"
echo "🧹 Dockerイメージ・コンテナのクリーンアップを実行します..."
docker-compose down --rmi all --volumes --remove-orphans

echo "🧹 クリーンアップ完了" 