#!/bin/bash
# AWS SAM CLI を使ったLambda シミュレーターテスト
set -e

cleanup() {
  echo "[CLEANUP] Lambda シミュレーターを停止中..."
  docker-compose down || true
  exit 1
}
trap cleanup ERR

echo "[1] Lambda シミュレーターを起動"
if ! docker-compose up -d yfinance-lambda-sim; then
  echo "ERROR: シミュレーター起動に失敗しました"
  exit 1
fi

# シミュレーター起動待ち
echo "[2] Lambda シミュレーターの起動を待機中..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
  if curl -f -s http://localhost:3000/ >/dev/null 2>&1; then
    echo "Lambda シミュレーターが起動しました！"
    break
  fi
  
  echo "待機中... ($(($attempt + 1))/$max_attempts)"
  sleep 2
  attempt=$(($attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
  echo "ERROR: Lambda シミュレーターの起動がタイムアウトしました"
  docker-compose logs yfinance-lambda-sim
  exit 1
fi

echo "[3] Lambda API テスト開始"
testdir="./test/lambda_sim_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$testdir"

# テスト関数
test_lambda_endpoint() {
  local name="$1"
  local path="$2"
  local url="http://localhost:3000$path"
  
  echo "Testing Lambda: $name -> $url"
  
  if curl -f -s "$url" > "$testdir/${name}.json" 2>"$testdir/${name}.error"; then
    echo "  ✓ SUCCESS"
    rm -f "$testdir/${name}.error"
    return 0
  else
    echo "  ✗ FAILED"
    head -5 "$testdir/${name}.error" 2>/dev/null | sed 's/^/    /' || echo "    (No error details)"
    return 1
  fi
}

# Lambda エンドポイントテスト
total=0
passed=0
failed=0

endpoints="
search:/search?q=Apple&region=US:
tickerDetail:/tickerDetail?ticker=AAPL:
basic:/ticker/basic?ticker=AAPL:
price:/ticker/price?ticker=AAPL:
home:/home:
news_rss:/news/rss?limit=5:
rankings_stocks:/rankings/stocks?type=gainers&market=sp500&limit=5:
"

echo "$endpoints" | while IFS=':' read -r name path _; do
  if [ -n "$name" ] && [ -n "$path" ]; then
    total=$((total + 1))
    
    if test_lambda_endpoint "$name" "$path"; then
      passed=$((passed + 1))
    else
      failed=$((failed + 1))
    fi
  fi
done

echo ""
echo "[4] Lambda シミュレーター結果: $testdir"

echo ""
echo "[5] Lambda シミュレーターを停止"
docker-compose down

echo "Lambda シミュレーターテスト完了" 