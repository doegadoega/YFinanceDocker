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
REGION=${AWS_DEFAULT_REGION:-us-east-1}

echo "S3バケット: $BUCKET_NAME"
echo "CloudFormationスタック: $STACK_NAME"
echo "リージョン: $REGION"

# S3バケットを作成
echo "S3バケットを作成しています..."
if [ "$REGION" = "us-east-1" ]; then
    aws s3 mb s3://$BUCKET_NAME
else
    aws s3 mb s3://$BUCKET_NAME --region $REGION
fi

# 既存のスタックを削除（存在する場合）
echo "既存のスタックをクリーンアップしています..."
aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION || true
echo "スタックの削除を待機中..."
aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME --region $REGION || true

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
echo "=== API エンドポイント ==="
echo "株価取得: GET $API_URL/price/{ticker}"
echo "詳細情報: GET $API_URL/info/{ticker}"  
echo "履歴データ: GET $API_URL/history/{ticker}?period=1mo"
echo ""
echo "=== 使用例 ==="
echo "curl \"${API_URL}price/AAPL\""
echo "curl \"${API_URL}info/MSFT\""
echo "curl \"${API_URL}history/GOOGL?period=1y\""
echo ""
echo "デプロイが完了しました！"