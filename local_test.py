#!/usr/bin/env python3
"""
ローカルテスト用シンプルなHTTPサーバー
Lambda関数の動作をローカルで確認するため（Lambda関数直接使用で完全統一）
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import os
from datetime import datetime
from lambda_function import (
    get_stock_info_api, 
    search_stocks_api,
    get_execution_info
)

# 実行モード設定
EXECUTION_MODE = os.getenv('EXECUTION_MODE', 'LOCAL')

class YFinanceHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """GETリクエストの処理"""
        try:
            # URLを解析
            parsed_url = urllib.parse.urlparse(self.path)
            path = parsed_url.path
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            # CORS ヘッダーを設定
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            
            # パスによる処理分岐
            if path.startswith('/search'):
                # 検索API（Lambda関数直接使用）
                query = query_params.get('q', [''])[0]
                region = query_params.get('region', ['US'])[0]
                if not query:
                    self._send_error_response(400, '検索クエリが必要です')
                    return
                
                # Lambda関数を直接呼び出し
                result = search_stocks_api(query, {'region': region})
                
                # 実行環境情報を追加
                if not result.get('error'):
                    result['execution_info'] = get_execution_info(EXECUTION_MODE)
                
                self._send_json_response(result)
                
            elif path.startswith('/tickerDetail'):
                # 包括的情報API（Lambda関数直接使用）
                ticker = query_params.get('ticker', [''])[0].upper()
                period = query_params.get('period', ['1mo'])[0]
                if not ticker:
                    self._send_error_response(400, 'ティッカーシンボルが必要です')
                    return
                
                # Lambda関数を直接呼び出し
                result = get_stock_info_api(ticker, period)
                
                # 実行環境情報を追加
                if not result.get('error'):
                    result['execution_info'] = get_execution_info(EXECUTION_MODE)
                
                self._send_json_response(result)
                
            elif path == '/':
                self._send_html_response()
                
            else:
                self._send_error_response(404, 'リソースが見つかりません')
                
        except Exception as e:
            self._send_error_response(500, f'サーバーエラー: {str(e)}')
    
    def do_OPTIONS(self):
        """OPTIONS リクエストの処理（CORS プリフライト）"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _send_json_response(self, data):
        """JSON レスポンスを送信（Lambda関数直接使用で完全統一）"""
        if data.get('error'):
            status_code = 500
        else:
            status_code = 200
            
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response_body = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response_body.encode('utf-8'))
    
    def _send_error_response(self, status_code, message):
        """エラーレスポンスを送信（Lambda関数直接使用で完全統一）"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        error_data = {
            'error': message,
            'execution_info': get_execution_info(EXECUTION_MODE)
        }
        response_body = json.dumps(error_data, ensure_ascii=False, indent=2)
        self.wfile.write(response_body.encode('utf-8'))
    
    def _send_html_response(self):
        """HTMLテストページを送信"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YFinance API ローカルテスト（Lambda関数直接使用版）</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        input, button, select {{ padding: 10px; margin: 5px; }}
        .result {{ background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px; }}
        pre {{ white-space: pre-wrap; }}
        .info {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .success {{ background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>YFinance API ローカルテスト（Lambda関数直接使用版）</h1>
        
        <div class="info">
            <h3>実行環境情報</h3>
            <p><strong>モード:</strong> {EXECUTION_MODE}</p>
            <p><strong>API形式:</strong> Lambda関数直接使用</p>
            <p><strong>エンドポイント:</strong> ローカルサーバー</p>
        </div>
        
        <div class="success">
            <h3>✅ 完全統一完了</h3>
            <p>Lambda関数を直接使用することで、出力形式が完全に統一されました。</p>
            <p>• 同じ関数から呼び出し</p>
            <p>• 同じデータ構造</p>
            <p>• 同じエラーハンドリング</p>
            <p>• 重複コードの排除</p>
        </div>
        
        <div>
            <h3>銘柄検索テスト（Lambda関数直接使用）</h3>
            <input type="text" id="searchQuery" placeholder="検索キーワード (例: apple)" value="apple">
            <select id="searchRegion">
                <option value="US" selected>US</option>
                <option value="JP">JP</option>
            </select>
            <button onclick="testSearch()">検索実行</button>
        </div>
        
        <div>
            <h3>包括的情報テスト（Lambda関数直接使用）</h3>
            <input type="text" id="infoTicker" placeholder="ティッカー (例: AAPL)" value="AAPL">
            <select id="infoPeriod">
                <option value="1d">1日</option>
                <option value="5d">5日</option>
                <option value="1mo" selected>1ヶ月</option>
                <option value="1y">1年</option>
            </select>
            <button onclick="testInfo()">情報取得</button>
        </div>
        
        <div class="result">
            <h3>結果:</h3>
            <pre id="result">ここに結果が表示されます</pre>
        </div>
    </div>

    <script>
        async function testSearch() {{
            const query = document.getElementById('searchQuery').value;
            const region = document.getElementById('searchRegion').value;
            try {{
                const response = await fetch(`/search?q=${{query}}&region=${{region}}`);
                const data = await response.json();
                document.getElementById('result').textContent = JSON.stringify(data, null, 2);
            }} catch (error) {{
                document.getElementById('result').textContent = 'エラー: ' + error.message;
            }}
        }}

        async function testInfo() {{
            const ticker = document.getElementById('infoTicker').value;
            const period = document.getElementById('infoPeriod').value;
            try {{
                const response = await fetch(`/tickerDetail?ticker=${{ticker}}&period=${{period}}`);
                const data = await response.json();
                document.getElementById('result').textContent = JSON.stringify(data, null, 2);
            }} catch (error) {{
                document.getElementById('result').textContent = 'エラー: ' + error.message;
            }}
        }}
    </script>
</body>
</html>
        """
        self.wfile.write(html_content.encode('utf-8'))


def main():
    port = 8000
    server_address = ('', port)
    httpd = HTTPServer(server_address, YFinanceHandler)
    
    print(f"YFinance API ローカルテストサーバーを開始しました（Lambda関数直接使用版）")
    print(f"実行モード: {EXECUTION_MODE}")
    print(f"統一方式: Lambda関数を直接使用")
    print(f"重複排除: 共通関数をlambda_function.pyからインポート")
    print(f"URL: http://localhost:{port}")
    print("Ctrl+C で停止")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを停止しています...")
        httpd.shutdown()


if __name__ == "__main__":
    main()