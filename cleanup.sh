#!/bin/bash

# YFinance API クリーンアップスクリプト
# AWS リソースを削除

set -e

STACK_NAME="yfinance-api-stack"
REGION=${AWS_DEFAULT_REGION:-us-east-1}

echo "=== YFinance API クリーンアップ開始 ==="
echo "スタック名: $STACK_NAME"
echo "リージョン: $REGION"

# CloudFormation スタックの存在確認
if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION &> /dev/null; then
    echo "CloudFormation スタックを削除しています..."
    aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION
    
    echo "スタック削除の完了を待機しています..."
    aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME --region $REGION
    
    echo "CloudFormation スタックが削除されました"
else
    echo "CloudFormation スタック '$STACK_NAME' は存在しません"
fi

# S3バケットの削除（もしあれば）
echo "デプロイ用S3バケットを確認しています..."
BUCKETS=$(aws s3api list-buckets --query "Buckets[?contains(Name, 'yfinance-api-deploy')].Name" --output text --region $REGION)

if [ ! -z "$BUCKETS" ]; then
    for bucket in $BUCKETS; do
        echo "S3バケット $bucket を削除しています..."
        # バケット内のオブジェクトを削除
        aws s3 rm s3://$bucket --recursive --region $REGION
        # バケットを削除
        aws s3 rb s3://$bucket --region $REGION
        echo "S3バケット $bucket が削除されました"
    done
else
    echo "削除対象のS3バケットは見つかりませんでした"
fi

echo "=== クリーンアップ完了 ==="
echo "全ての AWS リソースが削除されました"