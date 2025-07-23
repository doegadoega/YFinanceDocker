# YFinance Docker プロジェクト

YFinanceを使用した株式データ取得システムを、Lambda、Docker、ローカル実行の3つのパターンで統一された出力形式で提供します。

## 🎯 プロジェクトの特徴

### ✅ 完全統一された出力形式
- **Lambda関数を直接使用**することで、3つの実行環境で完全に同じ出力
- 同じ関数から呼び出し、同じデータ構造、同じエラーハンドリング
- 重複コードの排除により保守性が大幅向上

### 📊 包括的な金融データ（25種類以上）
- 基本情報（企業名、業界、セクター）
- 価格情報（現在価格、変化率、通貨）
- ESG情報（環境・社会・ガバナンススコア）
- 財務諸表（損益計算書、貸借対照表、キャッシュフロー）
- 株主情報（大株主、機関投資家）
- アナリスト情報（推奨、目標価格）
- ニュース情報
- 配当情報
- 株価履歴
- ISIN情報
- 推奨履歴
- 金融ニュースRSS
- 株価関連ランキング（上昇率、下落率、出来高、時価総額）
- セクター・業界ランキング
- 暗号通貨ランキング
- 主要指数情報
- 為替レート
- 商品価格
- 市場開閉状況
- その他詳細データ

### 🔌 柔軟なAPI設計（新機能）
- **統合版エンドポイント**: `/tickerDetail` - 全要素を一度に取得
- **個別エンドポイント**: 各要素を個別に取得可能
  - `/basic` - 基本情報のみ
  - `/price` - 株価情報のみ
  - `/history` - 履歴情報のみ
  - `/financials` - 財務情報のみ
  - `/analysts` - アナリスト情報のみ
  - `/holders` - 株主情報のみ
  - `/events` - イベント情報のみ
  - `/news` - ニュース情報のみ
  - `/options` - オプション情報のみ
  - `/sustainability` - ESG情報のみ
- **効率的なデータ取得**: 必要な情報のみを取得してレスポンス時間を短縮
- **重複排除**: 各要素専用関数を統合版で再利用

### 🔍 高速な株式検索機能
- 複数地域対応（US, JP, DE, CA, AU, GB, FR, IT, ES, KR, IN, HK, SG）
- リアルタイム価格情報付き
- ファジー検索対応

## 🏗️ アーキテクチャ

### 統一方式：Lambda関数直接使用
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   yfinance_     │    │   local_test.py │    │   Docker        │
│   sample.py     │    │   (HTTP Server) │    │   Container     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ lambda_function │
                    │      .py        │
                    │  (共通関数群)    │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   AWS Lambda    │
                    │   (本番環境)     │
                    └─────────────────┘
```

### 重複排除の仕組み
- **共通関数を`lambda_function.py`に集約**
  - `format_currency()`: 通貨フォーマット
  - `get_execution_info()`: 実行環境情報
  - `display_*()`: 表示関数群
  - `validate_ticker_parameter()`: パラメータバリデーション
- **各要素専用関数の再利用**
  - `get_stock_basic_info_api()`: 基本情報取得
  - `get_stock_price_api()`: 株価情報取得
  - `get_stock_history_api()`: 履歴情報取得
  - その他各要素専用関数
- **統合版での関数呼び出し**
  - `tickerDetail`エンドポイントで各要素専用関数を呼び出し
  - 重複コードを完全排除
  - 保守性と一貫性を確保

## 🚀 実行方法

### 1. ローカル実行
```bash
# サンプルプログラム実行
python yfinance_sample.py

# 検索ツール実行
python yfinance_search.py apple US

