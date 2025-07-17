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
echo ""
echo "=== 全APIエンドポイント テスト用URL ==="
echo ""
echo "1. 株価取得:"
echo "   curl \"$API_URL/price?ticker=AAPL\""
echo "   curl \"$API_URL/price?ticker=MSFT\""
echo "   curl \"$API_URL/price?ticker=7203.T\""
echo ""
echo "2. 詳細情報取得:"
echo "   curl \"$API_URL/info?ticker=AAPL\""
echo "   curl \"$API_URL/info?ticker=GOOGL\""
echo "   curl \"$API_URL/info?ticker=6758.T\""
echo ""
echo "3. 株価履歴取得:"
echo "   curl \"$API_URL/history?ticker=AAPL\""
echo "   curl \"$API_URL/history?ticker=TSLA&period=1y\""
echo "   curl \"$API_URL/history?ticker=7203.T&period=6mo\""
echo "   curl \"$API_URL/history?ticker=NVDA&period=1mo\""
echo ""
echo "4. ニュース取得:"
echo "   curl \"$API_URL/news?ticker=AAPL\""
echo "   curl \"$API_URL/news?ticker=MSFT\""
echo "   curl \"$API_URL/news?ticker=7203.T\""
echo ""
echo "5. 配当情報取得:"
echo "   curl \"$API_URL/dividends?ticker=AAPL\""
echo "   curl \"$API_URL/dividends?ticker=MSFT\""
echo "   curl \"$API_URL/dividends?ticker=7203.T\""
echo ""
echo "6. オプション情報取得:"
echo "   curl \"$API_URL/options?ticker=AAPL\""
echo "   curl \"$API_URL/options?ticker=TSLA\""
echo "   curl \"$API_URL/options?ticker=NVDA\""
echo ""
echo "7. 財務情報取得:"
echo "   curl \"$API_URL/financials?ticker=AAPL\""
echo "   curl \"$API_URL/financials?ticker=MSFT\""
echo "   curl \"$API_URL/financials?ticker=7203.T\""
echo ""
echo "8. アナリスト予想取得:"
echo "   curl \"$API_URL/analysts?ticker=AAPL\""
echo "   curl \"$API_URL/analysts?ticker=AMZN\""
echo "   curl \"$API_URL/analysts?ticker=6758.T\""
echo ""
echo "9. 銘柄検索:"
echo "   curl \"$API_URL/search?q=apple\""
echo "   curl \"$API_URL/search?q=microsoft&limit=20\""
echo "   curl \"$API_URL/search?q=トヨタ&region=JP\""
echo "   curl \"$API_URL/search?q=sony&region=JP&limit=15\""
echo ""
echo "=== パラメータ説明 ==="
echo "・ticker: ティッカーシンボル（例: AAPL, MSFT, 7203.T）"
echo "・period: 期間（1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max）"
echo "・q: 検索キーワード"
echo "・limit: 検索結果件数（デフォルト: 10）"
echo "・region: 検索リージョン（US, JP）"
echo ""
echo "=== テスト実行例 ==="
echo "# アメリカ株の株価を取得"
echo "curl \"$API_URL/price?ticker=AAPL\" | jq"
echo ""
echo "# 日本株の詳細情報を取得"
echo "curl \"$API_URL/info?ticker=7203.T\" | jq"
echo ""
echo "# 1年分の株価履歴を取得"
echo "curl \"$API_URL/history?ticker=TSLA&period=1y\" | jq"
echo ""
echo "# 銘柄検索を実行"
echo "curl \"$API_URL/search?q=apple&limit=5\" | jq"
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