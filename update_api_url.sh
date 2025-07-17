#!/bin/bash

# 新API GatewayのURLを環境変数として設定するスクリプト - 新API対応版

# 現在の新API GatewayのURL
API_URL="https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod"

echo "🌐 新YFinance API Gateway URL: $API_URL"
echo ""

# 新APIの機能一覧表示
echo "📊 新APIの機能:"
echo "• 検索エンドポイント: $API_URL/search"
echo "  - 株式検索（価格情報付き）"
echo "  - 13地域対応（US, JP, DE, CA, AU, GB, FR, IT, ES, KR, IN, HK, SG）"
echo ""
echo "• 包括的情報エンドポイント: $API_URL/info"
echo "  - 17種類の金融データを統合取得"
echo "  - 基本情報、価格、ESG、財務諸表、株主情報、ISIN等"
echo ""
echo "• チャートエンドポイント: $API_URL/chart"
echo "  - 株価履歴データ"
echo "  - 複数期間対応（1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max）"
echo ""

# Lambda関数名設定
FUNCTION_NAME="YFinanceAPI"

echo "🔧 Lambda関数の環境変数を更新中..."

# 現在の環境変数を取得
echo "現在の設定を確認中..."
CURRENT_ENV=$(aws lambda get-function-configuration --function-name $FUNCTION_NAME --query 'Environment.Variables' --output json 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "✅ Lambda関数 '$FUNCTION_NAME' が見つかりました"
    
    # 新しい環境変数を設定
    NEW_ENV=$(echo $CURRENT_ENV | jq --arg url "$API_URL" '. + {"API_GATEWAY_URL": $url, "API_VERSION": "v2", "LAST_UPDATED": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}')
    
    # Lambda関数を更新
    echo "環境変数を更新中..."
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --environment Variables="$NEW_ENV" \
        --output table
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ 環境変数の更新が完了しました"
        echo "🌐 新しいAPI Gateway URL: $API_URL"
        echo "📅 更新日時: $(date)"
        echo ""
        echo "🧪 新APIのテスト方法:"
        echo "• 検索テスト: curl '$API_URL/search?q=Apple&region=US'"
        echo "• 情報テスト: curl '$API_URL/info?ticker=AAPL'"
        echo "• チャートテスト: curl '$API_URL/chart?ticker=AAPL&period=1mo'"
        echo ""
        echo "• 総合テストスクリプト: python test_search_with_price.py"
        echo "• CLIツール: python yfinance_cli.py AAPL -c"
        echo "• シェルスクリプト: ./yfinance.sh search Apple"
    else
        echo "❌ 環境変数の更新に失敗しました"
        exit 1
    fi
else
    echo "⚠️ Lambda関数 '$FUNCTION_NAME' が見つからないか、アクセス権限がありません"
    echo ""
    echo "💡 手動確認方法:"
    echo "1. AWS CLIが正しく設定されているか確認:"
    echo "   aws sts get-caller-identity"
    echo ""
    echo "2. Lambda関数一覧を確認:"
    echo "   aws lambda list-functions --query 'Functions[].FunctionName'"
    echo ""
    echo "3. 正しい関数名を指定して再実行:"
    echo "   FUNCTION_NAME='正しい関数名' ./update_api_url.sh"
    echo ""
    echo "🌐 それでも新APIは利用可能です:"
    echo "   $API_URL"
fi

echo ""
echo "📋 関連ファイルも更新済み:"
echo "• yfinance_cli.py - 包括的CLIツール"
echo "• yfinance_sample.py - 新API対応サンプル"
echo "• yfinance_search.py - 検索機能強化版"
echo "• test_api.py - 新API総合テスト"
echo "• test_search_with_price.py - 検索・価格情報テスト"
echo "• yfinance.sh - 新API対応シェルスクリプト" 