# CLIツール実行
python yfinance_cli.py search apple US
python yfinance_cli.py info AAPL 1mo          # 統合版（全要素）
python yfinance_cli.py basic AAPL             # 基本情報のみ
python yfinance_cli.py price AAPL             # 株価情報のみ
python yfinance_cli.py history AAPL 1y        # 履歴情報のみ
python yfinance_cli.py financials AAPL        # 財務情報のみ
python yfinance_cli.py analysts AAPL          # アナリスト情報のみ
python yfinance_cli.py holders AAPL           # 株主情報のみ
python yfinance_cli.py events AAPL            # イベント情報のみ
python yfinance_cli.py news AAPL              # ニュース情報のみ
python yfinance_cli.py options AAPL           # オプション情報のみ
python yfinance_cli.py sustainability AAPL    # ESG情報のみ
python yfinance_cli.py home                    # ホーム画面情報
python yfinance_cli.py rankings gainers --limit 10    # 上昇率TOP10
python yfinance_cli.py rankings losers --limit 10     # 下落率TOP10
python yfinance_cli.py rankings volume --limit 20     # 出来高TOP20
python yfinance_cli.py rankings market-cap --limit 20 # 時価総額TOP20
python yfinance_cli.py sectors --limit 10             # セクターランキングTOP10
python yfinance_cli.py crypto --sort change --limit 10 # 暗号通貨ランキング
python yfinance_cli.py indices                    # 主要指数一覧
python yfinance_cli.py currencies                 # 為替レート
python yfinance_cli.py commodities                # 商品価格
python yfinance_cli.py status                     # 市場開閉状況

### 2. Docker実行

#### ローカルテスト用
```bash
# ローカルテスト用Dockerコンテナビルド
docker-compose build yfinance-local

# 基本的なサンプル実行
docker-compose run --rm yfinance-local python yfinance_sample.py

# CLIツール実行（統合版）
docker-compose run --rm yfinance-local python yfinance_cli.py info AAPL 1mo

# CLIツール実行（個別要素）
docker-compose run --rm yfinance-local python yfinance_cli.py basic AAPL
docker-compose run --rm yfinance-local python yfinance_cli.py price AAPL
docker-compose run --rm yfinance-local python yfinance_cli.py history AAPL 1y
docker-compose run --rm yfinance-local python yfinance_cli.py financials AAPL
docker-compose run --rm yfinance-local python yfinance_cli.py analysts AAPL
docker-compose run --rm yfinance-local python yfinance_cli.py holders AAPL
docker-compose run --rm yfinance-local python yfinance_cli.py events AAPL
docker-compose run --rm yfinance-local python yfinance_cli.py news AAPL
docker-compose run --rm yfinance-local python yfinance_cli.py options AAPL
docker-compose run --rm yfinance-local python yfinance_cli.py sustainability AAPL
docker-compose run --rm yfinance-local python yfinance_cli.py home
docker-compose run --rm yfinance-local python yfinance_cli.py rankings gainers --limit 10
docker-compose run --rm yfinance-local python yfinance_cli.py sectors --limit 10
docker-compose run --rm yfinance-local python yfinance_cli.py crypto --sort change --limit 10
docker-compose run --rm yfinance-local python yfinance_cli.py indices
docker-compose run --rm yfinance-local python yfinance_cli.py currencies
docker-compose run --rm yfinance-local python yfinance_cli.py commodities
docker-compose run --rm yfinance-local python yfinance_cli.py status

# 検索機能実行
docker-compose run --rm yfinance-local python yfinance_search.py Apple

# ローカルテスト実行
docker-compose run --rm yfinance-local python local_test.py

# 一括テスト実行
./docker_test.sh
```

#### Lambda用（デプロイ用）
```bash
# Lambda用Dockerコンテナビルド
docker-compose build yfinance-lambda

# Lambda関数テスト
./docker_lambda_test.sh

# 個別テスト
docker-compose run --rm yfinance-lambda python -c "import lambda_function"
```

### 3. Lambda実行
```bash
# AWS CLIでデプロイ
aws cloudformation deploy --template-file template.yaml --stack-name yfinance-stack

# API Gateway経由でアクセス（統合版）
curl "https://your-api-gateway-url/prod/search?q=apple&region=US"
curl "https://your-api-gateway-url/prod/tickerDetail?ticker=AAPL&period=1mo"

# API Gateway経由でアクセス（個別要素）
curl "https://your-api-gateway-url/prod/basic?ticker=AAPL"
curl "https://your-api-gateway-url/prod/price?ticker=AAPL"
curl "https://your-api-gateway-url/prod/history?ticker=AAPL&period=1y"
curl "https://your-api-gateway-url/prod/financials?ticker=AAPL"
curl "https://your-api-gateway-url/prod/analysts?ticker=AAPL"
curl "https://your-api-gateway-url/prod/holders?ticker=AAPL"
curl "https://your-api-gateway-url/prod/events?ticker=AAPL"
curl "https://your-api-gateway-url/prod/news?ticker=AAPL"
curl "https://your-api-gateway-url/prod/options?ticker=AAPL"
curl "https://your-api-gateway-url/prod/sustainability?ticker=AAPL"
curl "https://your-api-gateway-url/prod/home"
curl "https://your-api-gateway-url/prod/rankings/stocks?type=gainers&market=sp500&limit=10"
curl "https://your-api-gateway-url/prod/rankings/sectors?limit=10"
curl "https://your-api-gateway-url/prod/rankings/crypto?sort=change&limit=10"
curl "https://your-api-gateway-url/prod/markets/indices"
curl "https://your-api-gateway-url/prod/markets/currencies"
curl "https://your-api-gateway-url/prod/markets/commodities"
curl "https://your-api-gateway-url/prod/markets/status"
```

