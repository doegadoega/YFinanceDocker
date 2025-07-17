#!/bin/bash

# YFinance API デプロイスクリプト
# AWS SAM CLI を使用してLambda関数とAPI Gatewayをデプロイ

set -e

echo "=== YFinance API デプロイ開始 ==="

# AWS CLI と SAM CLI がインストールされているかチェック
if ! command -v aws &> /dev/null; then
    echo "エラー: AWS CLI がインストールされていません"
    echo "インストール方法: https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html"
    exit 1
fi

if ! command -v sam &> /dev/null; then
    echo "エラー: AWS SAM CLI がインストールされていません"
    echo "インストール方法: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "エラー: jq がインストールされていません（JSON処理用）"
    echo "インストール方法: https://stedolan.github.io/jq/download/"
    exit 1
fi

# AWS 認証情報の確認
echo "AWS 認証情報を確認しています..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "エラー: AWS認証情報が設定されていません"
    echo "aws configure を実行して認証情報を設定してください"
    exit 1
fi

CURRENT_USER=$(aws sts get-caller-identity --query "Arn" --output text)
echo "デプロイユーザー: $CURRENT_USER"

# S3バケット名を設定（デプロイパッケージ用）
BUCKET_NAME="yfinance-api-deploy-$(date +%s)"
STACK_NAME="yfinance-api-stack"
REGION=${AWS_DEFAULT_REGION:-ap-northeast-1}

echo "S3バケット: $BUCKET_NAME"
echo "CloudFormationスタック: $STACK_NAME"
echo "リージョン: $REGION"

# S3バケットを作成
echo "S3バケットを作成しています..."
if [ "$REGION" = "" ]; then
    aws s3 mb s3://$BUCKET_NAME
else
    aws s3 mb s3://$BUCKET_NAME --region $REGION
fi

# 既存のスタックが存在するかチェック
echo "既存のスタックを確認しています..."
if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION &> /dev/null; then
    echo "既存のスタックが見つかりました。更新モードでデプロイします..."
    DEPLOY_MODE="update"
else
    echo "新しいスタックを作成します..."
    DEPLOY_MODE="create"
fi

# SAM ビルド
echo "SAM ビルドを実行しています..."
sam build --use-container

# SAM デプロイ
echo "SAM デプロイを実行しています..."
sam deploy \
    --stack-name $STACK_NAME \
    --s3-bucket $BUCKET_NAME \
    --capabilities CAPABILITY_IAM \
    --region $REGION \
    --confirm-changeset \
    --no-fail-on-empty-changeset \
    --resolve-image-repos

# API Gateway URLを取得
echo "=== デプロイ完了 ==="
API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query "Stacks[0].Outputs[?OutputKey=='YFinanceApiUrl'].OutputValue" \
    --output text)

echo "API Gateway URL: $API_URL"

# Lambda関数の環境変数を更新
echo "Lambda関数の環境変数を更新しています..."
FUNCTION_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query "Stacks[0].Outputs[?OutputKey=='YFinanceFunctionName'].OutputValue" \
    --output text)

if [ ! -z "$FUNCTION_NAME" ] && [ "$FUNCTION_NAME" != "None" ]; then
    echo "Lambda関数名: $FUNCTION_NAME"
    
    # 現在の環境変数を取得
    CURRENT_ENV=$(aws lambda get-function-configuration --function-name $FUNCTION_NAME --region $REGION --query 'Environment.Variables' --output json 2>/dev/null || echo '{}')
    
    # 新しい環境変数を設定
    NEW_ENV=$(jq -nc --arg url "$API_URL" '
      {"PYTHONPATH":"/opt/python","API_GATEWAY_URL":$url}')
    
    echo "設定する環境変数: $NEW_ENV"
    
    # Lambda関数を更新（環境変数のJSON形式を修正）
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --region "$REGION" \
        --environment "Variables={PYTHONPATH=/opt/python,API_GATEWAY_URL=$API_URL}"
    
    echo "✅ 環境変数の更新が完了しました。"
    echo "   API_GATEWAY_URL: $API_URL"
else
    echo "❌ 警告: Lambda関数名を取得できませんでした。"
    echo "   手動で環境変数を設定してください:"
    echo "   aws lambda update-function-configuration --function-name <FUNCTION_NAME> --environment Variables='{\"API_GATEWAY_URL\":\"$API_URL\"}'"
fi

echo ""
echo "=== 全APIエンドポイント テスト用URL ==="
echo ""
echo "1. 銘柄検索:"
echo "   curl \"$API_URL/search?q=apple\""
echo "   curl \"$API_URL/search?q=microsoft&limit=5\""
echo "   curl \"$API_URL/search?q=トヨタ&region=JP\""
echo ""
echo "2. 詳細情報取得（全データ統合）:"
echo "   curl \"$API_URL/info?ticker=AAPL\""
echo "   curl \"$API_URL/info?ticker=AAPL&period=1y\""
echo "   curl \"$API_URL/info?ticker=7203.T&period=6mo\""
echo ""
echo "3. チャート生成:"
echo "   curl \"$API_URL/chart?ticker=AAPL\" --output aapl_chart.png"
echo "   curl \"$API_URL/chart?ticker=TSLA&period=1y&type=candle\" --output tsla_chart.png"
echo ""
echo "=== パラメータ説明 ==="
echo "・ticker: ティッカーシンボル（例: AAPL, MSFT, 7203.T）"
echo "・period: 期間（1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max）"
echo "・q: 検索キーワード"
echo "・limit: 検索結果件数（デフォルト: 10、最大: 10）"
echo "・region: 検索リージョン（US, JP）"
echo "・type: チャートタイプ（line, candle）"
echo "・size: チャートサイズ（例: 800x400）"
echo ""
echo "=== テスト実行例 ==="
echo "# 銘柄検索"
echo "curl \"$API_URL/search?q=apple&limit=5\" | jq"
echo ""
echo "# 統合情報取得（価格、履歴、ニュース、配当、オプション、財務、アナリスト全て）"
echo "curl \"$API_URL/info?ticker=AAPL&period=1y\" | jq"
echo ""
echo "# 日本株の情報を取得"
echo "curl \"$API_URL/info?ticker=7203.T\" | jq"
echo ""
echo "# チャートを画像で取得"
echo "curl \"$API_URL/chart?ticker=TSLA&period=1mo&type=candle\" --output tsla_chart.png"
echo ""
echo "デプロイが完了しました！"
echo "上記のcurlコマンドをコピー&ペーストしてテストしてください。"
echo ""
echo "=== Swagger (OpenAPI) 仕様書の自動生成 ==="
echo "Swagger仕様書を自動生成しています..."
python3 swagger_generator_advanced.py lambda_function.py "$API_URL"
echo ""
echo "=== Swagger UI の使用方法 ==="
echo "1. https://editor.swagger.io/ にアクセス"
echo "2. 生成された swagger.json をコピー&ペースト"
echo "3. または、PostmanでImport > Raw text で swagger.json をインポート"
echo ""
echo "=== 注意事項 ==="
echo "・すべてのエンドポイントでエラーが発生した場合は、Errorスキーマの形式でレスポンスが返されます"
echo "・レート制限: 各エンドポイント1000リクエスト/分、全体10000リクエスト/日"
echo "・CORS対応済み: ブラウザからの直接アクセスが可能"