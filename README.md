# YFinance 環境

YFinanceを使用して株式データを取得・分析するための環境です。

## 概要

このプロジェクトには以下の機能があります：
1. **CLIツール** - コマンドラインから株式データを取得
2. **AWS API** - Lambda + API Gateway による REST API

## セットアップ

### 1. 仮想環境の有効化
```bash
source venv/bin/activate
```

### 2. 依存関係のインストール
```bash
pip install -r requirements.txt
```

## CLIツールの使用方法

### サンプルプログラムの実行
```bash
python yfinance_sample.py
```

### CLIツールの使用

#### 基本的な使用方法
```bash
python yfinance_cli.py AAPL
```

#### オプション付きの使用方法
```bash
# 現在価格のみ表示
python yfinance_cli.py AAPL --price

# 詳細情報を表示
python yfinance_cli.py AAPL --info

# 株価履歴を表示（1ヶ月分）
python yfinance_cli.py AAPL --history

# 株価履歴を表示（1年分）
python yfinance_cli.py AAPL --history --period 1y

# 全ての情報を表示
python yfinance_cli.py AAPL --price --info --history

# JSON形式で出力
python yfinance_cli.py AAPL --price --info --json
```

## AWS API の構築・デプロイ

### 前提条件

AWS SAM CLI と AWS CLI が必要です：

```bash
# AWS CLI のインストール
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# AWS SAM CLI のインストール
pip install aws-sam-cli

# AWS認証情報の設定
aws configure
```

### ローカルテスト

API機能をローカルでテストできます：

```bash
# 基本的なAPIテスト
python test_api.py

# 特定の機能のみテスト
python test_api.py price
python test_api.py info
python test_api.py history
python test_api.py lambda

# ローカルHTTPサーバーでテスト
python local_test.py
# ブラウザで http://localhost:8000 にアクセス
```

### AWS へのデプロイ

```bash
# デプロイ実行
./deploy.sh
```

デプロイが成功すると、API Gateway のURLが表示されます：

```
API Gateway URL: https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/

=== API エンドポイント ===
株価取得: GET https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/price/{ticker}
詳細情報: GET https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/info/{ticker}
履歴データ: GET https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/history/{ticker}?period=1mo
```

### API の使用例

```bash
# 株価取得
curl "https://your-api-url/prod/price/AAPL"

# 詳細情報取得
curl "https://your-api-url/prod/info/MSFT"

# 履歴データ取得
curl "https://your-api-url/prod/history/GOOGL?period=1y"
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
   # Default region name: [リージョン名を入力（例：us-east-1）]
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
   - Lambda関数のデプロイ
   - API Gatewayの設定

3. デプロイが成功すると、以下のような出力が表示されます：
   ```
   API Gateway URL: https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/
   
   === API エンドポイント ===
   株価取得: GET https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/price/{ticker}
   詳細情報: GET https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/info/{ticker}
   履歴データ: GET https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/history/{ticker}?period=1mo
   ```

### 6. デプロイ後の確認

1. エンドポイントのテスト：
   ```bash
   # 株価取得
   curl "https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/price/AAPL"
   
   # 詳細情報取得
   curl "https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/info/MSFT"
   
   # 履歴データ取得
   curl "https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/history/GOOGL?period=1y"
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

- `GET /price/{ticker}` - 現在の株価取得
- `GET /info/{ticker}` - 株式の詳細情報取得
- `GET /history/{ticker}?period={period}` - 株価履歴取得

### 対応するティッカーシンボル

- **アメリカ株**: AAPL, MSFT, GOOGL, TSLA, NVDA など
- **日本株**: 7203.T (トヨタ), 9984.T (ソフトバンク), 6501.T (日立) など
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

## 注意事項

- インターネット接続が必要です
- Yahoo FinanceのAPIを使用しているため、利用制限がある場合があります
- 日本株式の場合は、ティッカーシンボルの後に`.T`を付けてください

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