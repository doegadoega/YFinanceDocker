# YFinance Docker プロジェクト

YFinanceを使用した**完全統一された株式データ取得システム**を、Lambda、Docker、ローカル実行の3つのパターンで提供します。

## 🎯 プロジェクトの特徴

### ✅ 完全統一された出力形式
- **Lambda関数を直接使用**することで、3つの実行環境で完全に同じ出力
- 同じ関数から呼び出し、同じデータ構造、同じエラーハンドリング
- **重複コードの完全排除**により保守性が大幅向上

### 📊 包括的な金融データ（30種類以上）
- **基本情報**（企業名、業界、セクター、ロゴURL）
- **リアルタイム価格情報**（現在価格、変化率、通貨）
- **ESG情報**（環境・社会・ガバナンススコア）
- **財務諸表**（損益計算書、貸借対照表、キャッシュフロー）
- **株主情報**（大株主、機関投資家、投資信託）
- **アナリスト情報**（推奨、目標価格、格付け）
- **ニュース情報**（企業関連ニュース）
- **オプション情報**（コール・プットオプション）
- **配当・株式分割情報**
- **株価履歴**（カスタム期間対応）
- **ISIN情報**
- **金融ニュースRSS**（Yahoo Finance・MarketWatch）
- **株価関連ランキング**（上昇率、下落率、出来高、時価総額）
- **セクター・業界ランキング**
- **暗号通貨ランキング**
- **主要指数情報**
- **為替レート**
- **商品価格**
- **市場開閉状況**
- その他詳細データ

### 🔌 柔軟なAPI設計
- **統合版エンドポイント**: `/tickerDetail` - 全要素を一度に取得
- **個別エンドポイント**: 各要素を個別に取得可能
  - `/ticker/basic` - 基本情報のみ
  - `/ticker/price` - 株価情報のみ
  - `/ticker/history` - 履歴情報のみ
  - `/ticker/financials` - 財務情報のみ
  - `/ticker/analysts` - アナリスト情報のみ
  - `/ticker/holders` - 株主情報のみ
  - `/ticker/events` - イベント情報のみ
  - `/ticker/news` - ニュース情報のみ
  - `/ticker/options` - オプション情報のみ
  - `/ticker/sustainability` - ESG情報のみ
- **効率的なデータ取得**: 必要な情報のみを取得してレスポンス時間を短縮
- **重複排除**: 各要素専用関数を統合版で再利用

### 🏠 統合マーケット概要機能
- **統合ホーム画面API** (`/home`): **7つのエンドポイントを統合**
  - 📰 金融ニュース（news/rss）
  - 📈 株価ランキング（rankings/stocks）
  - 🏢 セクターランキング（rankings/sectors）
  - 📊 主要指数（markets/indices）
  - 💱 為替レート（markets/currencies）
  - 🛢️ 商品価格（markets/commodities）
  - 🌍 市場開閉状況（markets/status）
- **ワンストップAPI**: 1回のリクエストで包括的なマーケット情報を取得

### 🔍 高速な株式検索機能
- 複数地域対応（US, JP, DE, CA, AU, GB, FR, IT, ES, KR, IN, HK, SG）
- リアルタイム価格情報付き
- ファジー検索対応

### 🚀 完全安定稼働
- **テスト成功率**: **100%** (21/21 エンドポイント)
- **エラーハンドリング**: 完全対応済み
- **データ変換**: 堅牢なDataFrame/JSON変換
- **NaN値処理**: 完全対応
- **日付処理**: JSON serializable

## 🏗️ アーキテクチャ

### 統一方式：Lambda関数直接使用
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   yfinance_     │    │   Docker        │    │   AWS Lambda    │
│   cli.py        │    │   Container     │    │   (本番環境)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ lambda_function │
                    │      .py        │
                    │  (共通関数群)    │
                    │  ✅ 100% 安定   │
                    └─────────────────┘
