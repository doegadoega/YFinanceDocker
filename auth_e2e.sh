#!/usr/bin/env bash
set -euo pipefail

# 一連の認証フローを自動実行するスクリプト
# 1) 登録 → 2) ログイン(JWT取得) → 3) /user/me 取得 → 4) /user/me 更新
# 事前条件: AWS CLI, jq がインストール済み。AWS 認証済み。スタック名: yfinance-api-stack

REGION=${REGION:-ap-northeast-1}
STACK=${STACK:-yfinance-api-stack}

EMAIL=${EMAIL:-your@example.com}
PASSWORD=${PASSWORD:-Passw0rd!}
NAME=${NAME:-Your Name}

# API URL は環境変数 API があればそれを優先、なければスタック出力から取得
if [[ -z "${API:-}" ]]; then
  echo "[INFO] Fetching API URL from CloudFormation outputs..."
  API=$(aws cloudformation describe-stacks \
    --stack-name "$STACK" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='YFinanceApiUrl'].OutputValue" \
    --output text)
fi

if [[ -z "$API" || "$API" == "None" ]]; then
  echo "[ERROR] API URL を取得できませんでした。環境変数 API を指定してください。" >&2
  exit 1
fi

echo "[INFO] API=$API"

have_jq=1
if ! command -v jq >/dev/null 2>&1; then
  have_jq=0
  echo "[WARN] jq が見つかりません。整形せずに表示します。"
fi

function pp() {
  if [[ $have_jq -eq 1 ]]; then jq; else cat; fi
}

echo "\n== 1) Register =="
register_payload=$(cat <<JSON
{"email":"$EMAIL","password":"$PASSWORD","name":"$NAME"}
JSON
)
curl -sS -X POST "${API%/}/auth/register" \
  -H "Content-Type: application/json" \
  -d "$register_payload" | pp

echo "\n== 2) Login (get JWT) =="
TOKEN=$(curl -sS -X POST "${API%/}/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" | (jq -r .token 2>/dev/null || cat))

if [[ -z "$TOKEN" || "$TOKEN" == "null" ]]; then
  echo "[ERROR] トークン取得に失敗しました" >&2
  exit 2
fi
echo "TOKEN=${TOKEN:0:40}..."

echo "\n== 3) GET /user/me =="
curl -sS -H "Authorization: Bearer $TOKEN" \
  "${API%/}/user/me" | pp

echo "\n== 4) PUT /user/me (update profile) =="
ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
update_payload=$(cat <<JSON
{"name":"$NAME","profile":{"lang":"ja","checkedAt":"$ts"}}
JSON
)
curl -sS -X PUT "${API%/}/user/me" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "$update_payload" | pp

echo "\n[OK] 認証フローの確認が完了しました。"


