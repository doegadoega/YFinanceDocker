#!/bin/bash

# API GatewayのURLを環境変数として設定するスクリプト

# 現在のAPI GatewayのURLを取得
API_URL="https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod/"

echo "API Gateway URL: $API_URL"

# AWS Lambda関数の環境変数を更新
echo "Lambda関数の環境変数を更新中..."

# 関数名を指定（実際の関数名に合わせて変更してください）
FUNCTION_NAME="YFinanceAPI"

# 現在の環境変数を取得
CURRENT_ENV=$(aws lambda get-function-configuration --function-name $FUNCTION_NAME --query 'Environment.Variables' --output json)

# 新しい環境変数を設定
NEW_ENV=$(echo $CURRENT_ENV | jq --arg url "$API_URL" '. + {"API_GATEWAY_URL": $url}')

# Lambda関数を更新
aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --environment Variables="$NEW_ENV"

echo "環境変数の更新が完了しました。"
echo "新しいAPI Gateway URL: $API_URL" 