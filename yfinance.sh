#!/bin/bash

# YFinanceのDockerコマンドと新APIを簡単に使用するためのシェルスクリプト - 新API対応版

# APIエンドポイント設定
API_BASE_URL="https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod"

# 使い方の表示
function show_usage {
  echo "使用方法: ./yfinance.sh [コマンド] [オプション]"
  echo ""
  echo "📈 新API機能（リモート実行）:"
  echo "  search KEYWORD    - 株式検索（価格情報付き）"
  echo "  info TICKER       - 包括的な株式情報（17種類のデータ）"
  echo "  chart TICKER      - チャートデータ"
  echo "  test-api          - 新APIの総合テスト"
  echo ""
  echo "🐳 Docker機能（ローカル実行）:"
  echo "  local-price TICKER      - 指定した銘柄の現在価格をローカルで表示"
  echo "  local-info TICKER       - 指定した銘柄の詳細情報をローカルで表示"
  echo "  local-history TICKER    - 指定した銘柄の株価履歴をローカルで表示"
  echo "  local-all TICKER        - 指定した銘柄の全情報をローカルで表示"
  echo "  local-search KEYWORD    - キーワードで銘柄をローカル検索"
  echo "  sample                  - サンプルプログラムを実行"
  echo "  build                   - Dockerイメージを再ビルド"
  echo "  shell                   - コンテナ内でシェルを実行"
  echo ""
  echo "🔧 その他:"
  echo "  help                    - このヘルプを表示"
  echo ""
  echo "オプション:"
  echo "  --period PERIOD   - 履歴・チャートの期間（1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max）"
  echo "  --region REGION   - 検索リージョン（US, CA, AU, DE, FR, GB, IT, ES, KR, JP, IN, HK, SG）"
  echo "  --limit NUMBER    - 検索結果の最大件数（ローカル検索のみ）"
  echo "  --json            - 結果をJSON形式で出力"
  echo "  --pretty          - JSONを整形して出力（--jsonと併用）"
  echo ""
  echo "📊 新API使用例:"
  echo "  ./yfinance.sh search Apple         - Apple株を検索（米国市場）"
  echo "  ./yfinance.sh search Toyota --region JP  - Toyota株を検索（日本市場）"
  echo "  ./yfinance.sh info AAPL           - Apple株の包括的情報（17種類のデータ）"
  echo "  ./yfinance.sh chart AAPL --period 1y  - Apple株の1年チャート"
  echo "  ./yfinance.sh info AAPL --json    - Apple株の情報をJSON形式で出力"
  echo ""
  echo "🐳 ローカル実行例:"
  echo "  ./yfinance.sh local-price AAPL         - アップルの現在価格をローカルで表示"
  echo "  ./yfinance.sh local-info 7203.T        - トヨタ自動車の詳細情報をローカルで表示"
  echo "  ./yfinance.sh local-search apple --region JP  - 「apple」でローカル検索（日本市場）"
}

# API呼び出し関数
function call_api {
  local endpoint="$1"
  local params="$2"
  local json_output="$3"
  local pretty_output="$4"
  
  local url="${API_BASE_URL}${endpoint}"
  
  echo "🌐 API呼び出し中: $url"
  if [ ! -z "$params" ]; then
    echo "📊 パラメータ: $params"
  fi
  echo ""
  
  if [ "$json_output" = "true" ]; then
    if [ "$pretty_output" = "true" ]; then
      curl -s "$url?$params" | jq '.'
    else
      curl -s "$url?$params"
    fi
  else
    # レスポンスを取得して整形表示
    local response=$(curl -s "$url?$params")
    echo "$response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'error' in data:
        print(f'❌ エラー: {data[\"error\"]}')
    elif 'query' in data:
        print(f'🔍 検索結果: \"{data[\"query\"]}\" ({data[\"region\"]})')
        print(f'件数: {data[\"count\"]}')
        for i, result in enumerate(data.get('results', [])[:5], 1):
            print(f'{i}. {result.get(\"symbol\", \"N/A\")} - {result.get(\"name\", \"N/A\")}')
            if result.get('current_price'):
                print(f'   価格: {result[\"current_price\"]} {result.get(\"currency\", \"USD\")}')
            if result.get('exchange'):
                print(f'   取引所: {result[\"exchange\"]}')
        if data['count'] > 5:
            print(f'... 他 {data[\"count\"] - 5} 件')
    elif 'ticker' in data:
        print(f'📊 {data[\"ticker\"]} の包括的情報')
        if data.get('info', {}).get('longName'):
            print(f'会社名: {data[\"info\"][\"longName\"]}')
        if data.get('price', {}).get('current_price'):
            print(f'現在価格: {data[\"price\"][\"current_price\"]} {data[\"price\"].get(\"currency\", \"USD\")}')
        data_count = len([k for k, v in data.items() if v and k != 'ticker'])
        print(f'取得データ種類: {data_count}')
    elif 'data' in data:
        print(f'📈 チャートデータ: {len(data[\"data\"])} ポイント')
        if data['data']:
            print(f'期間: {data[\"data\"][0][\"date\"]} 〜 {data[\"data\"][-1][\"date\"]}')
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))
except:
    print(sys.stdin.read())
