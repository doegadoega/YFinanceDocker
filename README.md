# YFinance Docker プロジェクト

YFinanceを使用した株式データ取得システムを、Lambda、Docker、ローカル実行の3つのパターンで統一された出力形式で提供します。

## 🎯 プロジェクトの特徴

### ✅ 完全統一された出力形式
- **Lambda関数を直接使用**することで、3つの実行環境で完全に同じ出力
- 同じ関数から呼び出し、同じデータ構造、同じエラーハンドリング
- 重複コードの排除により保守性が大幅向上

### 📊 包括的な金融データ（17種類）
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
- その他詳細データ

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
- **他のファイルから直接インポート**
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
python yfinance_cli.py info AAPL 1mo
python yfinance_cli.py basic AAPL
```

### 2. Docker実行

#### ローカルテスト用
```bash
# ローカルテスト用Dockerコンテナビルド
docker-compose build yfinance-local

# 基本的なサンプル実行
docker-compose run --rm yfinance-local python yfinance_sample.py

# CLIツール実行
docker-compose run --rm yfinance-local python yfinance_cli.py AAPL --price --info

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

# API Gateway経由でアクセス
curl "https://your-api-gateway-url/prod/search?q=apple&region=US"
curl "https://your-api-gateway-url/prod/tickerDetail?ticker=AAPL&period=1mo"
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

### 包括的情報
```json
{
  "ticker": "AAPL",
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