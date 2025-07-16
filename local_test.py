#!/usr/bin/env python3
"""
ローカルテスト用シンプルなHTTPサーバー
Lambda関数の動作をローカルで確認するため
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
from lambda_function import get_stock_price_api, get_stock_info_api, get_stock_history_api


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
            if path.startswith('/price/'):
                ticker = path.split('/price/')[-1].upper()
                result = get_stock_price_api(ticker)
                self._send_json_response(result)
                
            elif path.startswith('/info/'):
                ticker = path.split('/info/')[-1].upper()
                result = get_stock_info_api(ticker)
                self._send_json_response(result)
                
            elif path.startswith('/history/'):
                ticker = path.split('/history/')[-1].upper()
                period = query_params.get('period', ['1mo'])[0]
                result = get_stock_history_api(ticker, period)
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
        """JSON レスポンスを送信"""
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
        """エラーレスポンスを送信"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        error_data = {'error': message}
        response_body = json.dumps(error_data, ensure_ascii=False, indent=2)
        self.wfile.write(response_body.encode('utf-8'))
    
    def _send_html_response(self):
        """HTMLテストページを送信"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html_content = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YFinance API テスト</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        input, button { padding: 10px; margin: 5px; }
        .result { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px; }
        pre { white-space: pre-wrap; }
    </style>
</head>
<body>
    <div class="container">
        <h1>YFinance API ローカルテスト</h1>
        
        <div>
            <h3>株価取得テスト</h3>
            <input type="text" id="priceTicker" placeholder="ティッカー (例: AAPL)" value="AAPL">
            <button onclick="testPrice()">株価取得</button>
        </div>
        
        <div>
            <h3>詳細情報テスト</h3>
            <input type="text" id="infoTicker" placeholder="ティッカー (例: MSFT)" value="MSFT">
            <button onclick="testInfo()">詳細情報取得</button>
        </div>
        
        <div>
            <h3>履歴データテスト</h3>
            <input type="text" id="historyTicker" placeholder="ティッカー (例: GOOGL)" value="GOOGL">
            <select id="historyPeriod">
                <option value="1d">1日</option>
                <option value="5d">5日</option>
                <option value="1mo" selected>1ヶ月</option>
                <option value="1y">1年</option>
            </select>
            <button onclick="testHistory()">履歴取得</button>
        </div>
        
        <div class="result">
            <h3>結果:</h3>
            <pre id="result">ここに結果が表示されます</pre>
        </div>
    </div>

    <script>
        async function testPrice() {
            const ticker = document.getElementById('priceTicker').value;
            try {
                const response = await fetch(`/price/${ticker}`);
                const data = await response.json();
                document.getElementById('result').textContent = JSON.stringify(data, null, 2);
            } catch (error) {
                document.getElementById('result').textContent = 'エラー: ' + error.message;
            }
        }

        async function testInfo() {
            const ticker = document.getElementById('infoTicker').value;
            try {
                const response = await fetch(`/info/${ticker}`);
                const data = await response.json();
                document.getElementById('result').textContent = JSON.stringify(data, null, 2);
            } catch (error) {
                document.getElementById('result').textContent = 'エラー: ' + error.message;
            }
        }

        async function testHistory() {
            const ticker = document.getElementById('historyTicker').value;
            const period = document.getElementById('historyPeriod').value;
            try {
                const response = await fetch(`/history/${ticker}?period=${period}`);
                const data = await response.json();
                document.getElementById('result').textContent = JSON.stringify(data, null, 2);
            } catch (error) {
                document.getElementById('result').textContent = 'エラー: ' + error.message;
            }
        }
    </script>
</body>
</html>
        """
        self.wfile.write(html_content.encode('utf-8'))


def main():
    port = 8000
    server_address = ('', port)
    httpd = HTTPServer(server_address, YFinanceHandler)
    
    print(f"YFinance API ローカルテストサーバーを開始しました")
    print(f"URL: http://localhost:{port}")
    print("Ctrl+C で停止")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを停止しています...")
        httpd.shutdown()


if __name__ == "__main__":
    main()