"
  fi
}

# 引数のチェック
if [ $# -lt 1 ]; then
  show_usage
  exit 1
fi

# オプション解析
json_output=false
pretty_output=false
period=""
region="US"
limit=""

# パラメータを解析
command="$1"
shift

case "$command" in
  search|info|chart)
    if [ -z "$1" ]; then
      echo "❌ エラー: 検索キーワードまたはティッカーシンボルを指定してください"
      show_usage
      exit 1
    fi
    target="$1"
    shift
    ;;
  local-price|local-info|local-history|local-all|local-search)
    if [ -z "$1" ]; then
      echo "❌ エラー: ティッカーシンボルまたは検索キーワードを指定してください"
      show_usage
      exit 1
    fi
    target="$1"
    shift
    ;;
esac

# 残りの引数を処理
while [[ $# -gt 0 ]]; do
  case $1 in
    --json)
      json_output=true
      shift
      ;;
    --pretty)
      pretty_output=true
      shift
      ;;
    --period)
      period="$2"
      shift
      shift
      ;;
    --region)
      region="$2"
      shift
      shift
      ;;
    --limit)
      limit="$2"
      shift
      shift
      ;;
    *)
      echo "❌ 不明なオプション: $1"
      show_usage
      exit 1
      ;;
  esac
done

# コマンドの処理
case "$command" in
  search)
    echo "🔍 株式検索: $target (地域: $region)"
    params="q=$(echo "$target" | sed 's/ /%20/g')&region=$region"
    call_api "/search" "$params" "$json_output" "$pretty_output"
    ;;
    
  info)
    echo "📊 包括的情報取得: $target"
    params="ticker=$target"
    call_api "/info" "$params" "$json_output" "$pretty_output"
    ;;
    
  chart)
    echo "📈 チャートデータ取得: $target"
    if [ -z "$period" ]; then
      period="1mo"
    fi
    params="ticker=$target&period=$period"
    call_api "/chart" "$params" "$json_output" "$pretty_output"
    ;;
    
  test-api)
    echo "🧪 新API総合テスト実行中..."
    python3 test_search_with_price.py
    ;;
    
  local-price)
    echo "💰 現在価格取得（ローカル）: $target"
    docker run --rm yfinance-api python local_test.py price "$target"
    ;;
    
  local-info)
    echo "ℹ️ 詳細情報取得（ローカル）: $target"
    docker run --rm yfinance-api python local_test.py info "$target"
    ;;
    
  local-history)
    echo "📊 株価履歴取得（ローカル）: $target"
    if [ -z "$period" ]; then
      period="1mo"
    fi
    docker run --rm yfinance-api python local_test.py history "$target" "$period"
    ;;
    
  local-all)
    echo "📋 全情報取得（ローカル）: $target"
    extra_args=""
    if [ "$json_output" = "true" ]; then
      extra_args="$extra_args --json"
    fi
    if [ "$pretty_output" = "true" ]; then
      extra_args="$extra_args --pretty"
    fi
    docker run --rm yfinance-api python local_test.py all "$target" $extra_args
    ;;
    
  local-search)
    echo "🔍 銘柄検索（ローカル）: $target"
    extra_args="--region $region"
    if [ ! -z "$limit" ]; then
      extra_args="$extra_args --limit $limit"
    fi
    if [ "$json_output" = "true" ]; then
      extra_args="$extra_args --json"
    fi
    if [ "$pretty_output" = "true" ]; then
      extra_args="$extra_args --pretty"
    fi
    docker run --rm yfinance-api python yfinance_search.py "$target" $extra_args
    ;;
    
  sample)
    echo "🎯 サンプルプログラム実行中..."
    docker run --rm yfinance-api python yfinance_sample.py
    ;;
    
  build)
    echo "🔨 Dockerイメージを再ビルド中..."
    docker build -t yfinance-api .
    echo "✅ ビルド完了"
    ;;
    
  shell)
    echo "🐚 コンテナ内でシェルを実行..."
    docker run --rm -it yfinance-api /bin/bash
    ;;
    
  help)
    show_usage
    ;;
    
  *)
    echo "❌ 不明なコマンド: $command"
    show_usage
    exit 1
    ;;
esac
