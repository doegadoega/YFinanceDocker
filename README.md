# YFinance 環境

YFinanceを使用して株式データを取得・分析するための環境です。

## セットアップ

### 1. 仮想環境の有効化
```bash
source venv/bin/activate
```

### 2. 依存関係のインストール
```bash
pip install -r requirements.txt
```

## 使用方法

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

### 銘柄検索ツールの使用

```bash
# 米国市場で「apple」を検索
python yfinance_search.py apple

# 日本市場で検索
python yfinance_search.py toyota --region JP

# 検索結果の件数を指定
python yfinance_search.py bank --limit 20

# JSON形式で出力
python yfinance_search.py apple --json
```

## Docker を使った実行

Docker を使用して環境を構築せずに実行することもできます。

### Docker ビルド
```bash
docker build -t yfinance .
```

### Docker での実行
```bash
# ヘルプを表示
docker run --rm yfinance yfinance_cli.py --help

# アップルの株価を表示
docker run --rm yfinance yfinance_cli.py AAPL --price

# 詳細情報を表示
docker run --rm yfinance yfinance_cli.py AAPL --info

# 株価履歴を表示
docker run --rm yfinance yfinance_cli.py AAPL --history --period 1y

# JSON形式で出力
docker run --rm yfinance yfinance_cli.py AAPL --price --info --json

# 銘柄検索
docker run --rm yfinance yfinance_search.py apple

# サンプルプログラムを実行
docker run --rm yfinance yfinance_sample.py
```

### Docker Compose での実行
```bash
# デフォルト（ヘルプ表示）
docker-compose up --build

# コマンドを指定して実行
docker-compose run --rm yfinance yfinance_cli.py AAPL --price --info
```

### 便利なシェルスクリプト

より簡単に実行するためのシェルスクリプトが用意されています：

```bash
# 使い方を表示
./yfinance.sh help

# 株価を表示
./yfinance.sh price AAPL

# 詳細情報を表示
./yfinance.sh info AAPL

# 株価履歴を表示
./yfinance.sh history AAPL --period 1y

# 全情報を表示
./yfinance.sh all AAPL

# JSON形式で出力
./yfinance.sh all AAPL --json
./yfinance.sh info AAPL --json

# 銘柄検索
./yfinance.sh search apple
./yfinance.sh search toyota --region JP
./yfinance.sh search apple --json
```

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