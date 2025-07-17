# YFinance API - 包括的な金融データ取得プラットフォーム

YFinanceライブラリを活用した、AWS Lambda + API Gateway による高性能な金融データ取得APIです。

## 🌟 主な機能

### ✅ 包括的なデータ取得
- **17種類の金融データ**: 株価、企業情報、財務諸表、ESG、アナリスト分析など
- **最新のYFinance API**: 全ての新しいメソッドを統合
- **リアルタイム株価**: 現在価格と価格変動
- **チャート生成**: 株価チャートの画像生成

### ✅ 高度な検索機能
- **多地域対応**: 米国株・日本株
- **リアルタイム価格**: 検索結果に現在価格を含む
- **詳細フィルタ**: 銘柄タイプ、取引所別検索

### ✅ 開発者フレンドリー
- **Swagger UI**: 自動生成されたAPI仕様書
- **CORS対応**: ブラウザからの直接アクセス可能
- **JSON レスポンス**: 標準化されたデータ形式

## 🚀 クイックスタート

### 本番API（デプロイ済み）

**ベースURL**: `https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod/`

**Swagger UI**: [https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod/](https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod/)

### 基本的な使用例

```bash
# 銘柄検索
curl "https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod/search?q=apple&limit=5"

# 包括的な企業情報取得（全17種類のデータ）
curl "https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod/info?ticker=AAPL&period=1y"

# 日本株の情報取得
curl "https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod/info?ticker=7203.T"

# チャート画像生成
curl "https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod/chart?ticker=TSLA&period=1mo&type=candle" --output tsla_chart.png
```

## 📊 APIエンドポイント

### 1. 銘柄検索 (`/search`)

**URL**: `GET /search?q={keyword}&limit={count}&region={region}`

**説明**: キーワードによる銘柄検索を実行し、リアルタイム価格を取得

**パラメータ**:
- `q` (必須): 検索キーワード（例: apple, microsoft, トヨタ）
- `limit` (オプション): 検索結果件数（デフォルト: 10、最大: 10）
- `region` (オプション): 検索リージョン（US, JP、デフォルト: US）

**レスポンス例**:
```json
{
  "query": "tesla",
  "region": "US",
  "count": 3,
  "results": [
    {
      "symbol": "TSLA",
      "name": "Tesla, Inc.",
      "exchange": "NMS",
      "type": "Equity",
      "score": 28512.0,
      "current_price": 321.76,
      "previous_close": 319.22,
      "price_change": 2.54,
      "price_change_percent": 0.80,
      "price_change_direction": "up",
      "currency": "USD",
      "market_cap": 1026485534720,
      "volume": 22156800,
      "timestamp": "2025-07-18T00:39:20.517464Z"
    }
  ]
}
```

### 2. 包括的企業情報 (`/info`)

**URL**: `GET /info?ticker={symbol}&period={period}`

**説明**: 指定銘柄の全17種類の金融データを統合して取得

**パラメータ**:
- `ticker` (必須): ティッカーシンボル（例: AAPL, MSFT, 7203.T）
- `period` (オプション): 履歴期間（デフォルト: 1mo）

**取得可能なデータ（17種類）**:
1. **基本情報**: 企業概要、ロゴURL
2. **高速情報**: リアルタイム基本データ
3. **価格情報**: 現在価格、前日比、変化率
4. **株価履歴**: 指定期間のOHLCVデータ
5. **ニュース**: 関連ニュース記事
6. **配当情報**: 配当履歴と配当利回り
7. **オプション**: コール・プットオプション情報
8. **財務諸表**: 損益計算書、貸借対照表、キャッシュフロー
9. **アナリスト予想**: 推奨情報、目標株価
10. **🆕 ISIN**: 国際証券識別番号
11. **🆕 推奨履歴**: アナリスト推奨変更履歴
12. **🆕 カレンダー**: 決算日などのイベント
13. **🆕 決算日**: 過去・未来の決算日詳細
14. **🆕 ESG情報**: 環境・社会・ガバナンス評価
15. **🆕 株主情報**: 大株主、機関投資家、投資信託
16. **🆕 株式数詳細**: 発行済み株式数の詳細
17. **🆕 格付け変更**: アップグレード・ダウングレード履歴

