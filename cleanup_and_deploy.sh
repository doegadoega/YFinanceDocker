#!/bin/bash

# YFinance API クリーンアップ・再デプロイスクリプト
# 既存のスタックを削除してから新しくデプロイ

set -e

echo "=== YFinance API クリーンアップ・再デプロイ開始 ==="

# AWS CLI と SAM CLI がインストールされているかチェック
if ! command -v aws &> /dev/null; then
    echo "エラー: AWS CLI がインストールされていません"
    exit 1
fi

if ! command -v sam &> /dev/null; then
    echo "エラー: AWS SAM CLI がインストールされていません"
    exit 1
fi

# AWS 認証情報の確認
echo "AWS 認証情報を確認しています..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "エラー: AWS認証情報が設定されていません"
    exit 1
fi

CURRENT_USER=$(aws sts get-caller-identity --query "Arn" --output text)
echo "デプロイユーザー: $CURRENT_USER"

STACK_NAME="yfinance-api-stack"
REGION=${AWS_DEFAULT_REGION:-ap-northeast-1}

echo "CloudFormationスタック: $STACK_NAME"
echo "リージョン: $REGION"

# 既存のスタックが存在するかチェック
echo "既存のスタックを確認しています..."
if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION &> /dev/null; then
    echo "⚠️  既存のスタックが見つかりました。削除します..."
    
    # スタック削除の確認
    read -p "本当にスタックを削除しますか？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "スタックを削除しています..."
        aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION
        
        echo "スタック削除の完了を待機しています..."
        aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME --region $REGION
        
        echo "✅ スタックの削除が完了しました。"
    else
        echo "❌ スタックの削除をキャンセルしました。"
        exit 1
    fi
else
    echo "既存のスタックは見つかりませんでした。新規デプロイを実行します。"
fi

# 新しいデプロイを実行
echo ""
echo "=== 新規デプロイを実行 ==="
./deploy.sh

echo ""
echo "=== クリーンアップ・再デプロイ完了 ===" 