### 4. ローカルHTTPサーバー
```bash
# ローカルテストサーバー起動
python local_test.py

# ブラウザでアクセス
# http://localhost:8000
```

## 📁 ファイル構成

```
YFinanceDocker/
├── lambda_function.py          # メインLambda関数（共通関数群）
├── yfinance_sample.py          # サンプルプログラム
├── yfinance_search.py          # 検索ツール
├── yfinance_cli.py             # CLIツール
├── local_test.py               # ローカルHTTPサーバー
├── Dockerfile                  # Lambda用Docker設定
├── Dockerfile.local            # ローカルテスト用Docker設定
├── docker-compose.yml          # Docker Compose設定
├── docker_test.sh              # ローカルテスト実行スクリプト
├── docker_lambda_test.sh       # Lambdaテスト実行スクリプト
├── template.yaml               # CloudFormationテンプレート
├── requirements.txt            # Python依存関係
└── README.md                   # このファイル
```

### Docker設定の分離

| ファイル | 用途 | 説明 |
|----------|------|------|
| `Dockerfile` | Lambda用 | AWS Lambda環境用の設定 |
| `Dockerfile.local` | ローカルテスト用 | 開発・テスト環境用の設定 |
| `docker-compose.yml` | 両方のサービス定義 | ローカルとLambda両方のサービスを定義 |

## 🔧 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `EXECUTION_MODE` | 実行モード（LOCAL/DOCKER/LAMBDA） | `LOCAL` |
| `YFINANCE_API_URL` | API Gateway URL | `https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod` |

## 📊 出力例

### 検索結果
```json
{
  "query": "apple",
  "region": "US",
  "count": 5,
  "results": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "exchange": "NMS",
      "type": "EQUITY",
      "current_price": 150.25,
      "currency": "USD",
      "price_change": 2.15,
      "price_change_percent": 1.45,
      "price_change_direction": "up"
    }
  ],
  "execution_info": {
    "mode": "LOCAL",
    "timestamp": "2024-01-15T10:30:00",
    "server": "lambda"
  }
}
```

## 🔌 API エンドポイント

### 1. 検索 API
- **エンドポイント**: `/search`
- **メソッド**: GET
- **パラメータ**:
  - `q`: 検索クエリ（必須）
  - `region`: 検索地域（オプション、デフォルト: US）
- **例**: `GET /search?q=apple&region=US`

### 2. 包括的情報 API（統合版）
- **エンドポイント**: `/tickerDetail`
- **メソッド**: GET
- **パラメータ**:
  - `ticker`: ティッカーシンボル（必須）
  - `period`: 履歴期間（オプション、デフォルト: 1mo）
- **例**: `GET /tickerDetail?ticker=AAPL&period=1y`
- **説明**: 全ての要素を統合して返す（各要素専用関数を内部で呼び出し）

### 🆕 金融ニュースRSS API（/news/rss）

- **エンドポイント**: `/news/rss`
- **メソッド**: GET
- **パラメータ**:
  - `limit`: 取得件数（デフォルト: 50, 最大: 200）
  - `category`: ニュースカテゴリでフィルタ（例: general, market）
  - `source`: ソース名でフィルタ（例: Yahoo, MarketWatch）
  - `sort`: ソート順（published_desc, published_asc, title_asc）