**期間オプション**:
- `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `ytd`, `max`

**レスポンス例（一部抜粋）**:
```json
{
  "ticker": "AAPL",
  "price": {
    "current_price": 208.62,
    "currency": "USD",
    "price_change": -2.54,
    "price_change_percent": -1.20,
    "price_change_direction": "down"
  },
  "isin": "US0378331005",
  "sustainability": {
    "esgScores": {
      "totalEsg": 18.88,
      "environmentScore": 2.33,
      "socialScore": 7.98,
      "governanceScore": 8.58,
      "esgPerformance": "LAG_PERF"
    }
  },
  "financials": {
    "income_statement": { "損益計算書データ" },
    "balance_sheet": { "貸借対照表データ" },
    "cashflow": { "キャッシュフローデータ" }
  },
  "holders": {
    "major_holders": [ "大株主情報" ],
    "institutional_holders": [ "機関投資家情報" ],
    "mutualfund_holders": [ "投資信託情報" ]
  }
}
```

### 3. チャート生成 (`/chart`)

**URL**: `GET /chart?ticker={symbol}&period={period}&type={type}&size={size}`

**説明**: 株価チャートの画像を生成してPNG形式で返却

**パラメータ**:
- `ticker` (必須): ティッカーシンボル
- `period` (オプション): 期間（デフォルト: 1mo）
- `type` (オプション): チャートタイプ（line, candle、デフォルト: line）
- `size` (オプション): 画像サイズ（例: 800x400、デフォルト: 800x400）

**使用例**:
```bash
# 折れ線チャート
curl "https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod/chart?ticker=AAPL&period=1mo" --output aapl_chart.png

# ローソク足チャート
curl "https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod/chart?ticker=TSLA&period=1y&type=candle&size=1200x600" --output tsla_candle.png
```

## 🛠 開発・デプロイ

### 前提条件

- AWS CLI
- AWS SAM CLI
- Docker
- Python 3.9+

### ローカル開発

```bash
# 依存関係インストール
pip install -r requirements.txt

# ローカルテスト
python local_test.py
python test_api.py
```

### デプロイ

```bash
# 一発デプロイ
./deploy.sh
```

デプロイスクリプトは以下を自動実行します：
1. AWS認証確認
2. S3バケット作成
3. SAMビルド
4. Dockerイメージビルド
5. Lambda関数デプロイ
6. API Gateway設定
7. 環境変数設定
8. Swagger仕様書自動生成

### 環境要件

**Python依存関係**:
```txt
yfinance>=0.2.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
mplfinance==0.12.8b9
pillow>=9.5.0
requests>=2.28.0
PyYAML>=6.0.0
boto3>=1.26.0
```

**AWS リソース**:
- Lambda Function (Container Image)
- API Gateway (REST API)
- ECR Repository
- CloudFormation Stack
- IAM Roles

## 📈 使用例とベストプラクティス

### Python での使用例

```python
import requests
import json

# 銘柄検索
response = requests.get(
    "https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod/search",
    params={"q": "tesla", "limit": 5}
)
search_results = response.json()

# 包括的データ取得
response = requests.get(
    "https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod/info",
    params={"ticker": "TSLA", "period": "1y"}
)
company_data = response.json()

# ESG情報の取得
esg_score = company_data["sustainability"]["esgScores"]["totalEsg"]
print(f"ESGスコア: {esg_score}")

# 財務データの取得
revenue = company_data["financials"]["income_statement"]["Total Revenue"]
print(f"売上高: {revenue}")
```

### JavaScript での使用例

```javascript
// ブラウザから直接アクセス（CORS対応済み）
async function getStockData(ticker) {
    const response = await fetch(
        `https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod/info?ticker=${ticker}&period=1y`
    );
    const data = await response.json();
    
    // 現在価格
    console.log(`現在価格: ${data.price.current_price} ${data.price.currency}`);
    
    // ESG情報
    const esg = data.sustainability.esgScores;
    console.log(`ESG総合スコア: ${esg.totalEsg}`);
    
    // ISIN
    console.log(`ISIN: ${data.isin}`);
    
    return data;
}