```

### 重複排除の仕組み
- **共通関数を`lambda_function.py`に集約**
  - `serialize_for_json()`: JSON変換（NaN値対応）
  - `safe_dataframe_to_*()`: 堅牢なDataFrame変換
  - `format_currency()`: 通貨フォーマット
  - `get_execution_info()`: 実行環境情報
  - `validate_ticker_parameter()`: パラメータバリデーション
- **各要素専用関数の再利用**
  - 10個の個別API関数を統合版で再利用
  - 重複コードを完全排除
  - 保守性と一貫性を確保

## 🚀 実行方法

### 1. ローカル実行
```bash
# CLIツール実行（統合版）
python yfinance_cli.py tickerDetail AAPL --period 1mo

# CLIツール実行（個別要素）
python yfinance_cli.py basic AAPL
python yfinance_cli.py price AAPL
python yfinance_cli.py history AAPL --period 1y
python yfinance_cli.py financials AAPL
python yfinance_cli.py analysts AAPL
python yfinance_cli.py holders AAPL
python yfinance_cli.py events AAPL
python yfinance_cli.py news AAPL
python yfinance_cli.py options AAPL
python yfinance_cli.py sustainability AAPL

# マーケット情報
python yfinance_cli.py home
python yfinance_cli.py news_rss --limit 10
python yfinance_cli.py rankings_stocks --type gainers --market sp500 --limit 10
python yfinance_cli.py rankings_sectors --limit 10
python yfinance_cli.py rankings_crypto --sort change --limit 10
python yfinance_cli.py markets_indices
python yfinance_cli.py markets_currencies
python yfinance_cli.py markets_commodities
python yfinance_cli.py markets_status

# 検索機能
python yfinance_cli.py search apple --region US
```

### 2. Docker実行

#### 🧪 完全テスト実行
```bash
# 全エンドポイントの一括テスト（推奨）
bash docker_local_fulltest.sh

# 結果: 21/21 SUCCESS（100%）
```

#### 個別実行
```bash
# 統合版
docker-compose run --rm --entrypoint="" yfinance-local python yfinance_cli.py tickerDetail AAPL

# 個別要素
docker-compose run --rm --entrypoint="" yfinance-local python yfinance_cli.py basic AAPL
docker-compose run --rm --entrypoint="" yfinance-local python yfinance_cli.py price AAPL
docker-compose run --rm --entrypoint="" yfinance-local python yfinance_cli.py financials AAPL

# マーケット情報
docker-compose run --rm --entrypoint="" yfinance-local python yfinance_cli.py home
docker-compose run --rm --entrypoint="" yfinance-local python yfinance_cli.py rankings_stocks --type gainers
```

#### 🎯 AWS Lambda シミュレーター
```bash
# SAM CLI使用のLambdaシミュレーター
bash test_lambda_simulator.sh
```

### 3. AWS Lambda デプロイ
```bash
# AWS SAMでビルド & デプロイ
sam build
sam deploy --guided

# または従来のスクリプト
bash deploy.sh
bash cleanup_and_deploy.sh
```

### 4. API Gateway経由でアクセス
```bash
# 統合版
curl "https://your-api-gateway-url/prod/tickerDetail?ticker=AAPL&period=1mo"

# 個別要素
curl "https://your-api-gateway-url/prod/ticker/basic?ticker=AAPL"
curl "https://your-api-gateway-url/prod/ticker/price?ticker=AAPL"
curl "https://your-api-gateway-url/prod/ticker/financials?ticker=AAPL"

# マーケット情報
curl "https://your-api-gateway-url/prod/home"
curl "https://your-api-gateway-url/prod/news/rss?limit=10"
curl "https://your-api-gateway-url/prod/rankings/stocks?type=gainers&market=sp500&limit=10"
curl "https://your-api-gateway-url/prod/markets/indices"
```

## 📁 ファイル構成

```
YFinanceDocker/
├── lambda_function.py          # ✅ メインLambda関数（100%安定）
├── yfinance_cli.py             # ✅ CLIツール（全機能対応）
├── test_all_endpoints_direct.py  # ✅ 直接テストスクリプト
├── docker_local_fulltest.sh    # ✅ 一括テストスクリプト
├── test_lambda_simulator.sh    # ✅ Lambdaシミュレーターテスト
├── docker-compose.yml          # ✅ Docker設定（Local + Lambda-sim）
├── Dockerfile                  # ✅ Lambda用Docker設定
├── template.yaml               # ✅ CloudFormationテンプレート
├── requirements.txt            # ✅ Python依存関係
├── deploy.sh                   # ✅ デプロイスクリプト
├── cleanup_and_deploy.sh       # ✅ クリーンアップ&デプロイ
└── README.md                   # ✅ このファイル（最新版）