- **例**: `GET /news/rss?limit=10`
- **取得元**:
  - [Yahoo Finance](https://finance.yahoo.com/rss/2.0)
  - [MarketWatch Top Stories](https://www.marketwatch.com/rss/topstories)
- **説明**: 上記2つの金融ニュースRSSフィードから最新ニュースを一括取得し、重複排除・カテゴリ/ソース/件数/ソート指定が可能です。

#### 出力例
```json
{
  "status": "success",
  "data": [
    {
      "id": "a1b2c3d4e5f6",
      "title": "Philip Morris 2Q EPS Tops Views, Company Boosts 2025 EPS Projection",
      "summary": "Philip Morris International reported second-quarter earnings that topped analysts’ expectations and raised its full-year EPS guidance...",
      "url": "https://www.wsj.com/business/earnings/philip-morris-2q-eps-tops-views-company-boosts-2025-eps-projection-fb09063d?siteid=yhoof2&yptr=yahoo",
      "source": "Yahoo Finance",
      "category": "general",
      "published_at": "2025-07-22T12:04:00Z",
      "author": "The Wall Street Journal",
      "image_url": null,
      "tags": []
    }
  ],
  "metadata": {
    "total_sources": 2,
    "total_articles": 1,
    "sources_used": [
      "Yahoo Finance",
      "MarketWatch Top Stories"
    ],
    "category_filter": "all",
    "source_filter": "",
    "sort": "published_desc",
    "last_updated": "2025-07-22T12:10:00Z"
  },
  "timestamp": "2025-07-22T12:10:00Z"
}
```

### 3. 個別要素 API（新機能）

#### 3.1 基本情報 API
- **エンドポイント**: `/basic`
- **メソッド**: GET
- **パラメータ**: `ticker`（必須）
- **例**: `GET /basic?ticker=AAPL`

#### 3.2 株価情報 API
- **エンドポイント**: `/price`
- **メソッド**: GET
- **パラメータ**: `ticker`（必須）
- **例**: `GET /price?ticker=AAPL`

#### 3.3 履歴情報 API
- **エンドポイント**: `/history`
- **メソッド**: GET
- **パラメータ**:
  - `ticker`（必須）
  - `period`（オプション、デフォルト: 1mo）
- **例**: `GET /history?ticker=AAPL&period=1y`

#### 3.4 財務情報 API
- **エンドポイント**: `/financials`
- **メソッド**: GET
- **パラメータ**: `ticker`（必須）
- **例**: `GET /financials?ticker=AAPL`

#### 3.5 アナリスト情報 API
- **エンドポイント**: `/analysts`
- **メソッド**: GET
- **パラメータ**: `ticker`（必須）
- **例**: `GET /analysts?ticker=AAPL`

#### 3.6 株主情報 API
- **エンドポイント**: `/holders`
- **メソッド**: GET
- **パラメータ**: `ticker`（必須）
- **例**: `GET /holders?ticker=AAPL`

#### 3.7 イベント情報 API
- **エンドポイント**: `/events`
- **メソッド**: GET
- **パラメータ**: `ticker`（必須）
- **例**: `GET /events?ticker=AAPL`

#### 3.8 ニュース情報 API
- **エンドポイント**: `/news`
- **メソッド**: GET
- **パラメータ**: `ticker`（必須）
- **例**: `GET /news?ticker=AAPL`

### 3.12 金融ニュースRSS API
- **エンドポイント**: `/news/rss`
- **メソッド**: GET
- **パラメータ**:
  - `limit`（デフォルト: 50, 最大: 200）
  - `category`（任意）
  - `source`（任意）
  - `sort`（任意）
- **例**: `GET /news/rss?limit=10`
- **説明**: Yahoo Finance・MarketWatchの公式RSSから最新金融ニュースを一括取得

### 3.13 株価関連ランキング API
- **エンドポイント**: `/rankings/stocks`
- **メソッド**: GET
- **パラメータ**:
  - `type`（必須）: ランキング種別（gainers, losers, volume, market-cap）
  - `market`（必須）: 市場（sp500, nasdaq100）
  - `limit`（任意）: 取得件数（デフォルト: 10, 最大: 50）
- **例**: `GET /rankings/stocks?type=gainers&market=sp500&limit=10`
- **説明**: S&P500・NASDAQ-100の主要銘柄からリアルタイムランキングを取得（画像付き）

### 3.14 セクター・業界ランキング API
- **エンドポイント**: `/rankings/sectors`
- **メソッド**: GET
- **パラメータ**:
  - `limit`（任意）: 取得件数（デフォルト: 10, 最大: 20）
- **例**: `GET /rankings/sectors?limit=10`
- **説明**: 9つの主要セクター（Technology, Financial, Energy等）のパフォーマンス比較（画像付き）

### 3.15 暗号通貨ランキング API
- **エンドポイント**: `/rankings/crypto`
- **メソッド**: GET
- **パラメータ**:
  - `sort`（任意）: ソート基準（change, price, volume, market_cap、デフォルト: change）
  - `limit`（任意）: 取得件数（デフォルト: 10, 最大: 50）
- **例**: `GET /rankings/crypto?sort=change&limit=10`
- **説明**: 主要暗号通貨（BTC, ETH, BNB等）のランキング（画像付き）

### 3.16 主要指数 API
- **エンドポイント**: `/markets/indices`
- **メソッド**: GET
- **パラメータ**: なし
- **例**: `GET /markets/indices`
- **説明**: 主要株価指数（S&P500, NASDAQ, 日経225等）の現在値と変化率

### 3.17 為替レート API
- **エンドポイント**: `/markets/currencies`
- **メソッド**: GET
- **パラメータ**: なし
- **例**: `GET /markets/currencies`
- **説明**: 主要通貨ペア（USD/JPY, EUR/USD等）の為替レート

### 3.18 商品価格 API
- **エンドポイント**: `/markets/commodities`
- **メソッド**: GET
- **パラメータ**: なし
- **例**: `GET /markets/commodities`
- **説明**: 主要商品（金、銀、原油等）の価格情報

### 3.19 市場開閉状況 API
- **エンドポイント**: `/markets/status`
- **メソッド**: GET
- **パラメータ**: なし
- **例**: `GET /markets/status`
- **説明**: 主要市場（NYSE, NASDAQ, 東京証券取引所等）の開閉状況

### 3.9 オプション情報 API
- **エンドポイント**: `/options`
- **メソッド**: GET
- **パラメータ**: `ticker`（必須）
- **例**: `GET /options?ticker=AAPL`

### 3.10 ESG情報 API
- **エンドポイント**: `/sustainability`
- **メソッド**: GET
- **パラメータ**: `ticker`（必須）
- **例**: `GET /sustainability?ticker=AAPL`

### 3.11 ホーム画面情報 API
- **エンドポイント**: `/home`
- **メソッド**: GET
- **パラメータ**: なし
- **例**: `GET /home`
- **説明**: 株価指数、主要ETF、セクター情報を取得

### 4. チャート画像 API
- **エンドポイント**: `/chart`
- **メソッド**: GET
- **パラメータ**:
  - `ticker`: ティッカーシンボル（必須）
  - `period`: 期間（オプション、デフォルト: 1mo）
  - `size`: 画像サイズ（オプション、デフォルト: 800x400）
  - `chart_type`: チャートタイプ（オプション、デフォルト: line）
- **例**: `GET /chart?ticker=AAPL&period=1y&size=1200x600&chart_type=candlestick`

## 📊 出力例

### 検索結果
```json
{
  "query": "apple",
  "region": "US",
  "count": 5,
  "results": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "exchange": "NMS",
      "type": "EQUITY",
      "current_price": 150.25,
      "currency": "USD",
      "price_change": 2.15,
      "price_change_percent": 1.45,
      "price_change_direction": "up"
    }
  ],
  "execution_info": {
    "mode": "LOCAL",
    "timestamp": "2024-01-15T10:30:00",
    "server": "lambda"
  }
}
```

### 包括的情報（統合版）
```json
{
  "ticker": "AAPL",
  "period": "1mo",
  "info": {
    "longName": "Apple Inc.",
    "industry": "Consumer Electronics",
    "sector": "Technology"
  },
  "price": {
    "current_price": 150.25,
    "currency": "USD",
    "price_change": 2.15,
    "price_change_percent": 1.45
  },
  "sustainability": {
    "esgScores": {
      "totalEsg": 85,
      "environmentScore": 80,
      "socialScore": 90,
      "governanceScore": 85
    }
  },
  "financials": {
    "income_statement": {
      "Total Revenue": {"2023": 394328000000}
    }
  },
  "execution_info": {
    "mode": "LOCAL",
    "timestamp": "2024-01-15T10:30:00",
    "server": "lambda"
  }
}
```

### 個別要素情報（例：株価情報のみ）
```json
{
  "ticker": "AAPL",
  "price": {
    "current_price": 150.25,
    "currency": "USD",
    "previous_close": 148.10,
    "price_change": 2.15,
    "price_change_percent": 1.45,
    "price_change_direction": "up",
    "timestamp": "2024-01-15T10:30:00"
  },
  "execution_info": {
    "mode": "LOCAL",
    "timestamp": "2024-01-15T10:30:00",
    "server": "lambda"
  }
}
```

### 部分エラーの例（統合版）
```json
{
  "ticker": "AAPL",
  "period": "1mo",
  "info": {
    "longName": "Apple Inc.",
    "industry": "Consumer Electronics"
  },
  "price": {
    "current_price": 150.25,
    "currency": "USD"
  },
  "partial_errors": [
    "財務情報: 財務情報取得エラー: データが利用できません",
    "オプション情報: オプション情報取得エラー: オプションが利用できません"
  ],
  "execution_info": {
    "mode": "LOCAL",
    "timestamp": "2024-01-15T10:30:00",
    "server": "lambda"
  }
}
```

### ホーム画面情報
```json
{
  "indices": {
    "SPY": {
      "name": "S&P 500 ETF",
      "current_price": 450.25,
      "previous_close": 448.10,
      "price_change": 2.15,
      "price_change_percent": 0.48,
      "price_change_direction": "up",
      "currency": "USD"
    },
    "QQQ": {
      "name": "NASDAQ-100 ETF",
      "current_price": 380.50,
      "previous_close": 378.20,
      "price_change": 2.30,
      "price_change_percent": 0.61,
      "price_change_direction": "up",
      "currency": "USD"
    }
  },
  "sectors": {
    "XLK": {
      "name": "Technology Select Sector ETF",
      "sector": "Technology",
      "current_price": 180.75,
      "previous_close": 179.50,
      "price_change": 1.25,
      "price_change_percent": 0.70,
      "price_change_direction": "up",
      "currency": "USD"
    },
    "XLF": {
      "name": "Financial Select Sector ETF",
      "sector": "Financial",
      "current_price": 35.20,
      "previous_close": 35.80,
      "price_change": -0.60,
      "price_change_percent": -1.68,
      "price_change_direction": "down",
      "currency": "USD"
    }
  },
  "market_summary": {
    "total_indices": 10,
    "up_count": 7,
    "down_count": 2,
    "unchanged_count": 1,
    "average_change_percent": 0.35,
    "market_sentiment": "bullish"
  },
  "sector_summary": {
    "sector_averages": {
      "Technology": 0.70,
      "Financial": -1.68,
      "Energy": 0.25,
      "Healthcare": 0.45
    },
    "best_performing_sector": {
      "sector": "Technology",
      "change_percent": 0.70
    },
    "worst_performing_sector": {
      "sector": "Financial",
      "change_percent": -1.68
    }
  },
  "execution_info": {
    "mode": "LOCAL",
    "timestamp": "2024-01-15T10:30:00",
    "server": "lambda"
  }
}
```

## 🎯 統一の利点

### 1. 開発効率の向上
- **同じ関数を使用**: 3つの環境で同じロジック
- **デバッグの簡素化**: 問題の特定が容易
- **テストの統一**: 同じテストケースで全環境を検証

### 2. 保守性の向上
- **重複コードの排除**: 共通関数を一箇所で管理
- **一貫性の確保**: 出力形式が完全に統一
- **変更の簡素化**: 修正は`lambda_function.py`のみ

### 3. 信頼性の向上
- **同じエラーハンドリング**: 全環境で統一されたエラー処理
- **データ品質の保証**: 同じデータ取得ロジック
- **実行環境情報の自動付与**: トレーサビリティの確保

## 🔄 従来方式との比較

| 項目 | 従来方式 | 統一方式（Lambda関数直接使用） |
|------|----------|-------------------------------|
| コード重複 | 各ファイルに類似関数 | 共通関数を集約 |
| 出力形式 | 環境により異なる | 完全統一 |
| 保守性 | 低い（修正箇所が多い） | 高い（一箇所で管理） |
| デバッグ | 困難（環境ごとに確認） | 容易（同じロジック） |
| テスト | 環境ごとに必要 | 統一テストで全環境対応 |

## 🆕 新機能：個別要素APIの利点

### 1. 効率的なデータ取得
- **必要な情報のみ取得**: 全要素ではなく特定の要素のみを取得
- **レスポンス時間の短縮**: 不要なデータ取得を回避
- **ネットワーク負荷の軽減**: 転送データ量の削減

### 2. 柔軟なAPI設計
- **統合版**: 全要素を一度に取得したい場合
- **個別版**: 特定の要素のみ必要な場合
- **用途に応じた選択**: アプリケーションの要件に合わせて最適化

### 3. 重複排除の実現
- **関数の再利用**: 個別要素関数を統合版で再利用
- **保守性の向上**: 修正は各要素関数のみで済む
- **一貫性の確保**: 同じ関数を使用するため出力が統一

### 4. エラーハンドリングの改善
- **部分的な失敗対応**: 一部の要素でエラーが発生しても他の要素は取得
- **詳細なエラー情報**: どの要素でエラーが発生したかを明確化
- **堅牢性の向上**: 部分的な失敗でも可能な限り情報を提供

## 🆕 新機能：ランキングAPI

### 株価関連ランキング（/rankings/stocks）

#### 利用可能なランキング種別
- **gainers**: 上昇率ランキング（最も上昇した銘柄）
- **losers**: 下落率ランキング（最も下落した銘柄）
- **volume**: 出来高ランキング（最も取引が活発な銘柄）
- **market-cap**: 時価総額ランキング（最も時価総額が高い銘柄）

#### 利用可能な市場
- **sp500**: S&P500構成銘柄（50銘柄）
- **nasdaq100**: NASDAQ-100構成銘柄（50銘柄）

#### 出力例
```json
{
  "status": "success",
  "type": "gainers",
  "market": "sp500",
  "data": [
    {
      "symbol": "NVDA",
      "name": "NVIDIA Corporation",
      "current_price": 850.25,
      "previous_close": 820.10,
      "price_change": 30.15,
      "price_change_percent": 3.68,
      "volume": 45000000,
      "market_cap": 2100000000000,
      "currency": "USD"
    }
  ],
  "chart_image": "iVBORw0KGgoAAAANSUhEUgAA...",
  "metadata": {
    "total_stocks": 10,
    "limit": 10,
    "last_updated": "2025-07-22T12:30:00Z"
  },
  "timestamp": "2025-07-22T12:30:00Z"
}
```

### セクター・業界ランキング（/rankings/sectors）

#### 利用可能なランキング種別
- **performance**: セクターETFパフォーマンスランキング
- **constituent**: 構成銘柄平均パフォーマンスランキング

#### 対象セクター
- **Technology** (XLK): テクノロジー
- **Financial** (XLF): 金融
- **Energy** (XLE): エネルギー
- **Healthcare** (XLV): ヘルスケア
- **Industrial** (XLI): 工業
- **Consumer Staples** (XLP): 生活必需品
- **Consumer Discretionary** (XLY): 一般消費財
- **Utilities** (XLU): 公益事業
- **Real Estate** (XLRE): 不動産

#### 出力例
```json
{
  "status": "success",
  "type": "performance",
  "data": [
    {
      "symbol": "XLK",
      "name": "Technology",
      "current_price": 180.50,
      "previous_close": 178.20,
      "price_change": 2.30,
      "price_change_percent": 1.29,
      "constituent_change_avg": 1.45,
      "constituent_count": 5,
      "currency": "USD"
    }
  ],
  "chart_image": "iVBORw0KGgoAAAANSUhEUgAA...",
  "metadata": {
    "total_sectors": 9,
    "limit": 10,
    "last_updated": "2025-07-22T12:30:00Z"
  },
  "timestamp": "2025-07-22T12:30:00Z"
}
```

### 画像機能
- **株価関連ランキング**: 横棒グラフでランキング表示（上昇/下落は緑/赤、その他は青）
- **セクターランキング**: 2つの横棒グラフでETFパフォーマンスと構成銘柄平均を比較表示
- **Base64エンコード**: 画像はBase64文字列で返却

## 🛠️ 技術スタック

- **Python 3.9+**
- **YFinance**: 株式データ取得
- **AWS Lambda**: サーバーレス実行環境
- **Docker**: コンテナ化
- **AWS API Gateway**: RESTful API
- **CloudFormation**: インフラストラクチャ管理

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 コントリビューション

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📞 サポート

問題や質問がある場合は、GitHubのIssuesページでお知らせください。 