getStockData("AAPL");
```

## 🔧 高度な機能

### エラーハンドリング

```json
{
  "error": "エラーメッセージ",
  "details": "詳細なエラー情報",
  "status": "error", 
  "timestamp": "2025-07-18T00:39:20.517464Z"
}
```

### レート制限

- **エンドポイント毎**: 1000リクエスト/分
- **全体**: 10000リクエスト/日
- **地域制限**: なし（グローバル対応）

### データ形式

- **日付**: ISO 8601形式 (`YYYY-MM-DD`)
- **タイムスタンプ**: ISO 8601形式 (`YYYY-MM-DDTHH:mm:ss.ffffffZ`)
- **数値**: float型（小数点以下2桁まで）
- **通貨**: 3文字通貨コード（USD, JPY, EUR等）

## 📚 技術仕様

### アーキテクチャ

```
[Client] → [API Gateway] → [Lambda Function] → [YFinance API]
                ↓
        [Swagger UI / Documentation]
                ↓
        [ECR Container Registry]
```

### 技術スタック

- **ランタイム**: Python 3.9 (AWS Lambda)
- **データソース**: Yahoo Finance (yfinance ライブラリ)
- **インフラ**: AWS SAM (Serverless Application Model)
- **コンテナ**: Docker (Lambda Container Images)
- **API**: REST API (OpenAPI 3.0準拠)
- **チャート**: matplotlib + mplfinance

### セキュリティ

- **HTTPS**: 全通信はTLS暗号化
- **CORS**: 適切なCORSヘッダー設定
- **認証**: 現在は認証なし（パブリックAPI）
- **レート制限**: API Gateway レベルで実装

## 🤝 貢献・サポート

### 開発者向け情報

- **Repository**: YFinanceDocker
- **Branch**: develop
- **License**: MIT
- **Python**: 3.9+
- **AWS Region**: ap-northeast-1

### サポートされる市場

- **米国株**: NASDAQ, NYSE
- **日本株**: 東京証券取引所（.T サフィックス）
- **その他**: Yahoo Financeがサポートする全市場

### 今後の予定

- [ ] 認証機能の追加
- [ ] Webhookサポート
- [ ] バッチ処理API
- [ ] より多くの市場サポート
- [ ] リアルタイムWebSocket API

---

**🎯 このAPIを使用して、包括的な金融データ分析アプリケーションを構築できます！**
    }
  ]
}
```

**使用例**:
```bash
curl "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/dividends/AAPL"
```

#### 6. オプション情報取得エンドポイント
**URL**: `GET https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/options/{ticker}`

**説明**: 指定されたティッカーシンボルのオプション情報を取得します。

**パラメータ**:
- `ticker` (必須): ティッカーシンボル（例: AAPL, MSFT, 7203.T）

**レスポンス例**:
```json
{
  "symbol": "AAPL",
  "currentPrice": 208.62,
  "options": {
    "calls": [
      {
        "strike": 200,
        "lastPrice": 12.50,
        "bid": 12.45,
        "ask": 12.55,
        "volume": 1500,
        "openInterest": 5000
      }
    ],
    "puts": [
      {
        "strike": 200,
        "lastPrice": 4.20,
        "bid": 4.15,
        "ask": 4.25,
        "volume": 800,
        "openInterest": 3000
      }
    ]
  }
}
```

**使用例**:
```bash
curl "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/options/AAPL"
```

#### 7. 財務情報取得エンドポイント
**URL**: `GET https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/financials/{ticker}`

**説明**: 指定されたティッカーシンボルの財務情報を取得します。

**パラメータ**:
- `ticker` (必須): ティッカーシンボル（例: AAPL, MSFT, 7203.T）

