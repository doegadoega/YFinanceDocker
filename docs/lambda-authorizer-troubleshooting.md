### API Gateway Lambda Authorizer 認証トラブルシューティング

このドキュメントは、API Gateway + Lambda Authorizer で JWT 認証が通らない場合の原因と確認・対処手順をまとめたものです。参考: [API Gateway Lambda オーソライザーを使用する](https://docs.aws.amazon.com/ja_jp/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html)

---

#### クイックチェック（最短ルート）
- 両Lambdaの `JWT_SECRET` が一致しているか
- Authorizer のタイプが `TOKEN` で、IDソースが `Authorization` になっているか（キャッシュはデバッグ中は 0 秒）
- `Authorization: Bearer <JWT>` ヘッダーが API Gateway まで届いているか
- Authorizer の CloudWatch Logs に呼び出しログが出ているか（出ていない=設定/ヘッダー経路不備）
- JWT の `sub` もしくは `email` がプリンシパルとして解決できているか

---

#### 1. ヘッダーが届いているか確認
```bash
API="https://<api-id>.execute-api.ap-northeast-1.amazonaws.com/prod"
curl -i -H "Authorization: Bearer <JWT>" "$API/user/me"
```
- CloudFront/ALB/カスタムドメイン経由の場合、`Authorization` ヘッダー転送設定を有効化。
- CORS のプリフライト（OPTIONS）は Authorizer を外す（OPTIONS で 403 になりがち）。

---

#### 2. Authorizer 設定（TOKEN 型/キャッシュ無効）
SAM 例（本プロジェクトの `template.yaml` より抜粋）
```yaml
YFinanceApi:
  Type: AWS::Serverless::Api
  Properties:
    Auth:
      Authorizers:
        UserJwtAuthorizer:
          FunctionArn: !GetAtt AuthAuthorizer.Arn
          FunctionPayloadType: TOKEN
          AuthorizerResultTtlInSeconds: 0
          Identity:
            Header: Authorization
            ReauthorizeEvery: 0
```
- TOKEN 型では `Identity.Header: Authorization` を推奨。
- デバッグ時は `AuthorizerResultTtlInSeconds: 0` でキャッシュ無効化。

---

#### 3. JWT_SECRET と環境変数の同期
両Lambdaの環境変数を確認：
```bash
REGION=ap-northeast-1
STACK=yfinance-api-stack
FN_APP=$(aws cloudformation describe-stacks --stack-name $STACK --region $REGION --query "Stacks[0].Outputs[?OutputKey=='YFinanceFunctionName'].OutputValue" --output text)
FN_AUTH=$(aws cloudformation describe-stacks --stack-name $STACK --region $REGION --query "Stacks[0].Outputs[?OutputKey=='AuthAuthorizerFunctionName'].OutputValue" --output text)

aws lambda get-function-configuration --function-name "$FN_APP" --region $REGION --query 'Environment.Variables'
aws lambda get-function-configuration --function-name "$FN_AUTH" --region $REGION --query 'Environment.Variables'
```
必要なら同期：
```bash
API=$(aws cloudformation describe-stacks --stack-name $STACK --region $REGION --query "Stacks[0].Outputs[?OutputKey=='YFinanceApiUrl'].OutputValue" --output text)
NEW_SECRET="dev-secret-$(date +%s)"
aws lambda update-function-configuration --function-name "$FN_APP"  --region $REGION --environment "Variables={PYTHONPATH=/opt/python,API_GATEWAY_URL=$API,JWT_SECRET=$NEW_SECRET,USERS_TABLE=$STACK-Users}"
aws lambda update-function-configuration --function-name "$FN_AUTH" --region $REGION --environment "Variables={JWT_SECRET=$NEW_SECRET}"
```

---

#### 4. Authorizer ログで実行確認
```bash
FN_AUTH=$(aws cloudformation describe-stacks --stack-name $STACK --region $REGION --query "Stacks[0].Outputs[?OutputKey=='AuthAuthorizerFunctionName'].OutputValue" --output text)
aws logs tail "/aws/lambda/$FN_AUTH" --region $REGION --since 5m
```
- ログが出ない → API Gateway 設定/ヘッダー経路の問題
- ログに `no_token`/`signature mismatch`/`token expired` 等が出ていればメッセージに沿って対処

---

#### 5. JWT クレーム整合性（sub / email）
- 本実装は `sub` または `email` のどちらでもプリンシパルとして許可し、`context.email` に渡します。
- 運用上は「`sub` にメールアドレスを入れる」か「`email` を併記」すれば OK。
- 将来 `sub` を不変IDにする場合は、DynamoDB のキーも `userId` に変更する設計へ（メール変更に強い）。

---

#### 6. IAM ポリシーの Resource
- 返却するポリシーの `Resource` は、最低限 `event.methodArn` をカバーする必要があります。
- ステージ全体を許可したい場合の例：
  `arn:aws:execute-api:<region>:<account>:<apiId>/<stage>/*/*`

---

#### 7. 典型的な原因と対策早見表
- 【ヘッダー欠落】CF/ALB/カスタムドメインで `Authorization` 未転送 → 転送設定を有効化
- 【Authorizer 型不正】REQUEST のまま/TOKEN想定とズレ → `FunctionPayloadType: TOKEN` に揃える
- 【キャッシュ】古いDenyが再利用 → `AuthorizerResultTtlInSeconds: 0` で無効化
- 【Bearer 抽出】前後空白・大文字小文字・`authorizationToken` ケース未対応 → どちらも見て安全に抽出
- 【秘密鍵不一致】`JWT_SECRET` が本体とAuthorizerで異なる → 同期
- 【クレーム差異】`sub`のみだが`email`のみ参照 → どちらでも許可する実装に
- 【CORS/OPTIONS】OPTIONS に Authorizer が掛かって 403 → OPTIONS は Authorizer 無し
- 【時刻ズレ】`exp` が既に過去 → サーバ時刻確認

---

#### 8. 検証用 cURL（macOS/Linux）
```bash
API=https://<api-id>.execute-api.ap-northeast-1.amazonaws.com/prod

# 登録
curl -sS -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"your@example.com","password":"Passw0rd!","name":"Your Name"}' | jq

# ログイン → TOKEN
TOKEN=$(curl -sS -X POST "$API/auth/login" -H 'Content-Type: application/json' -d '{"email":"your@example.com","password":"Passw0rd!"}' | jq -r .token)
echo "TOKEN=${TOKEN:0:24}..."

# 認証付き取得
curl -sS -H "Authorization: Bearer $TOKEN" "$API/user/me" | jq
```

---

#### 9. 付録：DynamoDB の確認
- テーブル名: `yfinance-api-stack-Users`（リージョン: ap-northeast-1）
```bash
# 単一ユーザー
aws dynamodb get-item \
  --table-name yfinance-api-stack-Users \
  --region ap-northeast-1 \
  --key '{"email":{"S":"your@example.com"}}' | jq

# ざっくり確認
aws dynamodb execute-statement \
  --region ap-northeast-1 \
  --statement 'SELECT * FROM "yfinance-api-stack-Users" LIMIT 25' | jq
```

---

#### 10. 一括検証
- プロジェクト同梱の `auth_e2e.sh` で 登録→ログイン→取得→更新 を自動実行できます。
```bash
./auth_e2e.sh
EMAIL=you@example.com PASSWORD='Passw0rd!' NAME='You' ./auth_e2e.sh
```