# 🗑️ 削除済みファイル（重複排除）
# - yfinance_sample.py
# - local_test.py  
# - yfinance_search.py
# - test_search_with_price.py
# - swagger_generator_advanced.py
# - update_api_url.sh
# - yfinance.sh
```

## 🔧 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `EXECUTION_MODE` | 実行モード（LOCAL/DOCKER/LAMBDA） | `LOCAL` |

## 🔌 API エンドポイント一覧

### 1. 🔍 検索 API
- **エンドポイント**: `/search`
- **パラメータ**: `q` (検索クエリ), `region` (地域)
- **例**: `GET /search?q=apple&region=US`

### 2. 📊 包括的情報 API（統合版）
- **エンドポイント**: `/tickerDetail`
- **パラメータ**: `ticker` (必須), `period` (履歴期間)
- **例**: `GET /tickerDetail?ticker=AAPL&period=1y`
- **説明**: 全ての要素を統合して返す（個別関数を内部で呼び出し）

### 3. 🧩 個別要素 API

| エンドポイント | 説明 | 例 |
|---------------|------|---|
| `/ticker/basic` | 基本情報 | `GET /ticker/basic?ticker=AAPL` |
| `/ticker/price` | 株価情報 | `GET /ticker/price?ticker=AAPL` |
| `/ticker/history` | 履歴情報 | `GET /ticker/history?ticker=AAPL&period=1y` |
| `/ticker/financials` | 財務情報 | `GET /ticker/financials?ticker=AAPL` |
| `/ticker/analysts` | アナリスト情報 | `GET /ticker/analysts?ticker=AAPL` |
| `/ticker/holders` | 株主情報 | `GET /ticker/holders?ticker=AAPL` |
| `/ticker/events` | イベント情報 | `GET /ticker/events?ticker=AAPL` |
| `/ticker/news` | ニュース情報 | `GET /ticker/news?ticker=AAPL` |
| `/ticker/options` | オプション情報 | `GET /ticker/options?ticker=AAPL` |
| `/ticker/sustainability` | ESG情報 | `GET /ticker/sustainability?ticker=AAPL` |

### 4. 🏠 統合マーケット概要 API（✨NEW!）

| エンドポイント | 説明 | 統合された機能 |
|---------------|------|-------------|
| `/home` | **統合ホーム画面** | 📰 ニュース + 📈 株価ランキング + 🏢 セクター + 📊 指数 + 💱 為替 + 🛢️ 商品 + 🌍 市場状況 |

**特徴**: 7つのエンドポイントを1つに統合！ワンストップでマーケット全体を把握

### 5. 📰 ニュース API

| エンドポイント | 説明 | 例 |
|---------------|------|---|
| `/news/rss` | 金融ニュースRSS | `GET /news/rss?limit=10` |

**📰 ニュースソース:**
- **Yahoo Finance RSS**: `https://finance.yahoo.com/rss/2.0` (一般金融ニュース)
- **MarketWatch Top Stories**: `https://www.marketwatch.com/rss/topstories` (市場ニュース・画像付き)

### 6. 📈 ランキング API

| エンドポイント | 説明 | 例 |
|---------------|------|---|
| `/rankings/stocks` | 株価ランキング | `GET /rankings/stocks?type=gainers&market=sp500&limit=10` |
| `/rankings/sectors` | セクターランキング | `GET /rankings/sectors?limit=10` |
| `/rankings/crypto` | 暗号通貨ランキング | `GET /rankings/crypto?sort=change&limit=10` |

### 7. 🌍 マーケット情報 API