**レスポンス例**:
```json
{
  "symbol": "AAPL",
  "financials": {
    "incomeStatement": {
      "revenue": 394328000000,
      "grossProfit": 170782000000,
      "operatingIncome": 114301000000,
      "netIncome": 96995000000
    },
    "balanceSheet": {
      "totalAssets": 352755000000,
      "totalLiabilities": 287912000000,
      "totalEquity": 64843000000
    },
    "cashFlow": {
      "operatingCashFlow": 110543000000,
      "investingCashFlow": -109559000000,
      "financingCashFlow": -110543000000
    }
  }
}
```

**使用例**:
```bash
curl "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/financials/AAPL"
```

#### 8. アナリスト予想取得エンドポイント
**URL**: `GET https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/analysts/{ticker}`

**説明**: 指定されたティッカーシンボルのアナリスト予想情報を取得します。

**パラメータ**:
- `ticker` (必須): ティッカーシンボル（例: AAPL, MSFT, 7203.T）

**レスポンス例**:
```json
{
  "symbol": "AAPL",
  "analystRecommendations": {
    "strongBuy": 15,
    "buy": 20,
    "hold": 8,
    "sell": 2,
    "strongSell": 1,
    "meanRecommendation": "Buy",
    "targetMean": 225.50,
    "targetMedian": 220.00,
    "targetHigh": 250.00,
    "targetLow": 180.00
  }
}
```

**使用例**:
```bash
curl "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/analysts/AAPL"
```

#### 9. 銘柄検索エンドポイント
**URL**: `GET https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/search?query={query}&region={region}`

**説明**: キーワードによる銘柄検索を実行します。

**パラメータ**:
- `query` (必須): 検索キーワード（例: apple, microsoft）
- `region` (オプション): 検索リージョン（デフォルト: US）
  - `US`: アメリカ市場
  - `JP`: 日本市場

**レスポンス例**:
```json
{
  "query": "apple",
  "region": "US",
  "count": 7,
  "results": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "exchange": "NMS",
      "type": "Equity",
      "score": 31292.0
    },
    {
      "symbol": "APLE",
      "name": "Apple Hospitality REIT Inc",
      "exchange": "NYQ",
      "type": "Equity",
      "score": 1250.0
    }
  ]
}
```

**使用例**:
```bash
curl "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/search?query=apple"
curl "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/search?query=トヨタ&region=JP"
```

### エラーレスポンス

すべてのエンドポイントで、エラーが発生した場合は以下の形式でレスポンスが返されます：

```json
{
  "error": "エラーメッセージ",
  "status": "error",
  "timestamp": "2025-01-14T10:30:00Z"
}
```

### 共通レスポンスヘッダー

すべてのAPIレスポンスには以下のヘッダーが含まれます：

- `Content-Type: application/json`
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, POST, OPTIONS`
- `Access-Control-Allow-Headers: Content-Type`

### レート制限

- 各エンドポイント: 1000リクエスト/分
- 全体: 10000リクエスト/日
- 超過時は429エラーが返されます
```

### API の使用例

```bash
# 株価取得
curl "https://your-api-url/prod/price/AAPL"

# 詳細情報取得
curl "https://your-api-url/prod/info/MSFT"

# 履歴データ取得
curl "https://your-api-url/prod/history/GOOGL?period=1y"

# ニュース取得
curl "https://your-api-url/prod/news/AAPL"

# 配当情報取得
curl "https://your-api-url/prod/dividends/MSFT"

# オプション情報取得
curl "https://your-api-url/prod/options/TSLA"

# 財務情報取得
curl "https://your-api-url/prod/financials/NVDA"

# アナリスト予想取得
curl "https://your-api-url/prod/analysts/AMZN"

# 銘柄検索
curl "https://your-api-url/prod/search?query=apple"
curl "https://your-api-url/prod/search?query=トヨタ&region=JP"
```

### リソースの削除

```bash
# AWS リソースを削除
./cleanup.sh
```

## AWS デプロイマニュアル

このセクションでは、YFinanceアプリケーションをAWS Lambdaにデプロイする詳細な手順を説明します。

### 1. AWS アカウントの準備

