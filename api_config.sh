#!/bin/bash

# API設定管理スクリプト

# 現在のAPI URLを取得
get_current_api_url() {
    STACK_NAME="yfinance-api-stack"
    REGION=${AWS_DEFAULT_REGION:-ap-northeast-1}
    
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query "Stacks[0].Outputs[?OutputKey=='YFinanceApiUrl'].OutputValue" \
        --output text 2>/dev/null)
    
    if [ "$API_URL" != "None" ] && [ -n "$API_URL" ]; then
        echo $API_URL
    else
        echo "API URL not found"
    fi
}

# API URLを設定ファイルに保存
save_api_url() {
    API_URL=$(get_current_api_url)
    if [ "$API_URL" != "API URL not found" ]; then
        echo "API_URL=$API_URL" > .api_config
        echo "API URL saved: $API_URL"
    else
        echo "Failed to get API URL"
    fi
}

# 保存されたAPI URLを読み込み
load_api_url() {
    if [ -f .api_config ]; then
        source .api_config
        echo $API_URL
    else
        echo "No saved API URL found"
    fi
}

# 全エンドポイントのテスト用URLを表示
show_all_endpoints() {
    API_URL=$(load_api_url)
    if [ "$API_URL" = "No saved API URL found" ]; then
        API_URL=$(get_current_api_url)
    fi
    
    if [ "$API_URL" != "API URL not found" ]; then
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
        echo "=== テスト実行例（JSON整形付き）==="
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
    else
        echo "API URL not found. Please deploy first."
    fi
}

# 使用方法
case "$1" in
    "save")
        save_api_url
        ;;
    "load")
        load_api_url
        ;;
    "current")
        get_current_api_url
        ;;
    "endpoints")
        show_all_endpoints
        ;;
    *)
        echo "Usage: $0 {save|load|current|endpoints}"
        echo "  save      - 現在のAPI URLを保存"
        echo "  load      - 保存されたAPI URLを表示"
        echo "  current   - 現在のAPI URLを取得"
        echo "  endpoints - 全エンドポイントのテスト用URLを表示"
        ;;
esac 