| エンドポイント | 説明 | 例 |
|---------------|------|---|
| `/markets/indices` | 主要指数 | `GET /markets/indices` |
| `/markets/currencies` | 為替レート | `GET /markets/currencies` |
| `/markets/commodities` | 商品価格 | `GET /markets/commodities` |
| `/markets/status` | 市場開閉状況 | `GET /markets/status` |

## 📊 出力例

### 🔍 検索結果
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
      "current_price": 213.45,
      "currency": "USD",
      "price_change": 2.15,
      "price_change_percent": 1.02,
      "price_change_direction": "up"
    }
  ],
  "execution_info": {
    "mode": "DOCKER",
    "timestamp": "2025-07-24T14:49:56",
    "server": "lambda"
  }
}
```

### 🏠 統合ホーム画面情報（✨NEW!）
```json
{
  "news_rss": {
    "status": "success",
    "data": [
      {
        "title": "S&P 500 scores 5th straight record high",
        "summary": "Wall Street's so-called fear gauge dropped...",
        "url": "https://www.marketwatch.com/story/...",
        "source": "MarketWatch Top Stories",
        "image_url": "https://images.mktw.net/im-28297331",
        "published_at": "2025-07-25T22:34:00"
      }
    ],
    "metadata": {
      "total_sources": 2,
      "sources_used": ["Yahoo Finance", "MarketWatch Top Stories"]
    }
  },
  "rankings_stocks": {
    "gainers": {
      "status": "success",
      "data": [
        {
          "symbol": "NVDA",
          "name": "NVIDIA Corporation",
          "current_price": 850.25,
          "price_change_percent": 3.68
        }
      ]
    },
    "losers": { ... }
  },
  "markets_indices": {
    "status": "success",
    "data": [
      {
        "index": "S&P 500",
        "symbol": "^GSPC",
        "current_price": 5892.35,
        "price_change_percent": 0.26
      }
    ]
  },
  "markets_currencies": { ... },
  "markets_commodities": { ... },
  "markets_status": { ... },
  "endpoints_integrated": [
    "news/rss", "rankings/stocks", "rankings/sectors",
    "markets/indices", "markets/currencies", 
    "markets/commodities", "markets/status"
  ]
}
```

### 📊 包括的情報（統合版）
```json
{
  "ticker": "AAPL",
  "period": "1mo",
  "info": {
    "longName": "Apple Inc.",
    "industry": "Consumer Electronics",
    "sector": "Technology",
    "logo_url": "https://logo.clearbit.com/apple.com"
  },
  "price": {
    "current_price": 213.45,
    "currency": "USD",
    "price_change": 2.15,
    "price_change_percent": 1.02
  },
  "financials": {
    "income_statement": {
      "Total Revenue": {
        "2024-09-30 00:00:00": 391035000000.0,
        "2023-09-30 00:00:00": 383285000000.0
      }
    },
    "earnings": {
      "trailingEps": 6.42,
      "forwardEps": 8.31,
      "trailingPE": 33.37,
      "forwardPE": 25.78
    }
  },
  "execution_info": {
    "mode": "DOCKER",
    "timestamp": "2025-07-24T14:49:56",
    "server": "lambda"
  }
}
```

### 📈 ランキング情報（画像付き）
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
    "last_updated": "2025-07-24T14:30:00Z"
  }
}
```

### ⚠️ 部分エラーの例（統合版）
```json
{
  "ticker": "AAPL",
  "info": {
    "longName": "Apple Inc.",
    "industry": "Consumer Electronics"
  },
  "price": {
    "current_price": 213.45,
    "currency": "USD"
  },
  "partial_errors": [
    "財務情報: データが利用できません",
    "オプション情報: オプションが利用できません"
  ],
  "execution_info": {
    "mode": "DOCKER",
    "timestamp": "2025-07-24T14:49:56",
    "server": "lambda"
  }
}
```

## 🎯 統一の利点

### 1. 🚀 開発効率の向上
- **同じ関数を使用**: 3つの環境で同じロジック
- **デバッグの簡素化**: 問題の特定が容易
- **テストの統一**: 同じテストケースで全環境を検証