1. AWSアカウントを持っていない場合は、[AWS公式サイト](https://aws.amazon.com/)で作成してください
2. IAMユーザーに以下の権限が必要です：
   - AWSLambdaFullAccess
   - AmazonAPIGatewayAdministrator
   - AWSCloudFormationFullAccess
   - IAMFullAccess（または最小限必要な権限）

### 2. 開発環境のセットアップ

1. AWS CLIのインストール：
   ```bash
   # macOS/Linux
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   
   # Windows
   # https://aws.amazon.com/cli/ からインストーラーをダウンロード
   ```

2. AWS SAM CLIのインストール：
   ```bash
   pip install aws-sam-cli
   ```

3. AWS認証情報の設定：
   ```bash
   aws configure
   # AWS Access Key ID: [アクセスキーを入力]
   # AWS Secret Access Key: [シークレットキーを入力]
   # Default region name: [リージョン名を入力（例：ap-northeast-1）]
   # Default output format: [出力形式を入力（例：json）]
   ```

### 3. プロジェクトの準備

1. 依存関係のインストール：
   ```bash
   pip install -r requirements.txt
   ```

2. `template.yaml`の確認：
   - Lambda関数の設定
   - API Gatewayのエンドポイント設定
   - 必要に応じて、タイムアウトやメモリサイズを調整

### 4. ローカルテスト

デプロイ前にローカルでテストすることをお勧めします：

1. 基本機能のテスト：
   ```bash
   python test_api.py
   ```

2. ローカルHTTPサーバーでのテスト：
   ```bash
   python local_test.py
   # ブラウザで http://localhost:8000 にアクセス
   ```

### 5. AWS へのデプロイ

1. デプロイスクリプトの実行：
   ```bash
   ./deploy.sh
   ```

2. デプロイプロセスの流れ：
   - SAMテンプレートのビルド
   - CloudFormationスタックの作成/更新
   - Lambda関数のデプロイｙ
   - API Gatewayの設定

3. デプロイが成功すると、以下のような出力が表示されます：
   ```
   API Gateway URL: https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/
   
   === API エンドポイント ===
   株価取得: GET https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/price/{ticker}
   詳細情報: GET https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/info/{ticker}
   履歴データ: GET https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/history/{ticker}?period=1mo
   ```

### 6. デプロイ後の確認

1. エンドポイントのテスト：
   ```bash
   # 株価取得
   curl "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/price/AAPL"
   
   # 詳細情報取得
   curl "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/info/MSFT"
   
   # 履歴データ取得
   curl "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/history/GOOGL?period=1y"
   ```

2. AWS Management Consoleでの確認：
   - Lambda関数の確認（AWS Lambdaコンソール）
   - API Gatewayの確認（API Gatewayコンソール）
   - CloudFormationスタックの確認（CloudFormationコンソール）

### 7. トラブルシューティング

1. デプロイエラー：
   - AWS認証情報が正しく設定されているか確認
   - IAMユーザーに必要な権限があるか確認
   - AWS_DEFAULT_REGIONが正しく設定されているか確認

2. Lambda実行エラー：
   - CloudWatchログを確認（AWS Lambdaコンソールから）
   - 依存関係が正しくパッケージングされているか確認
   - タイムアウト設定が適切か確認

3. API Gatewayエラー：
   - CORSが正しく設定されているか確認
   - Lambda統合が正しく設定されているか確認

### 8. リソースの削除

プロジェクトが不要になった場合：
```bash
./cleanup.sh
```

このスクリプトは以下のリソースを削除します：
- CloudFormationスタック
- Lambda関数
- API Gateway
- IAMロール

## API仕様

詳細なAPI仕様については `api_documentation.md` を参照してください。

### エンドポイント一覧

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/price/{ticker}` | GET | 現在の株価取得 |
| `/info/{ticker}` | GET | 株式の詳細情報取得 |
| `/history/{ticker}` | GET | 株価履歴取得（期間指定可能） |
| `/news/{ticker}` | GET | 関連ニュース取得 |
| `/dividends/{ticker}` | GET | 配当情報取得 |
| `/options/{ticker}` | GET | オプション情報取得 |
| `/financials/{ticker}` | GET | 財務情報取得 |
| `/analysts/{ticker}` | GET | アナリスト予想取得 |
| `/search` | GET | 銘柄検索（キーワード・リージョン指定） |

### 対応するティッカーシンボル

- **アメリカ株**: AAPL, MSFT, GOOGL, TSLA, NVDA, AMZN, META, NFLX, AMD, INTC など
- **日本株**: 7203.T (トヨタ), 9984.T (ソフトバンク), 6501.T (日立), 6758.T (ソニー), 6861.T (キーエンス) など
- **その他の世界市場**: 対応する取引所の形式に従う

## プロジェクト構成

```
.
├── yfinance_cli.py          # CLIツール（元の実装）
├── yfinance_sample.py       # サンプルプログラム
├── lambda_function.py       # AWS Lambda関数
├── template.yaml            # AWS SAM テンプレート
├── deploy.sh               # デプロイスクリプト
├── cleanup.sh              # リソース削除スクリプト
├── test_api.py             # APIテスト用スクリプト
├── local_test.py           # ローカルHTTPサーバー
├── api_documentation.md    # API詳細ドキュメント
├── requirements.txt        # Python依存関係
└── README.md              # このファイル
```

## トラブルシューティング

### デプロイエラー

1. **AWS認証エラー**: `aws configure` で認証情報を設定
2. **権限エラー**: IAMユーザーに適切な権限を付与
3. **リージョンエラー**: `AWS_DEFAULT_REGION` 環境変数を設定

### API エラー

1. **CORS エラー**: すでに設定済みですが、ブラウザの開発者ツールで確認
2. **データ取得エラー**: Yahoo Finance の制限や無効なティッカーシンボル
3. **タイムアウト**: Lambda の実行時間制限（30秒）を確認

## 開発者向け情報

### コード構成

- **CLI機能**: `yfinance_cli.py` - 元のCLI実装
- **API機能**: `lambda_function.py` - AWS Lambda用の実装
- **共通ロジック**: 株価取得ロジックは両方で共有

### カスタマイズ

- **タイムアウト調整**: `template.yaml` の `Timeout` 設定
- **メモリ調整**: `template.yaml` の `MemorySize` 設定
- **CORS設定**: `lambda_function.py` と `template.yaml` の設定

## ライセンス

このプロジェクトはオープンソースです。

## 出力項目の説明

### 価格情報（--price）

| 項目 | 説明 | 例 |
|------|------|-----|
| 現在価格 | 最新の取引価格 | $208.62 |

### 詳細情報（--info）

| 項目 | 説明 | 例 |
|------|------|-----|
| 会社名 | 企業の正式名称 | Apple Inc. |
| 現在価格 | 最新の取引価格 | $208.62 |
| 前日終値 | 前営業日の終値 | $211.16 |
| 時価総額 | 発行済み株式総数×株価 | $3,115,906,498,560 |
| 配当利回り | 年間配当金÷株価×100（%） | 0.51 |
| P/E比率 | 株価収益率（株価÷1株当たり利益） | 32.44 |
| 52週高値 | 過去52週間の最高値 | $260.1 |
| 52週安値 | 過去52週間の最安値 | $169.21 |

### 株価履歴（--history）

| 項目 | 説明 | 例 |
|------|------|-----|
| Date | 取引日 | 2025-07-14 |
| Open | 始値 | 209.93 |
| High | 高値 | 210.91 |
| Low | 安値 | 207.54 |
| Close | 終値 | 208.62 |
| Volume | 出来高（取引量） | 38,711,400 |

### 検索結果（search）

| 項目 | 説明 | 例 |
|------|------|-----|
| シンボル | ティッカーシンボル | AAPL |
| 名称 | 企業/銘柄名 | Apple Inc. |
| 取引所 | 上場している取引所 | NMS (NASDAQ) |
| 種類 | 証券の種類 | Equity (株式) |

## JSON形式の出力

`--json`オプションを使用すると、結果をJSON形式で取得できます。これはAPIとしての利用や他のプログラムとの連携に便利です。

### 価格情報のJSON
```json
{
  "price": 208.62
}
```

### 詳細情報のJSON
```json
{
  "info": {
    "symbol": "AAPL",        // ティッカーシンボル
    "name": "Apple Inc.",    // 会社名
    "currentPrice": 208.62,  // 現在価格
    "previousClose": 211.16, // 前日終値
    "marketCap": 3115906498560, // 時価総額
    "dividendYield": 0.51,   // 配当利回り
    "trailingPE": 32.44479,  // P/E比率
    "fiftyTwoWeekHigh": 260.1, // 52週高値
    "fiftyTwoWeekLow": 169.21  // 52週安値
  }
}
```

### 株価履歴のJSON
```json
{
  "history": {
    "2025-07-14": {
      "Open": 209.9299926758,  // 始値
      "High": 210.9100036621,  // 高値
      "Low": 207.5399932861,   // 安値
      "Close": 208.6199951172, // 終値
      "Volume": 38711400,      // 出来高
      "Dividends": 0.0,        // 配当
      "Stock Splits": 0.0      // 株式分割
    },
    // 他の日付...
  }
}
```

### 検索結果のJSON
```json
{
  "query": "apple",        // 検索キーワード
  "region": "US",          // 検索リージョン
  "count": 7,              // 結果数
  "results": [
    {
      "symbol": "AAPL",    // ティッカーシンボル
      "name": "Apple Inc.", // 会社名
      "exchange": "NMS",   // 取引所
      "type": "Equity",    // 証券の種類
      "score": 31292.0     // 検索スコア（関連度）
    },
    // 他の結果...
  ]
}
```

### Docker 使用のメリット
- Python環境のインストール不要
- 依存関係の管理が簡単
- どのOSでも同じ動作を保証
- 仮想環境の作成・管理が不要

### 利用可能な期間オプション
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

## ティッカーシンボルの例

### 米国株式
- `AAPL`: Apple Inc.
- `MSFT`: Microsoft Corporation
- `GOOGL`: Alphabet Inc.
- `AMZN`: Amazon.com Inc.
- `TSLA`: Tesla Inc.

### 日本株式
- `7203.T`: トヨタ自動車
- `6758.T`: ソニーグループ
- `9984.T`: ソフトバンクグループ
- `6861.T`: キーエンス
- `7974.T`: 任天堂

## 機能

### yfinance_sample.py
- 株式データの取得
- 基本情報の表示
- リターン分析
- グラフ描画（matplotlib）

### yfinance_cli.py
- コマンドラインからの株式情報取得
- 現在価格の表示
- 詳細情報の表示
- 株価履歴の表示
- JSON形式での出力

### yfinance_search.py
- キーワードによる銘柄検索
- 米国・日本市場での検索
- 検索結果の表形式表示
- JSON形式での出力

## ファイル構成

### 主要ファイル
- `lambda_function.py`: AWS Lambda関数のメインコード
- `template.yaml`: AWS SAMテンプレート
- `deploy.sh`: デプロイスクリプト
- `swagger_generator_advanced.py`: Swagger自動生成ツール（コード解析ベース）
- `swagger_auto.json`: 自動生成されるSwagger仕様書

### CLIツール
- `yfinance_cli.py`: コマンドライン株式データ取得ツール
- `yfinance_search.py`: 銘柄検索ツール
- `yfinance_sample.py`: サンプルプログラム

### テスト・開発用
- `test_api.py`: API機能テスト
- `local_test.py`: ローカルHTTPサーバーテスト
- `requirements.txt`: Python依存関係

## 注意事項

- インターネット接続が必要です
- Yahoo FinanceのAPIを使用しているため、利用制限がある場合があります
- 日本株式の場合は、ティッカーシンボルの後に`.T`を付けてください
- Swagger仕様書はデプロイ時に自動生成されます（`swagger_auto.json`）

## トラブルシューティング

### 仮想環境が有効になっていない場合
```bash
source venv/bin/activate
```

### 依存関係の再インストール
```bash
pip install -r requirements.txt --force-reinstall
```

### 権限エラーの場合
```bash
chmod +x yfinance_sample.py yfinance_cli.py yfinance_search.py
```

### Dockerのトラブルシューティング
```bash
# イメージの再ビルド
docker build --no-cache -t yfinance .

# Docker Composeの再ビルド
docker-compose build --no-cache
``` 