#!/bin/bash
# Webサーバーを使わず、APIロジックを直接テストするスクリプト
set -e

# エラーハンドリング関数
cleanup() {
  echo "[ERROR] スクリプトが異常終了しました"
  docker-compose down || true
  exit 1
}
trap cleanup ERR

# 1. Dockerイメージをビルド
echo "[1] Dockerイメージをビルド"
if ! docker-compose build yfinance-local; then
  echo "ERROR: ビルドに失敗しました"
  exit 1
fi

# 2. テストスクリプトをDockerコンテナ内で実行
echo "[2] APIロジック直接テストを実行"
if ! docker-compose run --rm --entrypoint="" yfinance-local python test_all_endpoints_direct.py; then
  echo "ERROR: テストスクリプトの実行に失敗しました"
  exit 1
fi

echo "[3] テスト完了。結果は ./test/ 以下に保存されています。"