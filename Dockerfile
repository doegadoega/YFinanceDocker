FROM python:3.10-slim

WORKDIR /app

# 必要なパッケージをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY yfinance_sample.py .
COPY yfinance_cli.py .
COPY yfinance_search.py .

# 実行権限を付与
RUN chmod +x yfinance_sample.py yfinance_cli.py yfinance_search.py

# コンテナ起動時のデフォルトコマンド
ENTRYPOINT ["python"]
CMD ["yfinance_cli.py", "--help"] 