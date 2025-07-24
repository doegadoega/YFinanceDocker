# YFinance Docker コマンド一覧

## 基本コマンド

### イメージのビルド
```bash
docker build -t yfinance .
```

### ヘルプを表示
```bash
docker run --rm yfinance yfinance_cli.py --help
```

## 株価情報の取得

### 現在の株価を取得
```bash
# 米国株（例：アップル）
docker run --rm yfinance yfinance_cli.py AAPL --price

# 日本株（例：トヨタ自動車）
docker run --rm yfinance yfinance_cli.py 7203.T --price
```

### 詳細情報を表示
```bash
# 米国株（例：アップル）
docker run --rm yfinance yfinance_cli.py AAPL --info

# 日本株（例：トヨタ自動車）
docker run --rm yfinance yfinance_cli.py 7203.T --info
```

### 株価履歴を表示
```bash
# 1ヶ月分の履歴（デフォルト）
docker run --rm yfinance yfinance_cli.py AAPL --history

# 期間を指定（例：1年分）
docker run --rm yfinance yfinance_cli.py AAPL --history --period 1y

# 日本株の履歴（例：3ヶ月分）
docker run --rm yfinance yfinance_cli.py 7203.T --history --period 3mo
```

### 複数の情報を一度に表示
```bash
# 価格と詳細情報
docker run --rm yfinance yfinance_cli.py AAPL --price --info

# 全ての情報（価格・詳細・履歴）
docker run --rm yfinance yfinance_cli.py AAPL --price --info --history
```

### JSON形式で出力
```bash
# 価格情報をJSON形式で出力
docker run --rm yfinance yfinance_cli.py AAPL --price --json

# 詳細情報をJSON形式で出力
docker run --rm yfinance yfinance_cli.py AAPL --info --json

# 株価履歴をJSON形式で出力
docker run --rm yfinance yfinance_cli.py AAPL --history --json

# 全ての情報をJSON形式で出力
docker run --rm yfinance yfinance_cli.py AAPL --price --info --history --json
```

## 銘柄検索

### キーワードで銘柄を検索
```bash
# 米国市場で「apple」を検索
docker run --rm yfinance yfinance_search.py apple

# 日本市場で「トヨタ」を検索
docker run --rm yfinance yfinance_search.py トヨタ --region JP

# 検索結果の件数を指定
docker run --rm yfinance yfinance_search.py bank --limit 20
```

### 検索結果をJSON形式で出力
```bash
# 米国市場の検索結果をJSON形式で出力
docker run --rm yfinance yfinance_search.py apple --json

# 日本市場の検索結果をJSON形式で出力
docker run --rm yfinance yfinance_search.py toyota --region JP --json
```

## サンプルプログラムの実行
```bash
docker run --rm yfinance yfinance_sample.py
```

## Docker Compose を使った実行

### デフォルト（ヘルプ表示）
```bash
docker-compose up
```

### 特定のコマンドを実行
```bash
# 価格と詳細情報を表示
docker-compose run --rm yfinance yfinance_cli.py AAPL --price --info

# 株価履歴を表示
docker-compose run --rm yfinance yfinance_cli.py AAPL --history --period 1y

# JSON形式で出力
docker-compose run --rm yfinance yfinance_cli.py AAPL --price --info --json

# 銘柄検索
docker-compose run --rm yfinance yfinance_search.py apple --region US

# サンプルプログラムを実行
docker-compose run --rm yfinance yfinance_sample.py
```

## 統一されたCLIツールを使った実行

```bash
# 銘柄検索
python yfinance_cli.py search apple
python yfinance_cli.py search toyota --region JP

# 包括的情報取得
python yfinance_cli.py info AAPL
python yfinance_cli.py info 7203.T --period 1mo

# 基本情報表示
python yfinance_cli.py basic AAPL

# JSON形式で出力
python yfinance_cli.py info AAPL --json
```

## よく使う銘柄のティッカーシンボル

### 米国株
```
AAPL  - Apple Inc.
MSFT  - Microsoft Corporation
GOOGL - Alphabet Inc.
AMZN  - Amazon.com Inc.
TSLA  - Tesla Inc.
META  - Meta Platforms Inc.
NVDA  - NVIDIA Corporation
JPM   - JPMorgan Chase & Co.
V     - Visa Inc.
WMT   - Walmart Inc.
```

### 日本株
```
7203.T - トヨタ自動車
9432.T - 日本電信電話
6758.T - ソニーグループ
9984.T - ソフトバンクグループ
6861.T - キーエンス
7974.T - 任天堂
6501.T - 日立製作所
8306.T - 三菱UFJフィナンシャル・グループ
9433.T - KDDI
4502.T - 武田薬品工業
```

### 指数
```
^N225  - 日経225
^DJI   - ダウ工業株30種平均
^GSPC  - S&P 500
^IXIC  - NASDAQ総合指数
```

### 為替
```
USDJPY=X - 米ドル/円
EURJPY=X - ユーロ/円
GBPJPY=X - 英ポンド/円
```

## トラブルシューティング

### イメージの再ビルド
```bash
docker build --no-cache -t yfinance .
```

### Docker Composeの再ビルド
```bash
docker-compose build --no-cache
```

### コンテナ内でシェルを実行
```bash
docker run --rm -it yfinance /bin/bash
``` 

# Docker運用コマンド例

## ローカルAPIテスト自動化スクリプト

```sh
docker-compose build yfinance-local

docker-compose up -d yfinance-local

# サーバー起動待ち（数秒）
sleep 5

# テスト結果保存ディレクトリ
testdir="./test/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$testdir"

# テストしたいエンドポイント一覧
declare -A endpoints=(
  [basic]="/ticker/basic?ticker=AAPL"
  [price]="/ticker/price?ticker=AAPL"
  [news]="/news/rss?limit=5"
  [rankings]="/rankings/stocks?type=gainers&market=sp500&limit=5"
  # 必要に応じて追加
)

for name in "${!endpoints[@]}"; do
  url="http://localhost:8000${endpoints[$name]}"
  echo "Testing $url"
  curl -s "$url" > "$testdir/${name}.json"
done

echo "テスト結果は $testdir に保存されました"

docker-compose down
```

## 注意点
- APIサーバーが8000番ポートで起動している必要あり（docker-compose.ymlでports: - "8000:8000" を有効化）
- 必要なエンドポイントは適宜追加・修正してください
- テスト結果は ./test/日付_時刻/ フォルダに保存されます 