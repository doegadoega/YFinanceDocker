# カスタムドメイン名の設定

## 概要
API GatewayのBaseURLが毎回変わる問題を解決するために、カスタムドメイン名を設定できます。

## 設定手順

### 1. ドメイン名の準備
- Route 53でドメインを取得、または既存のドメインを使用
- 例：`api.yourdomain.com`

### 2. SSL証明書の作成
```bash
# ACMで証明書をリクエスト
aws acm request-certificate \
    --domain-name api.yourdomain.com \
    --validation-method DNS \
    --region us-east-1
```

### 3. 証明書の検証
- ACMコンソールでDNS検証レコードをRoute 53に追加

### 4. API Gatewayでカスタムドメイン名を設定
```bash
# カスタムドメイン名を作成
aws apigateway create-domain-name \
    --domain-name api.yourdomain.com \
    --regional-certificate-arn arn:aws:acm:us-east-1:123456789012:certificate/xxxxx \
    --endpoint-configuration types=REGIONAL

# APIマッピングを作成
aws apigateway create-base-path-mapping \
    --domain-name api.yourdomain.com \
    --rest-api-id your-api-id \
    --stage prod
```

### 5. Route 53でAレコードを設定
- カスタムドメイン名のエイリアスレコードを作成
- ターゲット：API Gatewayのリージョナルエンドポイント

## メリット
- **安定したURL**: デプロイ後もURLが変わらない
- **ブランディング**: 独自のドメイン名を使用可能
- **SSL証明書**: 自動的にHTTPS対応

## 注意事項
- ドメイン名の取得・維持費用が発生
- 設定に時間がかかる
- 証明書の更新が必要 