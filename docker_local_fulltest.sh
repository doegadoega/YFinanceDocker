#!/bin/bash
# Webサーバーを使わず、APIロジックを直接テストするスクリプト（拡張版）
set -e

# エラーハンドリング関数
cleanup() {
  echo "[ERROR] スクリプトが異常終了しました"
  docker-compose down || true
  exit 1
}
trap cleanup ERR

echo "🚀 YFinance Docker 完全テストスクリプト（拡張版）"
echo "================================================="
echo "📅 実行日時: $(date)"
echo "🐳 Docker環境での包括的テスト開始"
echo "================================================="
echo

# 1. Dockerイメージをビルド
echo "[1/4] 🔨 Dockerイメージをビルド"
if ! docker-compose build yfinance-local; then
  echo "❌ ERROR: ビルドに失敗しました"
  exit 1
fi
echo "✅ ビルド完了"
echo

# 2. テストスクリプトをDockerコンテナ内で実行
echo "[2/4] 🧪 APIロジック直接テスト実行（拡張版）"
if ! docker-compose run --rm --entrypoint="" yfinance-local python test_all_endpoints_direct.py; then
  echo "❌ ERROR: テストスクリプトの実行に失敗しました"
  exit 1
fi
echo "✅ 直接テスト完了"
echo

# 3. 拡張されたHomeエンドポイントの個別テスト
echo "[3/4] 🏠 拡張Homeエンドポイント個別テスト"
echo "--- 拡張機能の各セクションを個別にテスト ---"

# Homeエンドポイントの基本テスト
echo "🏠 基本Homeエンドポイント:"
if docker-compose run --rm --entrypoint="" yfinance-local python yfinance_cli.py home > /dev/null 2>&1; then
  echo "  ✅ Home基本機能: OK"
else
  echo "  ❌ Home基本機能: FAILED"
fi

# 個別機能のテスト
echo "📰 ニュースRSS統合:"
if docker-compose run --rm --entrypoint="" yfinance-local python yfinance_cli.py news_rss --limit 3 > /dev/null 2>&1; then
  echo "  ✅ News RSS: OK"
else
  echo "  ❌ News RSS: FAILED"
fi

echo "📈 株価ランキング統合:"
if docker-compose run --rm --entrypoint="" yfinance-local python yfinance_cli.py rankings_stocks --type gainers --limit 3 > /dev/null 2>&1; then
  echo "  ✅ Stock Rankings: OK"
else
  echo "  ❌ Stock Rankings: FAILED"
fi

echo "🏢 セクターランキング統合:"
if docker-compose run --rm --entrypoint="" yfinance-local python yfinance_cli.py rankings_sectors --limit 3 > /dev/null 2>&1; then
  echo "  ✅ Sector Rankings: OK"
else
  echo "  ❌ Sector Rankings: FAILED"
fi

echo "📊 主要指数統合:"
if docker-compose run --rm --entrypoint="" yfinance-local python yfinance_cli.py markets_indices > /dev/null 2>&1; then
  echo "  ✅ Major Indices: OK"
else
  echo "  ❌ Major Indices: FAILED"
fi

echo "💱 為替レート統合:"
if docker-compose run --rm --entrypoint="" yfinance-local python yfinance_cli.py markets_currencies > /dev/null 2>&1; then
  echo "  ✅ Currency Rates: OK"
else
  echo "  ❌ Currency Rates: FAILED"
fi

echo "🛢️ 商品価格統合:"
if docker-compose run --rm --entrypoint="" yfinance-local python yfinance_cli.py markets_commodities > /dev/null 2>&1; then
  echo "  ✅ Commodity Prices: OK"
else
  echo "  ❌ Commodity Prices: FAILED"
fi

echo "🌍 市場状況統合:"
if docker-compose run --rm --entrypoint="" yfinance-local python yfinance_cli.py markets_status > /dev/null 2>&1; then
  echo "  ✅ Market Status: OK"
else
  echo "  ❌ Market Status: FAILED"
fi

echo "✅ 個別機能テスト完了"
echo

# 4. 結果の確認と表示
echo "[4/4] 📋 テスト結果確認"
TEST_DIR=$(ls -t ./test/ | head -n 1 2>/dev/null || echo "")

if [ -n "$TEST_DIR" ] && [ -d "./test/$TEST_DIR" ]; then
  echo "📁 結果保存ディレクトリ: ./test/$TEST_DIR"
  
  # ファイル数を確認
  FILE_COUNT=$(ls -1 ./test/$TEST_DIR/*.json 2>/dev/null | wc -l || echo 0)
  echo "📄 生成されたテストファイル数: $FILE_COUNT"
  
  # 拡張機能の詳細テスト結果確認
  if [ -f "./test/$TEST_DIR/enhanced_home_detailed.json" ]; then
    echo "🎉 拡張機能詳細テスト結果が生成されました"
    
    # JSONファイルの存在確認（主要ファイル）
    echo "🔍 主要テストファイル確認:"
    for file in "home.json" "enhanced_home_detailed.json" "news_rss.json" "rankings_stocks.json" "rankings_sectors.json" "markets_indices.json" "markets_currencies.json" "markets_commodities.json" "markets_status.json"; do
      if [ -f "./test/$TEST_DIR/$file" ]; then
        echo "  ✅ $file"
      else
        echo "  ❌ $file (missing)"
      fi
    done
  else
    echo "⚠️  拡張機能詳細テスト結果が見つかりません"
  fi
  
  echo
  echo "📖 テスト結果の詳細は以下で確認できます:"
  echo "   cat ./test/$TEST_DIR/enhanced_home_detailed.json | jq '.enhanced_features_analysis'"
  echo
else
  echo "⚠️  テスト結果ディレクトリが見つかりません"
fi

echo "================================================="
echo "🎊 拡張版テスト完了！"
echo "================================================="
echo "🏠 /home エンドポイントに以下の機能が統合されました:"
echo "  📰 news/rss - 最新金融ニュース"
echo "  📈 rankings/stocks - 株価ランキング（上昇・下落）"
echo "  🏢 rankings/sectors - セクターランキング"
echo "  📊 markets/indices - 主要指数詳細"
echo "  💱 markets/currencies - 為替レート"
echo "  🛢️ markets/commodities - 商品価格"
echo "  🌍 markets/status - 市場開閉状況"
echo "================================================="
echo "✨ 包括的なマーケット情報を一つのエンドポイントで取得可能！"
echo "================================================="