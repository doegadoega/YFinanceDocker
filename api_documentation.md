# YFinance API ドキュメント

株式データを取得するためのREST APIです。AWS Lambda + API Gatewayで構築されています。

## ベースURL

```
https://{api-id}.execute-api.{region}.amazonaws.com/prod/
```

## 認証

このAPIは現在認証なしでアクセス可能です。

## エンドポイント

### 1. 株価取得 API

現在の株価を取得します。

**エンドポイント:** `GET /price/{ticker}`

**パラメータ:**
- `ticker` (required): ティッカーシンボル（例: AAPL, MSFT, 7203.T）

**レスポンス例:**
```json
{
  "ticker": "AAPL",
  "current_price": 150.75,
  "currency": "USD",
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

**cURLサンプル:**
```bash
curl "https://your-api-gateway-url/prod/price/AAPL"
```

### 2. 詳細情報取得 API

株式の詳細情報を取得します。

**エンドポイント:** `GET /info/{ticker}`

**パラメータ:**
- `ticker` (required): ティッカーシンボル

**レスポンス例:**
```json
{
  "ticker": "AAPL",
  "name": "Apple Inc.",
  "current_price": 150.75,
  "previous_close": 149.50,
  "market_cap": 2500000000000,
  "dividend_yield": 0.0045,
  "trailing_pe": 28.5,
  "fifty_two_week_high": 182.94,
  "fifty_two_week_low": 124.17,
  "currency": "USD",
  "exchange": "NASDAQ",
  "sector": "Technology",
  "industry": "Consumer Electronics",
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

**cURLサンプル:**
```bash
curl "https://your-api-gateway-url/prod/info/AAPL"
```

### 3. 株価履歴取得 API

指定期間の株価履歴を取得します。

**エンドポイント:** `GET /history/{ticker}`

**パラメータ:**
- `ticker` (required): ティッカーシンボル
- `period` (optional): 取得期間（デフォルト: 1mo）

**利用可能な期間:**
- `1d`: 1日
- `5d`: 5日
- `1mo`: 1ヶ月
- `3mo`: 3ヶ月
- `6mo`: 6ヶ月
- `1y`: 1年
- `2y`: 2年
- `5y`: 5年
- `10y`: 10年
- `ytd`: 年初来
- `max`: 最大期間

**レスポンス例:**
```json
{
  "ticker": "AAPL",
  "period": "1mo",
  "data": [
    {
      "date": "2024-01-01",
      "open": 147.50,
      "high": 150.75,
      "low": 146.25,
      "close": 149.93,
      "volume": 75234567
    }
  ],
  "count": 21,
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

**cURLサンプル:**
```bash
# 1ヶ月分の履歴
curl "https://your-api-gateway-url/prod/history/AAPL"

# 1年分の履歴
curl "https://your-api-gateway-url/prod/history/AAPL?period=1y"
```

## エラーレスポンス

APIでエラーが発生した場合、以下の形式でエラー情報が返されます：

```json
{
  "error": "エラーメッセージ",
  "details": "詳細なエラー情報（オプション）"
}
```

**HTTPステータスコード:**
- `200`: 成功
- `400`: リクエストパラメータエラー
- `404`: リソースが見つからない
- `500`: サーバーエラー

## CORS サポート

このAPIはCORS（Cross-Origin Resource Sharing）をサポートしており、ブラウザからの直接アクセスが可能です。

## レート制限

現在、レート制限は設定されていませんが、過度なリクエストは避けてください。

## 使用例

### JavaScript (ブラウザ)

```javascript
// 株価取得
async function getStockPrice(ticker) {
  const response = await fetch(`https://your-api-gateway-url/prod/price/${ticker}`);
  const data = await response.json();
  return data;
}

// 詳細情報取得
async function getStockInfo(ticker) {
  const response = await fetch(`https://your-api-gateway-url/prod/info/${ticker}`);
  const data = await response.json();
  return data;
}

// 履歴データ取得
async function getStockHistory(ticker, period = '1mo') {
  const response = await fetch(`https://your-api-gateway-url/prod/history/${ticker}?period=${period}`);
  const data = await response.json();
  return data;
}
```

### Python

```python
import requests

base_url = "https://your-api-gateway-url/prod"

# 株価取得
def get_stock_price(ticker):
    response = requests.get(f"{base_url}/price/{ticker}")
    return response.json()

# 詳細情報取得
def get_stock_info(ticker):
    response = requests.get(f"{base_url}/info/{ticker}")
    return response.json()

# 履歴データ取得
def get_stock_history(ticker, period="1mo"):
    response = requests.get(f"{base_url}/history/{ticker}", params={"period": period})
    return response.json()
```

## サポートされている市場

- アメリカ株式市場（NASDAQ, NYSE など）: AAPL, MSFT, GOOGL
- 日本株式市場: 7203.T (トヨタ), 9984.T (ソフトバンク)
- その他の主要な世界市場

## 注意事項

1. データは Yahoo Finance から取得されており、リアルタイムデータではない場合があります
2. 市場休業日や取引時間外はデータが更新されません
3. 無効なティッカーシンボルを指定した場合はエラーが返されます
4. サービスの可用性はYahoo Financeの状況に依存します