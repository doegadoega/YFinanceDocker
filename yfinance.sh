#!/bin/bash

# YFinanceのDockerコマンドを簡単に実行するためのシェルスクリプト

# 使い方の表示
function show_usage {
  echo "使用方法: ./yfinance.sh [コマンド] [オプション]"
  echo ""
  echo "コマンド:"
  echo "  price TICKER      - 指定した銘柄の現在価格を表示"
  echo "  info TICKER       - 指定した銘柄の詳細情報を表示"
  echo "  history TICKER    - 指定した銘柄の株価履歴を表示（デフォルト：1ヶ月）"
  echo "  all TICKER        - 指定した銘柄の全情報を表示"
  echo "  search KEYWORD    - キーワードで銘柄を検索"
  echo "  sample            - サンプルプログラムを実行"
  echo "  build             - Dockerイメージを再ビルド"
  echo "  shell             - コンテナ内でシェルを実行"
  echo "  help              - このヘルプを表示"
  echo ""
  echo "オプション:"
  echo "  --period PERIOD   - 履歴の期間を指定（1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max）"
  echo "  --region REGION   - 検索リージョン（US, JP）"
  echo "  --limit NUMBER    - 検索結果の最大件数"
  echo "  --json            - 結果をJSON形式で出力"
  echo "  --pretty          - JSONを整形して出力（--jsonと併用）"
  echo ""
  echo "例:"
  echo "  ./yfinance.sh price AAPL         - アップルの現在価格を表示"
  echo "  ./yfinance.sh info 7203.T        - トヨタ自動車の詳細情報を表示"
  echo "  ./yfinance.sh history AAPL --period 1y  - アップルの1年分の株価履歴を表示"
  echo "  ./yfinance.sh all MSFT           - マイクロソフトの全情報を表示"
  echo "  ./yfinance.sh search apple       - 「apple」で銘柄を検索（米国市場）"
  echo "  ./yfinance.sh search トヨタ --region JP  - 「トヨタ」で銘柄を検索（日本市場）"
  echo "  ./yfinance.sh all AAPL --json    - アップルの情報をJSON形式で出力"
  echo "  ./yfinance.sh search apple --json --pretty  - 検索結果を整形されたJSONで出力"
}

# 引数のチェック
if [ $# -lt 1 ]; then
  show_usage
  exit 1
fi

# コマンドの処理
case "$1" in
  price)
    if [ -z "$2" ]; then
      echo "エラー: ティッカーシンボルを指定してください"
      show_usage
      exit 1
    fi
    
    # JSONオプションの確認
    if [[ "$*" == *"--json"* ]]; then
      docker run --rm yfinance yfinance_cli.py "$2" --price --json
    else
      docker run --rm yfinance yfinance_cli.py "$2" --price
    fi
    ;;
    
  info)
    if [ -z "$2" ]; then
      echo "エラー: ティッカーシンボルを指定してください"
      show_usage
      exit 1
    fi
    
    # JSONオプションの確認
    if [[ "$*" == *"--json"* ]]; then
      docker run --rm yfinance yfinance_cli.py "$2" --info --json
    else
      docker run --rm yfinance yfinance_cli.py "$2" --info
    fi
    ;;
    
  history)
    if [ -z "$2" ]; then
      echo "エラー: ティッカーシンボルを指定してください"
      show_usage
      exit 1
    fi
    
    # 期間オプションとJSONオプションの処理
    period="1mo"
    json_flag=""
    
    if [[ "$*" == *"--period"* ]]; then
      for ((i=3; i<=$#; i++)); do
        if [ "${!i}" == "--period" ] && [ $((i+1)) -le $# ]; then
          period="${!((i+1))}"
          break
        fi
      done
    fi
    
    if [[ "$*" == *"--json"* ]]; then
      json_flag="--json"
    fi
    
    docker run --rm yfinance yfinance_cli.py "$2" --history --period "$period" $json_flag
    ;;
    
  all)
    if [ -z "$2" ]; then
      echo "エラー: ティッカーシンボルを指定してください"
      show_usage
      exit 1
    fi
    
    # JSONオプションの確認
    if [[ "$*" == *"--json"* ]]; then
      docker run --rm yfinance yfinance_cli.py "$2" --price --info --history --json
    else
      docker run --rm yfinance yfinance_cli.py "$2" --price --info --history
    fi
    ;;
    
  search)
    if [ -z "$2" ]; then
      echo "エラー: 検索キーワードを指定してください"
      show_usage
      exit 1
    fi
    
    # オプションの処理
    region="US"
    limit=10
    json_flag=""
    pretty_flag=""
    
    for ((i=3; i<=$#; i++)); do
      case "${!i}" in
        --region)
          if [ $((i+1)) -le $# ]; then
            i=$((i+1))
            region="${!i}"
          fi
          ;;
        --limit)
          if [ $((i+1)) -le $# ]; then
            i=$((i+1))
            limit="${!i}"
          fi
          ;;
        --json)
          json_flag="--json"
          ;;
        --pretty)
          pretty_flag="--pretty"
          ;;
      esac
    done
    
    docker run --rm yfinance yfinance_search.py "$2" --region "$region" --limit "$limit" $json_flag $pretty_flag
    ;;
    
  sample)
    docker run --rm yfinance yfinance_sample.py
    ;;
    
  build)
    docker build -t yfinance .
    ;;
    
  shell)
    docker run --rm -it yfinance /bin/bash
    ;;
    
  help|*)
    show_usage
    ;;
esac 