### 2. 🛠️ 保守性の向上
- **重複コードの完全排除**: 共通関数を一箇所で管理
- **一貫性の確保**: 出力形式が完全に統一
- **変更の簡素化**: 修正は`lambda_function.py`のみ

### 3. 🔒 信頼性の向上
- **同じエラーハンドリング**: 全環境で統一されたエラー処理
- **データ品質の保証**: 同じデータ取得ロジック
- **実行環境情報の自動付与**: トレーサビリティの確保

## 🧪 テスト結果

### ✅ 完全安定稼働達成
```bash
============================================================
📊 テスト結果サマリー
============================================================
🔢 総テスト数: 21
✅ 成功: 21
❌ 失敗: 0
📈 成功率: 100.0%
============================================================
```

### 🔧 解消されたエラー
1. ✅ `The truth value of an array with more than one element is ambiguous`
2. ✅ `Object of type date is not JSON serializable`
3. ✅ `cannot convert float NaN to integer`
4. ✅ `'dict' object has no attribute 'empty'`
5. ✅ 古い`yfinance`メソッド使用問題
6. ✅ `pd.isna()` with リスト/配列エラー

### 📊 個別エンドポイントテスト結果
| エンドポイント | ステータス | 詳細 |
|---------------|-----------|------|
| search | ✅ SUCCESS | 検索機能正常 |
| tickerDetail | ✅ SUCCESS | 統合版API正常 |
| basic | ✅ SUCCESS | 基本情報取得正常 |
| price | ✅ SUCCESS | 株価情報取得正常 |
| history | ✅ SUCCESS | 履歴情報取得正常 |
| financials | ✅ SUCCESS | 財務情報取得正常 |
| analysts | ✅ SUCCESS | アナリスト情報取得正常 |
| holders | ✅ SUCCESS | 株主情報取得正常 |
| events | ✅ SUCCESS | イベント情報取得正常 |
| news | ✅ SUCCESS | ニュース情報取得正常 |
| options | ✅ SUCCESS | オプション情報取得正常 |
| sustainability | ✅ SUCCESS | ESG情報取得正常 |
| home | ✅ SUCCESS | ホーム画面情報取得正常 |
| news_rss | ✅ SUCCESS | RSSニュース取得正常 |
| rankings_stocks | ✅ SUCCESS | 株価ランキング取得正常 |
| rankings_sectors | ✅ SUCCESS | セクターランキング取得正常 |
| rankings_crypto | ✅ SUCCESS | 暗号通貨ランキング取得正常 |
| markets_indices | ✅ SUCCESS | 主要指数取得正常 |
| markets_currencies | ✅ SUCCESS | 為替レート取得正常 |
| markets_commodities | ✅ SUCCESS | 商品価格取得正常 |
| markets_status | ✅ SUCCESS | 市場開閉状況取得正常 |

## 🛠️ 技術スタック

- **Python 3.12**
- **YFinance**: 株式データ取得
- **Pandas/NumPy**: データ処理
- **AWS Lambda**: サーバーレス実行環境
- **Docker**: コンテナ化
- **AWS API Gateway**: RESTful API
- **AWS SAM CLI**: Lambda シミュレーター
- **CloudFormation**: インフラストラクチャ管理
- **Matplotlib**: チャート生成
- **Feedparser**: RSSニュース取得
  - Yahoo Finance RSS (https://finance.yahoo.com/rss/2.0)
  - MarketWatch RSS (https://www.marketwatch.com/rss/topstories)

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

---

## 🎉 最新アップデート

### ✅ 2025年7月24日 - 完全安定版リリース
- **100%テスト成功**: 21/21エンドポイントが正常動作
- **エラーハンドリング完全対応**: 全データ変換エラーを解消
- **堅牢なJSON変換**: NaN値、日付、DataFrame処理を完全対応
- **個別APIエンドポイント**: 効率的なデータ取得に対応
- **マーケット概要機能**: ランキング、ニュース、市場情報を追加
- **AWS Lambda シミュレーター**: SAM CLI対応
- **重複コード完全排除**: 保守性を大幅向上 