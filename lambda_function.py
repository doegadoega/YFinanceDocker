import json
import yfinance as yf
from datetime import datetime, date
import traceback
import os
import pandas as pd
import numpy as np
from typing import Union, Dict, Any, Optional
import feedparser
import hashlib
import re
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
import base64
import hmac
import hashlib
import base64 as _b64

# ... 既存のimport文の下に追加 ...
BULLISH_THRESHOLD = 0.5
BEARISH_THRESHOLD = -0.5

# =====================
# 認証/ユーザー管理 追加
# =====================
import time
import json as _json
import boto3
from botocore.exceptions import ClientError


def _b64url_encode(data: bytes) -> str:
    return _b64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data_str: str) -> bytes:
    padding = '=' * (-len(data_str) % 4)
    return _b64.urlsafe_b64decode(data_str + padding)


def _jwt_sign(payload: dict, secret: str, expires_in_seconds: int = 3600) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {
        **payload,
        "iat": now,
        "exp": now + int(expires_in_seconds),
    }
    header_b64 = _b64url_encode(_json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = _b64url_encode(_json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    sig = hmac.new(secret.encode('utf-8'), signing_input, hashlib.sha256).digest()
    signature_b64 = _b64url_encode(sig)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def _get_json_body(event: Dict[str, Any]) -> Dict[str, Any]:
    body = event.get('body')
    if not body:
        return {}
    if event.get('isBase64Encoded'):
        try:
            body = base64.b64decode(body).decode('utf-8')
        except Exception:
            return {}
    try:
        return json.loads(body)
    except Exception:
        return {}


def _get_users_table():
    table_name = os.environ.get('USERS_TABLE', '')
    if not table_name:
        raise RuntimeError('USERS_TABLE is not configured')
    ddb = boto3.resource('dynamodb')
    return ddb.Table(table_name)


def _hash_password(password: str, salt: Optional[bytes] = None, iterations: int = 100_000) -> Dict[str, Any]:
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return {
        'algo': 'pbkdf2_sha256',
        'iter': iterations,
        'salt': base64.b64encode(salt).decode('ascii'),
        'hash': base64.b64encode(dk).decode('ascii'),
    }


def _verify_password(password: str, stored: Dict[str, Any]) -> bool:
    try:
        if stored.get('algo') != 'pbkdf2_sha256':
            return False
        iterations = int(stored.get('iter', 100_000))
        salt = base64.b64decode(stored['salt'])
        expected = base64.b64decode(stored['hash'])
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


def handle_auth_register(event: Dict[str, Any]) -> Dict[str, Any]:
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }
    data = _get_json_body(event)
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    name = (data.get('name') or '').strip()
    profile_in = data.get('profile') if isinstance(data.get('profile'), dict) else {}
    if not email or not password:
        return {'error': 'emailとpasswordは必須です'}
    table = _get_users_table()
    try:
        # 既存チェック
        res = table.get_item(Key={'email': email})
        if 'Item' in res:
            return {'error': 'このメールは既に登録されています'}
        pw = _hash_password(password)
        item = {
            'email': email,
            'password': pw,
            'name': name,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'profile': profile_in,
        }
        table.put_item(Item=item, ConditionExpression='attribute_not_exists(email)')
        return {'status': 'ok'}
    except ClientError as e:
        return {'error': f'DynamoDBエラー: {e.response.get("Error", {}).get("Message", str(e))}'}
    except Exception as e:
        return {'error': str(e)}


def handle_auth_login(event: Dict[str, Any]) -> Dict[str, Any]:
    data = _get_json_body(event)
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    if not email or not password:
        return {'error': 'emailとpasswordは必須です'}
    table = _get_users_table()
    try:
        res = table.get_item(Key={'email': email})
        user = res.get('Item')
        if not user or not _verify_password(password, user.get('password', {})):
            return {'error': '認証に失敗しました'}
        secret = os.environ.get('JWT_SECRET', '')
        if not secret:
            return {'error': 'サーバー設定エラー（JWT_SECRET未設定）'}
        token = _jwt_sign({'sub': email, 'email': email}, secret, expires_in_seconds=3600)
        return {'token': token, 'token_type': 'Bearer', 'expires_in': 3600}
    except Exception as e:
        return {'error': str(e)}


def _get_authorized_email(event: Dict[str, Any]) -> Optional[str]:
    try:
        rc = event.get('requestContext') or {}
        authz = rc.get('authorizer') or {}
        email = authz.get('email') or authz.get('principalId')
        return email
    except Exception:
        return None


def handle_user_me_get(event: Dict[str, Any]) -> Dict[str, Any]:
    email = _get_authorized_email(event)
    if not email:
        return {'error': '未認証です'}
    table = _get_users_table()
    try:
        res = table.get_item(Key={'email': email})
        user = res.get('Item')
        if not user:
            return {'error': 'ユーザーが見つかりません'}
        # 機密情報除去
        basic = {
            'email': user.get('email'),
            'name': user.get('name'),
            'profile': user.get('profile') or {},
            'created_at': user.get('created_at'),
            'updated_at': user.get('updated_at'),
        }
        return {'status': 'ok', 'user': basic}
    except Exception as e:
        return {'error': str(e)}


def handle_user_me_put(event: Dict[str, Any]) -> Dict[str, Any]:
    email = _get_authorized_email(event)
    if not email:
        return {'error': '未認証です'}
    data = _get_json_body(event)
    # 更新可能なフィールド
    name = data.get('name')
    profile_updates = data.get('profile') if isinstance(data.get('profile'), dict) else None
    if name is None and profile_updates is None:
        return {'error': '更新フィールドがありません'}
    table = _get_users_table()
    try:
        update_expr = []
        expr_vals = {':u': datetime.utcnow().isoformat()}
        expr_names = {}
        if name is not None:
            update_expr.append('#n = :n')
            expr_vals[':n'] = name
            expr_names['#n'] = 'name'
        if profile_updates is not None:
            # 既存profileにマージ（上書き）
            # DynamoDBのUpdateExpressionだけでネストマージは難しいため、まず現状を取得してマージしてから全体をSET
            cur = table.get_item(Key={'email': email}).get('Item') or {}
            merged_profile = {**(cur.get('profile') or {}), **profile_updates}
            update_expr.append('#p = :p')
            expr_vals[':p'] = merged_profile
            expr_names['#p'] = 'profile'
        update_expr.append('updated_at = :u')
        update_str = 'SET ' + ', '.join(update_expr)
        res = table.update_item(
            Key={'email': email},
            UpdateExpression=update_str,
            ExpressionAttributeValues=expr_vals,
            ExpressionAttributeNames=expr_names if expr_names else None,
            ReturnValues='ALL_NEW'
        )
        attrs = res.get('Attributes') or {}
        basic = {
            'email': attrs.get('email'),
            'name': attrs.get('name'),
            'profile': attrs.get('profile') or {},
            'created_at': attrs.get('created_at'),
            'updated_at': attrs.get('updated_at'),
        }
        return {'status': 'ok', 'user': basic}
    except Exception as e:
        return {'error': str(e)}

# RSSフィードソース設定
RSS_SOURCES = [
    {
        'name': 'Yahoo Finance',
        'url': 'https://finance.yahoo.com/rss/2.0',
        'category': 'general'
    },
    {
        'name': 'MarketWatch Top Stories',
        'url': 'https://www.marketwatch.com/rss/topstories',
        'category': 'market'
    }
]

# ランキング用銘柄リスト
STOCK_LISTS = {
    'sp500': [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK-B', 'UNH', 'JNJ',
        'JPM', 'V', 'PG', 'HD', 'MA', 'DIS', 'PYPL', 'BAC', 'ADBE', 'CRM',
        'NFLX', 'KO', 'PEP', 'ABT', 'TMO', 'AVGO', 'COST', 'DHR', 'MRK', 'ACN',
        'WMT', 'VZ', 'TXN', 'QCOM', 'HON', 'LLY', 'UNP', 'LOW', 'IBM', 'RTX',
        'CAT', 'SPGI', 'AXP', 'PLD', 'GS', 'AMAT', 'DE', 'ADI', 'GILD', 'ISRG'
    ],
    'nasdaq100': [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX', 'ADBE', 'CRM',
        'PYPL', 'INTC', 'AMD', 'CSCO', 'QCOM', 'AVGO', 'TXN', 'ADI', 'MU', 'KLAC',
        'LRCX', 'AMAT', 'ASML', 'ORLY', 'PAYX', 'ADP', 'INTU', 'SNPS', 'CDNS', 'MELI',
        'JD', 'BIDU', 'PDD', 'NTES', 'BABA', 'TCOM', 'VRTX', 'REGN', 'GILD', 'AMGN',
        'MRNA', 'BIIB', 'ILMN', 'IDXX', 'ALGN', 'DXCM', 'WDAY', 'ZS', 'CRWD', 'OKTA'
    ]
}

# セクター・業界定義
SECTORS = {
    'XLK': {'name': 'Technology', 'symbols': ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'META', 'ADBE', 'CRM', 'PYPL', 'NFLX', 'TSLA']},
    'XLF': {'name': 'Financial', 'symbols': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'BLK', 'SCHW', 'USB']},
    'XLE': {'name': 'Energy', 'symbols': ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PSX', 'VLO', 'MPC', 'HAL', 'BKR']},
    'XLV': {'name': 'Healthcare', 'symbols': ['JNJ', 'UNH', 'PFE', 'ABT', 'TMO', 'DHR', 'MRK', 'LLY', 'GILD', 'AMGN']},
    'XLI': {'name': 'Industrial', 'symbols': ['UNP', 'HON', 'CAT', 'DE', 'RTX', 'LMT', 'BA', 'GE', 'MMM', 'UPS']},
    'XLP': {'name': 'Consumer Staples', 'symbols': ['PG', 'KO', 'PEP', 'WMT', 'COST', 'PM', 'MO', 'EL', 'CL', 'GIS']},
    'XLY': {'name': 'Consumer Discretionary', 'symbols': ['AMZN', 'TSLA', 'HD', 'DIS', 'MCD', 'NKE', 'SBUX', 'TJX', 'MAR', 'BKNG']},
    'XLU': {'name': 'Utilities', 'symbols': ['NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'XEL', 'SRE', 'DTE', 'WEC']},
    'XLRE': {'name': 'Real Estate', 'symbols': ['PLD', 'AMT', 'CCI', 'EQIX', 'PSA', 'O', 'SPG', 'WELL', 'EQR', 'AVB']}
}

# 主要銘柄リスト（より効率的な取得用）
MAJOR_STOCKS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'JNJ', 'V',
    'PG', 'UNH', 'HD', 'MA', 'BAC', 'ABBV', 'PFE', 'KO', 'AVGO', 'PEP',
    'WMT', 'DIS', 'NFLX', 'ADBE', 'CRM', 'TMO', 'ACN', 'LLY', 'COST', 'NKE'
]

# セクターETF（改善版）
SECTOR_ETFS = {
    'Technology': 'XLK',
    'Healthcare': 'XLV',
    'Financial': 'XLF',
    'Consumer Discretionary': 'XLY',
    'Communication Services': 'XLC',
    'Industrial': 'XLI',
    'Consumer Staples': 'XLP',
    'Energy': 'XLE',
    'Utilities': 'XLU',
    'Real Estate': 'XLRE',
    'Materials': 'XLB'
}

# 暗号通貨
CRYPTO_SYMBOLS = [
    'BTC-USD', 'ETH-USD', 'BNB-USD', 'XRP-USD', 'ADA-USD',
    'SOL-USD', 'DOGE-USD', 'MATIC-USD', 'DOT-USD', 'AVAX-USD'
]

# 主要指数
MAJOR_INDICES = {
    'S&P 500': '^GSPC',
    'Dow Jones': '^DJI',
    'NASDAQ': '^IXIC',
    'Russell 2000': '^RUT',
    'VIX': '^VIX',
    'Nikkei 225': '^N225',
    'FTSE 100': '^FTSE',
    'DAX': '^GDAXI'
}

# 為替ペア
CURRENCY_PAIRS = {
    'USD/JPY': 'USDJPY=X',
    'EUR/USD': 'EURUSD=X',
    'GBP/USD': 'GBPUSD=X',
    'USD/CHF': 'USDCHF=X',
    'AUD/USD': 'AUDUSD=X',
    'USD/CAD': 'USDCAD=X',
    'USD/CNY': 'USDCNY=X'
}

# 商品
COMMODITIES = {
    'Gold': 'GC=F',
    'Silver': 'SI=F',
    'Crude Oil': 'CL=F',
    'Natural Gas': 'NG=F',
    'Copper': 'HG=F',
    'Wheat': 'ZW=F',
    'Corn': 'ZC=F'
}

def get_price_change_direction(price_change):
    if price_change is None:
        return "unchanged"
    if price_change > 0:
        return "up"
    elif price_change < 0:
        return "down"
    else:
        return "unchanged"

def get_market_sentiment(avg_change):
    if avg_change > BULLISH_THRESHOLD:
        return "bullish"
    elif avg_change < BEARISH_THRESHOLD:
        return "bearish"
    else:
        return "neutral"

def serialize_for_json(obj):
    """オブジェクトをJSON serializable に変換"""
    if obj is None:
        return None

    # pd.isna()はスカラー値に対してのみ使用
    try:
        if pd.isna(obj):
            return None
    except (ValueError, TypeError):
        # リストやnumpy配列などでpd.isna()が使えない場合は無視
        pass

    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.strftime('%Y-%m-%d') if hasattr(obj, 'strftime') else str(obj)
    elif isinstance(obj, date):
        return obj.strftime('%Y-%m-%d')
    elif isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {str(k): serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_json(item) for item in obj]
    elif hasattr(obj, 'to_dict'):
        return serialize_for_json(obj.to_dict())
    else:
        return obj

def safe_dataframe_to_dict(df):
    """DataFrameを安全にdictに変換（JSON serializable）"""
    try:
        # Noneや文字列エラーの場合
        if df is None or isinstance(df, str):
            return {} if df is None else df

        # 既に辞書の場合
        if isinstance(df, dict):
            return serialize_for_json(df)

        # リストの場合
        if isinstance(df, list):
            return serialize_for_json(df)

        # numpy arrayの場合
        if hasattr(df, 'ndim') and hasattr(df, 'tolist'):
            try:
                return serialize_for_json(df.tolist())
            except:
                return {}

        # DataFrameの場合
        if hasattr(df, 'to_dict') and hasattr(df, 'index'):
            try:
                # DataFrameをdictに変換
                result = df.to_dict(orient='index')
                return serialize_for_json(result)
            except Exception as inner_e:
                # DataFrame処理に失敗した場合はrecords形式で試行
                try:
                    result = df.to_dict('records')
                    return serialize_for_json(result)
                except:
                    return f"DataFrame変換エラー: {str(inner_e)}"

        # その他の場合は空の辞書
        return {}

    except Exception as e:
        return f"DataFrame変換エラー: {str(e)}"

def safe_dataframe_to_records(df):
    """DataFrameを安全にrecordsに変換（JSON serializable）"""
    try:
        # Noneや文字列エラーをそのまま返す
        if df is None or isinstance(df, str):
            return [] if df is None else df

        # 既にリストや辞書の場合
        if isinstance(df, (list, dict)):
            return serialize_for_json(df)

        # numpy arrayの場合
        if hasattr(df, 'ndim') and hasattr(df, 'tolist'):
            try:
                return serialize_for_json(df.tolist())
            except:
                return []

        # DataFrameの場合
        if hasattr(df, 'to_dict') and hasattr(df, 'index'):
            try:
                # DataFrameをrecordsに変換
                records = df.to_dict('records')
                return serialize_for_json(records)
            except Exception as inner_e:
                # records変換に失敗した場合はlist形式で試行
                try:
                    if hasattr(df, 'values'):
                        result = df.values.tolist()
                        return serialize_for_json(result)
                    else:
                        return []
                except:
                    return f"DataFrame変換エラー: {str(inner_e)}"

        # その他の場合
        return []

    except Exception as e:
        return f"Records変換エラー: {str(e)}"

def format_currency(value: Union[int, float, str], currency: str = "USD") -> str:
    """
    通貨を適切にフォーマット（共通関数）

    Args:
        value: 数値
        currency: 通貨コード

    Returns:
        str: フォーマットされた通貨文字列
    """
    if value is None or value == "N/A":
        return "N/A"

    try:
        value = float(value)
        if currency == "JPY":
            return f"¥{value:,.0f}"
        elif currency == "USD":
            return f"${value:,.2f}"
        else:
            return f"{value:,.2f} {currency}"
    except (ValueError, TypeError):
        return str(value)

def get_execution_info(mode: str = "LAMBDA") -> Dict[str, str]:
    """実行環境の情報を取得（共通関数）"""
    return {
        'mode': mode,
        'timestamp': datetime.now().isoformat(),
        'server': 'lambda'
    }

def validate_ticker_parameter(query_parameters, headers):
    """ティッカーパラメータのバリデーション（共通化）"""
    ticker = query_parameters.get('ticker', '').upper()
    if not ticker:
        return None, {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': 'ティッカーシンボルが必要です'})
        }
    return ticker, None

def display_stock_info_local(ticker: str) -> None:
    """
    株式の基本情報をローカルで表示（共通関数）

    Args:
        ticker (str): ティッカーシンボル
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        print(f"\n=== {ticker} の基本情報（ローカル取得）===")
        print(f"会社名: {info.get('longName', 'N/A')}")
        print(f"業界: {info.get('industry', 'N/A')}")
        print(f"セクター: {info.get('sector', 'N/A')}")

        # 価格情報の安全な表示
        current_price = info.get('currentPrice')
        if current_price is not None:
            currency = "JPY" if ticker.endswith('.T') else "USD"
            print(f"現在価格: {format_currency(current_price, currency)}")
        else:
            print("現在価格: N/A")

        # 時価総額の安全な表示
        market_cap = info.get('marketCap')
        if market_cap is not None:
            currency = "JPY" if ticker.endswith('.T') else "USD"
            print(f"時価総額: {format_currency(market_cap, currency)}")
        else:
            print("時価総額: N/A")

        # 配当利回りの安全な表示
        dividend_yield = info.get('dividendYield')
        if dividend_yield is not None:
            print(f"配当利回り: {dividend_yield:.2%}")
        else:
            print("配当利回り: N/A")

    except Exception as e:
        print(f"エラー: {ticker} の情報取得に失敗しました - {e}")

def display_comprehensive_info_api(data: Dict[str, Any]) -> None:
    """
    APIから取得した包括的な株式情報を表示（共通関数）

    Args:
        data (dict): API応答データ
    """
    if not data or 'error' in data:
        print(f"エラー: {data.get('error', '不明なエラー')}")
        return

    ticker = data.get('ticker', 'N/A')
    print(f"\n=== {ticker} の包括的情報（API取得）===")

    # 基本情報
    if data.get('info'):
        info = data['info']
        print(f"会社名: {info.get('longName', 'N/A')}")
        print(f"業界: {info.get('industry', 'N/A')}")
        print(f"セクター: {info.get('sector', 'N/A')}")

        # 従業員数の安全な表示
        employees = info.get('fullTimeEmployees')
        if employees is not None:
            print(f"従業員数: {employees:,}")
        else:
            print("従業員数: N/A")

    # 価格情報
    if data.get('price'):
        price = data['price']
        print(f"\n--- 価格情報 ---")

        current_price = price.get('current_price')
        currency = price.get('currency', 'USD')
        print(f"現在価格: {format_currency(current_price, currency)}")

        # 価格変化の安全な表示
        price_change = price.get('price_change')
        if price_change is not None and isinstance(price_change, (int, float)):
            direction = get_price_change_direction(price_change)
            price_change_percent = price.get('price_change_percent', 0)
            print(f"変化: {price_change:+.2f} ({price_change_percent:+.2f}%) {direction}")

    # ESG情報
    if data.get('sustainability') and isinstance(data['sustainability'], dict):
        esg = data['sustainability'].get('esgScores', {})
        if esg:
            print(f"\n--- ESG情報 ---")
            print(f"ESG総合スコア: {esg.get('totalEsg', 'N/A')}")
            print(f"環境スコア: {esg.get('environmentScore', 'N/A')}")
            print(f"社会スコア: {esg.get('socialScore', 'N/A')}")
            print(f"ガバナンススコア: {esg.get('governanceScore', 'N/A')}")

    # 財務情報
    if data.get('financials') and isinstance(data['financials'], dict):
        income = data['financials'].get('income_statement', {})
        if income:
            print(f"\n--- 財務情報 ---")
            # 売上高を探す
            revenue_keys = ['Total Revenue', 'Revenue', 'Net Sales']
            for key in revenue_keys:
                if key in income:
                    revenue_data = income[key]
                    if isinstance(revenue_data, dict) and revenue_data:
                        latest_revenue = list(revenue_data.values())[0]
                        if latest_revenue is not None:
                            if isinstance(latest_revenue, (int, float)):
                                currency = data.get('price', {}).get('currency', 'USD')
                                print(f"売上高: {format_currency(latest_revenue, currency)}")
                            else:
                                print(f"売上高: {latest_revenue}")
                    break

    # 決算情報
    if data.get('earnings') and isinstance(data['earnings'], dict):
        earnings = data['earnings']
        if earnings and not earnings.get('error'):
            print(f"\n--- 決算情報 ---")
            if 'trailingEps' in earnings:
                print(f"過去12ヶ月EPS: {earnings['trailingEps']}")
            if 'forwardEps' in earnings:
                print(f"予想EPS: {earnings['forwardEps']}")
            if 'trailingPE' in earnings:
                print(f"過去12ヶ月P/E比: {earnings['trailingPE']}")
            if 'forwardPE' in earnings:
                print(f"予想P/E比: {earnings['forwardPE']}")
            if 'pegRatio' in earnings:
                print(f"PEGレシオ: {earnings['pegRatio']}")

    # 株式分割
    if data.get('splits') and isinstance(data['splits'], list) and data['splits']:
        print(f"\n--- 株式分割履歴 ---")
        for split in data['splits'][:3]:  # 最新3件
            if isinstance(split, dict):
                print(f"日付: {split.get('date')}, 比率: {split.get('ratio')}")

    # 配当情報
    if data.get('dividends') and isinstance(data['dividends'], list) and data['dividends']:
        print(f"\n--- 配当履歴 ---")
        for dividend in data['dividends'][:3]:  # 最新3件
            if isinstance(dividend, dict):
                amount = dividend.get('amount', 'N/A')
                if isinstance(amount, (int, float)):
                    currency = data.get('price', {}).get('currency', 'USD')
                    print(f"日付: {dividend.get('date')}, 配当: {format_currency(amount, currency)}")
                else:
                    print(f"日付: {dividend.get('date')}, 配当: {amount}")

    # 株主情報
    if data.get('holders') and isinstance(data['holders'], dict):
        holders = data['holders']
        if holders and not holders.get('error'):
            print(f"\n--- 株主情報 ---")
            if holders.get('major_holders') and isinstance(holders['major_holders'], list):
                print("大株主:")
                for holder in holders['major_holders'][:3]:  # 上位3件
                    if isinstance(holder, dict):
                        print(f"  {holder.get('Holder', 'N/A')}: {holder.get('% of Shares', 'N/A')}%")

    # ESG情報
    if data.get('sustainability') and isinstance(data['sustainability'], dict):
        sustainability = data['sustainability']
        if sustainability and not sustainability.get('error'):
            esg = sustainability.get('esgScores', {})
            if esg:
                print(f"\n--- ESG情報 ---")
                print(f"ESG総合スコア: {esg.get('totalEsg', 'N/A')}")
                print(f"環境スコア: {esg.get('environmentScore', 'N/A')}")
                print(f"社会スコア: {esg.get('socialScore', 'N/A')}")
                print(f"ガバナンススコア: {esg.get('governanceScore', 'N/A')}")

    # アナリスト推奨履歴
    if data.get('recommendations') and isinstance(data['recommendations'], list) and data['recommendations']:
        print(f"\n--- アナリスト推奨履歴 ---")
        for rec in data['recommendations'][:3]:  # 最新3件
            if isinstance(rec, dict):
                print(f"日付: {rec.get('Date', 'N/A')}, 推奨: {rec.get('To Grade', 'N/A')}")

    # 決算日
    if data.get('earnings_dates') and isinstance(data['earnings_dates'], list) and data['earnings_dates']:
        print(f"\n--- 決算日 ---")
        for date_info in data['earnings_dates'][:3]:  # 最新3件
            if isinstance(date_info, dict):
                print(f"日付: {date_info.get('Earnings Date', 'N/A')}, EPS予想: {date_info.get('EPS Estimate', 'N/A')}")

    # 株価履歴
    if data.get('history') and isinstance(data['history'], list):
        print(f"\n--- 直近の株価履歴 ---")
        recent_data = data['history'][-5:] if len(data['history']) >= 5 else data['history']
        for day in recent_data:
            close_price = day.get('close', 'N/A')
            volume = day.get('volume', 0)
            if isinstance(volume, (int, float)):
                volume_str = f"{volume:,}"
            else:
                volume_str = str(volume)
            print(f"{day.get('date', 'N/A')}: 終値 {close_price} (出来高: {volume_str})")

    # アナリスト情報
    if data.get('analysts') and isinstance(data['analysts'], dict):
        analysts = data['analysts']
        print(f"\n--- アナリスト情報 ---")
        if analysts.get('recommendation_mean'):
            print(f"推奨平均: {analysts['recommendation_mean']}")
        if analysts.get('target_mean_price'):
            print(f"目標平均価格: {analysts['target_mean_price']}")
        if analysts.get('number_of_analysts'):
            print(f"アナリスト数: {analysts['number_of_analysts']}")

    # ニュース情報
    if data.get('news') and isinstance(data['news'], list) and len(data['news']) > 0:
        print(f"\n--- 最新ニュース ---")
        for i, news_item in enumerate(data['news'][:3], 1):  # 最新3件
            if isinstance(news_item, dict):
                title = news_item.get('title', 'N/A')
                print(f"{i}. {title}")

    # 実行環境情報
    if data.get('execution_info'):
        exec_info = data['execution_info']
        print(f"\n--- 実行環境情報 ---")
        print(f"実行モード: {exec_info.get('mode', 'N/A')}")
        print(f"実行時刻: {exec_info.get('timestamp', 'N/A')}")

def display_search_results_api(results: Dict[str, Any]) -> None:
    """
    API検索結果を表示（共通関数）

    Args:
        results (dict): 検索結果
    """
    if not results or 'error' in results:
        print(f"検索エラー: {results.get('error', '不明なエラー')}")
        return

    print(f"\n=== 検索結果: '{results.get('query', 'N/A')}' ({results.get('region', 'N/A')}) ===")
    print(f"件数: {results.get('count', 0)}")

    for i, result in enumerate(results.get('results', []), 1):
        print(f"\n{i}. {result.get('symbol', 'N/A')} - {result.get('name', 'N/A')}")
        print(f"   取引所: {result.get('exchange', 'N/A')} | タイプ: {result.get('type', 'N/A')}")

        # 価格情報の安全な表示
        current_price = result.get('current_price')
        if current_price is not None:
            currency = result.get('currency', 'USD')
            price_info = f"   価格: {format_currency(current_price, currency)}"

            # 価格変化の安全な表示
            price_change = result.get('price_change')
            if price_change is not None and isinstance(price_change, (int, float)):
                direction = get_price_change_direction(price_change)
                price_change_percent = result.get('price_change_percent', 0)
                price_info += f" ({price_change:+.2f}, {price_change_percent:+.2f}% {direction})"
            print(price_info)

        # エラー情報の表示
        if result.get('price_error'):
            print(f"   価格取得エラー: {result['price_error']}")

    # 実行環境情報
    if results.get('execution_info'):
        exec_info = results['execution_info']
        print(f"\n--- 実行環境情報 ---")
        print(f"実行モード: {exec_info.get('mode', 'N/A')}")
        print(f"実行時刻: {exec_info.get('timestamp', 'N/A')}")

def lambda_handler(event, context):
    """
    AWS Lambda メインハンドラー
    API Gateway からのリクエストを処理
    """
    try:
        # CORS ヘッダーを設定
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }

        # OPTIONSリクエスト（CORS プリフライト）への対応
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'OK'})
            }

        # パスとメソッドを取得
        resource = event.get('resource', '')
        method = event.get('httpMethod', '')
        path_parameters = event.get('pathParameters', {})
        query_parameters = event.get('queryStringParameters', {}) or {}

        # ベースURL（/）へのアクセス - Swagger UIを表示
        if resource == '/' or resource == '':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'text/html',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': generate_swagger_ui_html(event, context)
            }

        # リソースごとの処理
        if '/auth/register' in resource and method == 'POST':
            result = handle_auth_register(event)
        elif '/auth/login' in resource and method == 'POST':
            result = handle_auth_login(event)
        elif '/user/me' in resource and method == 'GET':
            result = handle_user_me_get(event)
        elif '/user/me' in resource and method == 'PUT':
            result = handle_user_me_put(event)
        elif '/search' in resource:
            query = query_parameters.get('q', '')
            if not query:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': '検索クエリが必要です'})
                }
            result = search_stocks_api(query, query_parameters)
        elif '/tickerDetail' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            # periodパラメータも受け取る（history用）
            period = query_parameters.get('period', '1mo')
            result = get_stock_info_api(ticker, period)
        elif '/ticker/basic' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            result = get_stock_basic_info_api(ticker)
        elif '/ticker/price' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            result = get_stock_price_api(ticker)
        elif '/ticker/history' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            period = query_parameters.get('period', '1mo')
            result = get_stock_history_api(ticker, period)
        elif '/ticker/financials' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            result = get_stock_financials_api(ticker)
        elif '/ticker/analysts' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            result = get_stock_analysts_api(ticker)
        elif '/ticker/holders' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            result = get_stock_holders_api(ticker)
        elif '/ticker/events' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            result = get_stock_events_api(ticker)
        elif '/ticker/news' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            result = get_stock_news_api(ticker)
        elif '/ticker/options' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            result = get_stock_options_api(ticker)
        elif '/ticker/sustainability' in resource:
            ticker, error_response = validate_ticker_parameter(query_parameters, headers)
            if error_response:
                return error_response
            result = get_stock_sustainability_api(ticker)
        elif '/chart' in resource:
            ticker = query_parameters.get('ticker', '').upper()
            if not ticker:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'ティッカーシンボルが必要です'})
                }
            period = query_parameters.get('period', '1mo')
            size = query_parameters.get('size', '800x400')
            chart_type = query_parameters.get('type', 'line')
            # 画像はBase64バイナリで返却
            chart_base64, err = get_stock_chart_api(ticker, period, size, chart_type)
            if err:
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': err})
                }
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'image/png',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': chart_base64,
                'isBase64Encoded': True
            }
        elif '/home' in resource:
            result = get_stock_home_api()
        elif '/news/rss' in resource:
            result = lamuda_get_rss_news_api(query_parameters)
        elif '/rankings/stocks' in resource:
            result = get_stock_rankings_api(query_parameters)
        elif '/rankings/sectors' in resource:
            result = get_sector_rankings_api(query_parameters)
        elif '/rankings/crypto' in resource:
            result = get_crypto_rankings_api(query_parameters)
        elif '/markets/indices' in resource:
            result = get_markets_indices_api(query_parameters)
        elif '/markets/currencies' in resource:
            result = get_markets_currencies_api(query_parameters)
        elif '/markets/commodities' in resource:
            result = get_markets_commodities_api(query_parameters)
        elif '/markets/status' in resource:
            result = get_markets_status_api(query_parameters)
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'リソースが見つかりません'})
            }

        if result.get('error'):
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps(result)
            }

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(result, default=serialize_for_json)
        }

    except Exception as e:
        print(f"Lambda Error: {str(e)}")
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': '内部サーバーエラーが発生しました',
                'details': str(e)
            })
        }


def search_stocks_api(query, query_parameters):
    """銘柄検索（API用）- 株価情報付き"""
    try:
        import requests

        # 検索結果を10件に制限
        limit = min(int(query_parameters.get('limit', 10)), 10)
        region = query_parameters.get('region', 'US')

        base_url = "https://query1.finance.yahoo.com/v1/finance/search"

        if region.upper() == 'JP':
            params = {
                'q': query,
                'quotesCount': limit,
                'newsCount': 0,
                'enableFuzzyQuery': True,
                'region': 'JP',
                'lang': 'ja-JP'
            }
        else:
            params = {
                'q': query,
                'quotesCount': limit,
                'newsCount': 0,
                'enableFuzzyQuery': True
            }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(base_url, params=params, headers=headers)
        data = response.json()

        if 'quotes' in data and data['quotes']:
            results = []
            for quote in data['quotes'][:10]:  # 最大10件に制限
                symbol = quote.get('symbol', '')

                # 基本情報
                result = {
                    'symbol': symbol,
                    'name': quote.get('longname', quote.get('shortname', '')),
                    'exchange': quote.get('exchange', ''),
                    'type': quote.get('quoteType', ''),
                    'score': quote.get('score', 0),
                    'timestamp': datetime.now().isoformat()
                }

                # 株価情報を取得
                try:
                    stock = yf.Ticker(symbol)
                    info = stock.info

                    current_price = info.get('currentPrice', info.get('regularMarketPrice'))
                    previous_close = info.get('previousClose')

                    if current_price is not None:
                        result['current_price'] = round(float(current_price), 2)
                        result['currency'] = info.get('currency', 'USD')

                        # 前日との差分を計算
                        if previous_close is not None:
                            previous_close = float(previous_close)
                            price_change = current_price - previous_close
                            price_change_percent = (price_change / previous_close) * 100

                            result['previous_close'] = round(previous_close, 2)
                            result['price_change'] = round(price_change, 2)
                            result['price_change_percent'] = round(price_change_percent, 2)
                            result['price_change_direction'] = get_price_change_direction(price_change)

                        # 追加情報
                        result['market_cap'] = info.get('marketCap')
                        result['volume'] = info.get('volume')
                        result['avg_volume'] = info.get('averageVolume')

                except Exception as e:
                    # 株価取得に失敗した場合でも基本情報は返す
                    result['price_error'] = f'株価取得エラー: {str(e)}'

                results.append(result)

            return {
                'query': query,
                'region': region,
                'results': results,
                'count': len(results),
                'max_results': 10,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'query': query,
                'region': region,
                'results': [],
                'count': 0,
                'max_results': 10,
                'message': '検索結果が見つかりませんでした',
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        return {'error': f'検索エラー: {str(e)}'}


def get_stock_info_api(ticker, period='1mo'):
    """包括的な株式情報取得API（統合版）- 各要素専用関数を呼び出し"""
    try:
        # 各要素専用の関数を呼び出して統合
        basic_info = get_stock_basic_info_api(ticker)
        price_info = get_stock_price_api(ticker)
        history_info = get_stock_history_api(ticker, period)
        financials_info = get_stock_financials_api(ticker)
        analysts_info = get_stock_analysts_api(ticker)
        holders_info = get_stock_holders_api(ticker)
        events_info = get_stock_events_api(ticker)
        news_info = get_stock_news_api(ticker)
        options_info = get_stock_options_api(ticker)
        sustainability_info = get_stock_sustainability_api(ticker)

        # 統合結果を作成
        result = {
            'ticker': ticker,
            'period': period,
            # 基本情報
            'info': basic_info.get('info', {}),
            'info_error': basic_info.get('info_error'),
            'fast_info': basic_info.get('fast_info', {}),
            'logo_url': basic_info.get('logo_url'),
            'isin': basic_info.get('isin'),
            # 株価情報
            'price': price_info.get('price'),
            # 履歴情報
            'history': history_info.get('history', []),
            # 財務情報
            'financials': financials_info.get('financials', {}),
            'earnings': financials_info.get('earnings', {}),
            # アナリスト情報
            'analysts': analysts_info.get('analysts', {}),
            'recommendations': analysts_info.get('recommendations', []),
            'analysis': analysts_info.get('analysis', {}),
            'upgrades_downgrades': analysts_info.get('upgrades_downgrades', []),
            # 株主情報
            'holders': holders_info.get('holders', {}),
            'shares': holders_info.get('shares', {}),
            # イベント情報
            'calendar': events_info.get('calendar', []),
            'earnings_dates': events_info.get('earnings_dates', []),
            'dividends': events_info.get('dividends', []),
            'splits': events_info.get('splits', []),
            # ニュース情報
            'news': news_info.get('news', []),
            # オプション情報
            'options': options_info.get('options', []),
            # ESG情報
            'sustainability': sustainability_info.get('sustainability', {}),
            # 実行情報
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }

        # エラーがある場合は統合
        errors = []
        for name, data in [
            ('基本情報', basic_info),
            ('株価情報', price_info),
            ('履歴情報', history_info),
            ('財務情報', financials_info),
            ('アナリスト情報', analysts_info),
            ('株主情報', holders_info),
            ('イベント情報', events_info),
            ('ニュース情報', news_info),
            ('オプション情報', options_info),
            ('ESG情報', sustainability_info)
        ]:
            if data.get('error'):
                errors.append(f"{name}: {data['error']}")

        if errors:
            result['partial_errors'] = errors

        return result

    except Exception as e:
        return {'error': f'銘柄情報取得エラー: {str(e)}'}

def get_stock_basic_info_api(ticker):
    """基本情報取得API"""
    try:
        stock = yf.Ticker(ticker)

        # 詳細情報
        try:
            info = stock.info
            if not info:
                info = {}
                info_error = "詳細情報が取得できませんでした"
            else:
                info_error = None
        except Exception as e:
            info = {}
            info_error = f"詳細情報取得エラー: {str(e)}"

        # 高速基本情報
        try:
            fast_info = stock.fast_info
            if hasattr(fast_info, '__dict__'):
                fast_info_dict = {}
                for key in dir(fast_info):
                    if not key.startswith('_') and not callable(getattr(fast_info, key)):
                        try:
                            value = getattr(fast_info, key)
                            if value is not None:
                                fast_info_dict[key] = float(value) if isinstance(value, (int, float)) else str(value)
                        except:
                            pass
                fast_info = fast_info_dict
            else:
                fast_info = {}
        except Exception as e:
            fast_info = {}

        # ロゴURL (Clearbit使用)
        logo_url = None
        try:
            if info:
                # websiteからClearbitロゴURLを生成
                website = (info.get('website') or
                          info.get('webSite') or
                          info.get('companyWebsite'))

                if website:
                    import re
                    # ドメイン名を抽出
                    m = re.search(r'https?://(?:www\.)?([^/]+)', website)
                    if m:
                        domain = m.group(1)
                        logo_url = f"https://logo.clearbit.com/{domain}"

                # websiteがない場合は主要企業を直接指定
                if not logo_url:
                    known_logos = {
                        'AAPL': 'https://logo.clearbit.com/apple.com',
                        'MSFT': 'https://logo.clearbit.com/microsoft.com',
                        'GOOGL': 'https://logo.clearbit.com/google.com',
                        'AMZN': 'https://logo.clearbit.com/amazon.com',
                        'TSLA': 'https://logo.clearbit.com/tesla.com',
                        'META': 'https://logo.clearbit.com/meta.com',
                        'NVDA': 'https://logo.clearbit.com/nvidia.com',
                        'JPM': 'https://logo.clearbit.com/jpmorganchase.com',
                        'V': 'https://logo.clearbit.com/visa.com',
                        'JNJ': 'https://logo.clearbit.com/jnj.com',
                        'WMT': 'https://logo.clearbit.com/walmart.com',
                        'PG': 'https://logo.clearbit.com/pg.com',
                        'UNH': 'https://logo.clearbit.com/unitedhealthgroup.com',
                        'HD': 'https://logo.clearbit.com/homedepot.com',
                        'BAC': 'https://logo.clearbit.com/bankofamerica.com',
                        'MA': 'https://logo.clearbit.com/mastercard.com',
                        'DIS': 'https://logo.clearbit.com/disney.com',
                        'ADBE': 'https://logo.clearbit.com/adobe.com',
                        'CRM': 'https://logo.clearbit.com/salesforce.com',
                        'NFLX': 'https://logo.clearbit.com/netflix.com'
                    }
                    if ticker.upper() in known_logos:
                        logo_url = known_logos[ticker.upper()]
        except Exception as e:
            logo_url = None

        # ISIN
        isin = None
        try:
            isin = stock.isin
        except Exception as e:
            isin = {'error': f'ISIN取得エラー: {str(e)}'}

        result = {
            'ticker': ticker,
            'info': info,
            'info_error': info_error,
            'fast_info': fast_info,
            'logo_url': logo_url,
            'isin': isin,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'基本情報取得エラー: {str(e)}'}

def get_stock_price_api(ticker):
    """株価情報取得API"""
    try:
        stock = yf.Ticker(ticker)

        # 詳細情報と高速情報を取得
        try:
            info = stock.info
        except:
            info = {}

        try:
            fast_info = stock.fast_info
            if hasattr(fast_info, '__dict__'):
                fast_info_dict = {}
                for key in dir(fast_info):
                    if not key.startswith('_') and not callable(getattr(fast_info, key)):
                        try:
                            value = getattr(fast_info, key)
                            if value is not None:
                                fast_info_dict[key] = float(value) if isinstance(value, (int, float)) else str(value)
                        except:
                            pass
                fast_info = fast_info_dict
            else:
                fast_info = {}
        except:
            fast_info = {}

        # 株価情報
        price = None
        try:
            current_price = fast_info.get('last_price') or info.get('currentPrice') if info else None
            previous_close = fast_info.get('previous_close') or info.get('previousClose') if info else None

            if current_price is not None:
                price = {
                    'current_price': round(float(current_price), 2),
                    'currency': fast_info.get('financial_currency') or info.get('currency', 'USD') if info else 'USD',
                    'timestamp': datetime.now().isoformat()
                }
                if previous_close is not None:
                    previous_close = float(previous_close)
                    diff = current_price - previous_close
                    price['previous_close'] = round(previous_close, 2)
                    price['price_change'] = round(diff, 2)
                    price['price_change_percent'] = round(diff / previous_close * 100, 2)
                    price['price_change_direction'] = get_price_change_direction(diff)
        except Exception as e:
            price = {'error': f'価格情報取得エラー: {str(e)}'}

        result = {
            'ticker': ticker,
            'price': price,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'株価情報取得エラー: {str(e)}'}

def get_stock_history_api(ticker, period='1mo'):
    """株価履歴取得API"""
    try:
        stock = yf.Ticker(ticker)

        # 履歴
        history = []
        try:
            valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
            if period not in valid_periods:
                period = '1mo'

            hist_df = stock.history(period=period)
            if not hist_df.empty:
                history = [{
                    'date': idx.strftime('%Y-%m-%d'),
                    'open': round(float(row['Open']), 2),
                    'high': round(float(row['High']), 2),
                    'low': round(float(row['Low']), 2),
                    'close': round(float(row['Close']), 2),
                    'volume': int(row['Volume'])
                } for idx, row in hist_df.iterrows()]
        except Exception as e:
            history = {'error': f'履歴データ取得エラー: {str(e)}'}

        result = {
            'ticker': ticker,
            'period': period,
            'history': history,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'株価履歴取得エラー: {str(e)}'}

def get_stock_financials_api(ticker):
    """財務情報取得API"""
    try:
        stock = yf.Ticker(ticker)

        # 財務諸表
        financials = {}
        try:
            # 損益計算書
            income_stmt = stock.income_stmt
            if income_stmt is not None and hasattr(income_stmt, 'empty') and not income_stmt.empty:
                income_stmt_data = safe_dataframe_to_dict(income_stmt)
            else:
                income_stmt_data = {}

            # 貸借対照表
            balance_sheet = stock.balance_sheet
            if balance_sheet is not None and hasattr(balance_sheet, 'empty') and not balance_sheet.empty:
                balance_sheet_data = safe_dataframe_to_dict(balance_sheet)
            else:
                balance_sheet_data = {}

            # キャッシュフロー
            cashflow = stock.cashflow
            if cashflow is not None and hasattr(cashflow, 'empty') and not cashflow.empty:
                cashflow_data = safe_dataframe_to_dict(cashflow)
            else:
                cashflow_data = {}

            financials = {
                'income_statement': income_stmt_data,
                'balance_sheet': balance_sheet_data,
                'cashflow': cashflow_data
            }
        except Exception as e:
            financials = {'error': f'財務情報取得エラー: {str(e)}'}

        # 決算情報
        earnings = {}
        try:
            info = stock.info
            if info:
                earnings_keys = ['trailingEps', 'forwardEps', 'trailingPE', 'forwardPE', 'pegRatio']
                for key in earnings_keys:
                    if key in info and info[key] is not None:
                        earnings[key] = info[key]
        except Exception as e:
            earnings = {'error': f'決算情報取得エラー: {str(e)}'}

        result = {
            'ticker': ticker,
            'financials': financials,
            'earnings': earnings,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'財務情報取得エラー: {str(e)}'}

def get_stock_analysts_api(ticker):
    """アナリスト情報取得API"""
    try:
        stock = yf.Ticker(ticker)

        # アナリスト予想
        analysts = {}
        try:
            info = stock.info
            if info:
                if 'recommendationMean' in info:
                    analysts['recommendation_mean'] = info['recommendationMean']
                if 'targetMeanPrice' in info:
                    analysts['target_mean_price'] = info['targetMeanPrice']
                if 'numberOfAnalystOpinions' in info:
                    analysts['number_of_analysts'] = info['numberOfAnalystOpinions']
                keys = ['strongBuy', 'buy', 'hold', 'sell', 'strongSell']
                ratings = {k: info[k] for k in keys if k in info}
                if ratings:
                    analysts['rating_distribution'] = ratings
        except Exception as e:
            analysts = {'error': f'アナリスト予想取得エラー: {str(e)}'}

        # アナリスト推奨履歴
        recommendations_data = []
        try:
            recommendations = stock.get_recommendations()
            if not recommendations.empty:
                recommendations_data = safe_dataframe_to_records(recommendations)
        except Exception as e:
            recommendations_data = {'error': f'推奨履歴取得エラー: {str(e)}'}

        # アナリスト分析
        analysis_data = {}
        try:
            analysis = stock.get_analysis()
            if not analysis.empty:
                analysis_data = safe_dataframe_to_dict(analysis)
        except Exception as e:
            analysis_data = {'error': f'アナリスト分析取得エラー: {str(e)}'}

        # 格付け変更履歴
        upgrades_downgrades_data = []
        try:
            upgrades_downgrades = stock.get_upgrades_downgrades()
            if not upgrades_downgrades.empty:
                upgrades_downgrades_data = safe_dataframe_to_records(upgrades_downgrades)
        except Exception as e:
            upgrades_downgrades_data = {'error': f'格付け変更履歴取得エラー: {str(e)}'}

        result = {
            'ticker': ticker,
            'analysts': analysts,
            'recommendations': recommendations_data,
            'analysis': analysis_data,
            'upgrades_downgrades': upgrades_downgrades_data,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'アナリスト情報取得エラー: {str(e)}'}

def get_stock_holders_api(ticker):
    """株主情報取得API"""
    try:
        stock = yf.Ticker(ticker)

        # 株主情報
        holders_data = {}
        try:
            # 大株主
            major_holders_data = safe_dataframe_to_records(stock.major_holders)

            # 機関投資家
            institutional_holders_data = safe_dataframe_to_records(stock.institutional_holders)

            # 投資信託
            mutualfund_holders_data = safe_dataframe_to_records(stock.mutualfund_holders)

            holders_data = {
                'major_holders': major_holders_data,
                'institutional_holders': institutional_holders_data,
                'mutualfund_holders': mutualfund_holders_data
            }
        except Exception as e:
            holders_data = {'error': f'株主情報取得エラー: {str(e)}'}

        # 株式数詳細
        shares_data = {}
        try:
            shares_data = safe_dataframe_to_dict(stock.shares)
        except Exception as e:
            shares_data = {'error': f'株式数取得エラー: {str(e)}'}

        result = {
            'ticker': ticker,
            'holders': holders_data,
            'shares': shares_data,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'株主情報取得エラー: {str(e)}'}

def get_stock_events_api(ticker):
    """イベント情報取得API"""
    try:
        stock = yf.Ticker(ticker)

        # カレンダー（決算日など）
        calendar_data = []
        try:
            calendar = stock.calendar
            if calendar is not None:
                calendar_data = safe_dataframe_to_records(calendar)
        except Exception as e:
            calendar_data = {'error': f'カレンダー取得エラー: {str(e)}'}

        # 決算日
        earnings_dates_data = []
        try:
            earnings_dates = stock.earnings_dates
            if earnings_dates is not None:
                earnings_dates_data = safe_dataframe_to_records(earnings_dates)
        except Exception as e:
            earnings_dates_data = {'error': f'決算日取得エラー: {str(e)}'}

        # 配当
        dividends = []
        try:
            dividends_series = stock.dividends
            if dividends_series is not None and hasattr(dividends_series, 'empty') and not dividends_series.empty:
                dividends = [{
                    'date': idx.strftime('%Y-%m-%d'),
                    'amount': float(val)
                } for idx, val in dividends_series.items()]
            elif dividends_series is not None and hasattr(dividends_series, 'items'):
                dividends = [{
                    'date': idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx),
                    'amount': float(val)
                } for idx, val in dividends_series.items()]
        except Exception as e:
            dividends = {'error': f'配当情報取得エラー: {str(e)}'}

        # 株式分割
        splits = []
        try:
            splits_series = stock.splits
            if splits_series is not None and hasattr(splits_series, 'empty') and not splits_series.empty:
                splits = [{
                    'date': idx.strftime('%Y-%m-%d'),
                    'ratio': float(val)
                } for idx, val in splits_series.items()]
            elif splits_series is not None and hasattr(splits_series, 'items'):
                splits = [{
                    'date': idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx),
                    'ratio': float(val)
                } for idx, val in splits_series.items()]
        except Exception as e:
            splits = {'error': f'株式分割取得エラー: {str(e)}'}

        result = {
            'ticker': ticker,
            'calendar': calendar_data,
            'earnings_dates': earnings_dates_data,
            'dividends': dividends,
            'splits': splits,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'イベント情報取得エラー: {str(e)}'}

def get_stock_news_api(ticker):
    """ニュース情報取得API"""
    try:
        stock = yf.Ticker(ticker)

        # ニュース
        news = []
        try:
            news_data = stock.get_news()
            if isinstance(news_data, list):
                news = news_data
            elif hasattr(news_data, 'empty') and not news_data.empty:
                news = safe_dataframe_to_records(news_data)
            elif news_data:
                # その他のデータ型の場合
                news = news_data if isinstance(news_data, list) else []
        except Exception as e:
            news = {'error': f'ニュース取得エラー: {str(e)}'}

        result = {
            'ticker': ticker,
            'news': news,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'ニュース情報取得エラー: {str(e)}'}

def get_stock_options_api(ticker):
    """オプション情報取得API"""
    try:
        stock = yf.Ticker(ticker)

        # オプション
        options_data = []
        try:
            options_dates = stock.options
            if options_dates:
                expiry = options_dates[0]
                chain = stock.option_chain(expiry)
                calls_data = [{
                    'strike': float(r['strike']) if not pd.isna(r['strike']) else 0.0,
                    'last_price': float(r['lastPrice']) if not pd.isna(r['lastPrice']) else 0.0,
                    'bid': float(r['bid']) if not pd.isna(r['bid']) else 0.0,
                    'ask': float(r['ask']) if not pd.isna(r['ask']) else 0.0,
                    'volume': int(r['volume']) if not pd.isna(r['volume']) else 0,
                    'open_interest': int(r['openInterest']) if not pd.isna(r['openInterest']) else 0
                } for _, r in chain.calls.iterrows()]
                puts_data = [{
                    'strike': float(r['strike']) if not pd.isna(r['strike']) else 0.0,
                    'last_price': float(r['lastPrice']) if not pd.isna(r['lastPrice']) else 0.0,
                    'bid': float(r['bid']) if not pd.isna(r['bid']) else 0.0,
                    'ask': float(r['ask']) if not pd.isna(r['ask']) else 0.0,
                    'volume': int(r['volume']) if not pd.isna(r['volume']) else 0,
                    'open_interest': int(r['openInterest']) if not pd.isna(r['openInterest']) else 0
                } for _, r in chain.puts.iterrows()]
                options_data = {'expiry_date': expiry, 'calls': calls_data, 'puts': puts_data}
        except Exception as e:
            options_data = {'error': f'オプション情報取得エラー: {str(e)}'}

        result = {
            'ticker': ticker,
            'options': options_data,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'オプション情報取得エラー: {str(e)}'}

def get_stock_sustainability_api(ticker):
    """ESG情報取得API"""
    try:
        stock = yf.Ticker(ticker)

        # ESG情報
        sustainability_data = {}
        try:
            sustainability = stock.get_sustainability()
            if not sustainability.empty:
                sustainability_data = safe_dataframe_to_dict(sustainability)
        except Exception as e:
            sustainability_data = {'error': f'ESG情報取得エラー: {str(e)}'}

        result = {
            'ticker': ticker,
            'sustainability': sustainability_data,
            'execution_info': get_execution_info('LAMBDA'),
            'timestamp': datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {'error': f'ESG情報取得エラー: {str(e)}'}

def get_stock_home_api():
    """ホーム画面用情報取得API - 各エンドポイントの処理を並行実行で統合"""
    import concurrent.futures
    import time

    try:
        result = {}
        start_time = time.time()

        # 並行処理用のヘルパー関数
        def fetch_news():
            try:
                news_params = {'limit': '10', 'sort': 'published_desc'}
                return ('news_rss', lamuda_get_rss_news_api(news_params))
            except Exception as e:
                return ('news_rss', {'error': f'ニュース取得エラー: {str(e)}'})

        def fetch_gainers():
            try:
                rankings_params = {'type': 'gainers', 'limit': '10', 'market': 'sp500'}
                return ('gainers', get_stock_rankings_api(rankings_params))
            except Exception as e:
                return ('gainers', {'error': f'上昇株取得エラー: {str(e)}'})

        def fetch_losers():
            try:
                rankings_params = {'type': 'losers', 'limit': '10', 'market': 'sp500'}
                return ('losers', get_stock_rankings_api(rankings_params))
            except Exception as e:
                return ('losers', {'error': f'下落株取得エラー: {str(e)}'})

        def fetch_sectors():
            try:
                sector_rankings_params = {'limit': '10'}
                return ('rankings_sectors', get_sector_rankings_api(sector_rankings_params))
            except Exception as e:
                return ('rankings_sectors', {'error': f'セクターランキング取得エラー: {str(e)}'})

        def fetch_indices():
            try:
                indices_params = {}
                return ('markets_indices', get_markets_indices_api(indices_params))
            except Exception as e:
                return ('markets_indices', {'error': f'主要指数取得エラー: {str(e)}'})

        def fetch_currencies():
            try:
                currency_params = {}
                return ('markets_currencies', get_markets_currencies_api(currency_params))
            except Exception as e:
                return ('markets_currencies', {'error': f'為替レート取得エラー: {str(e)}'})

        def fetch_commodities():
            try:
                commodity_params = {}
                return ('markets_commodities', get_markets_commodities_api(commodity_params))
            except Exception as e:
                return ('markets_commodities', {'error': f'商品価格取得エラー: {str(e)}'})

        def fetch_status():
            try:
                status_params = {}
                return ('markets_status', get_markets_status_api(status_params))
            except Exception as e:
                return ('markets_status', {'error': f'市場状況取得エラー: {str(e)}'})

        # 並行処理で全ての API を実行（タイムアウト設定）
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            # 全てのタスクを並行実行
            future_to_name = {
                executor.submit(fetch_news): 'news',
                executor.submit(fetch_gainers): 'gainers',
                executor.submit(fetch_losers): 'losers',
                executor.submit(fetch_sectors): 'sectors',
                executor.submit(fetch_indices): 'indices',
                executor.submit(fetch_currencies): 'currencies',
                executor.submit(fetch_commodities): 'commodities',
                executor.submit(fetch_status): 'status'
            }

            gainers_result = None
            losers_result = None

            # 結果を収集（30秒でタイムアウト）
            for future in concurrent.futures.as_completed(future_to_name, timeout=30):
                try:
                    key, data = future.result()
                    if key == 'gainers':
                        gainers_result = data
                    elif key == 'losers':
                        losers_result = data
                    elif key in ['news_rss', 'rankings_sectors', 'markets_indices', 'markets_currencies', 'markets_commodities', 'markets_status']:
                        result[key] = data
                except Exception as e:
                    # 個別のタスクが失敗した場合
                    task_name = future_to_name[future]
                    result[f'{task_name}_error'] = f'{task_name}取得エラー: {str(e)}'

            # rankings_stocks を組み立て
            if gainers_result and losers_result:
                result['rankings_stocks'] = {
                    'gainers': gainers_result,
                    'losers': losers_result
                }
            else:
                result['rankings_stocks'] = {
                    'gainers': gainers_result or {'error': '上昇株データ取得失敗'},
                    'losers': losers_result or {'error': '下落株データ取得失敗'}
                }

        # メタ情報
        end_time = time.time()
        result['execution_info'] = get_execution_info('LAMBDA')
        result['execution_info']['parallel_execution_time'] = f"{end_time - start_time:.2f}秒"
        result['timestamp'] = datetime.now().isoformat()
        result['endpoints_integrated'] = [
            'news/rss',
            'rankings/stocks',
            'rankings/sectors',
            'markets/indices',
            'markets/currencies',
            'markets/commodities',
            'markets/status'
        ]

        return result

    except concurrent.futures.TimeoutError:
        return {'error': 'ホーム情報取得がタイムアウトしました（30秒）'}
    except Exception as e:
        return {'error': f'ホーム情報取得エラー: {str(e)}'}


def get_api_gateway_url(event=None, context=None):
    """API GatewayのURLを動的に取得する"""
    # 1. 環境変数から取得
    api_url = os.environ.get('API_GATEWAY_URL', '')
    if api_url:
        return api_url

    # 2. 代替環境変数から取得
    api_url = os.environ.get('AWS_API_GATEWAY_URL', '')
    if api_url:
        return api_url

    # 3. リクエストヘッダーから取得
    if event:
        headers = event.get('headers', {})
        host = headers.get('Host', '')
        if host:
            protocol = 'https' if headers.get('X-Forwarded-Proto') == 'https' else 'http'
            return f"{protocol}://{host}"

    # 4. Lambdaコンテキストから取得
    if context:
        try:
            function_arn = context.invoked_function_arn
            if function_arn:
                parts = function_arn.split(':')
                if len(parts) >= 4:
                    region = parts[3]
                    return f"https://execute-api.{region}.amazonaws.com/prod/"
        except:
            pass

    # 5. AWS SDKを使用してCloudFormationから取得
    try:
        import boto3
        cloudformation = boto3.client('cloudformation')
        response = cloudformation.describe_stacks(
            StackName='yfinance-api-stack'
        )
        for output in response['Stacks'][0]['Outputs']:
            if output['OutputKey'] == 'YFinanceApiUrl':
                return output['OutputValue']
    except:
        pass

    # 6. 最後の手段として固定URLを使用
    return 'https://zwtiey61i2.execute-api.ap-northeast-1.amazonaws.com/prod'

def generate_swagger_ui_html(event=None, context=None):
    """Swagger UIのHTMLを生成"""
    # API GatewayのベースURLを動的に取得
    api_url = get_api_gateway_url(event, context)

    # Swagger仕様書のJSON（簡略版）
    swagger_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "YFinance API",
            "description": "YFinanceを使用した株式データ取得API",
            "version": "1.0.0",
            "contact": {
                "name": "YFinance API Support"
            }
        },
        "servers": [
            {
                "url": api_url.rstrip('/'),
                "description": "Production server"
            }
        ],
        "paths": {
            "/search": {
                "get": {
                    "summary": "銘柄検索",
                    "description": "キーワードによる銘柄検索を実行します",
                    "parameters": [
                        {
                            "name": "q",
                            "in": "query",
                            "required": True,
                            "description": "検索キーワード（例: apple, microsoft）",
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "description": "検索結果件数（デフォルト: 10、最大: 10）",
                            "schema": {"type": "integer", "default": 10, "maximum": 10}
                        },
                        {
                            "name": "region",
                            "in": "query",
                            "required": False,
                            "description": "検索リージョン（デフォルト: US）",
                            "schema": {"type": "string", "enum": ["US", "JP"], "default": "US"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "query": {
                                                "type": "string",
                                                "example": "apple",
                                                "description": "検索キーワード"
                                            },
                                            "region": {
                                                "type": "string",
                                                "example": "US",
                                                "description": "検索リージョン"
                                            },
                                            "count": {
                                                "type": "integer",
                                                "example": 7,
                                                "description": "検索結果件数"
                                            },
                                            "results": {
                                                "type": "array",
                                                "description": "検索結果の配列",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "symbol": {
                                                            "type": "string",
                                                            "example": "AAPL",
                                                            "description": "ティッカーシンボル"
                                                        },
                                                        "name": {
                                                            "type": "string",
                                                            "example": "Apple Inc.",
                                                            "description": "企業名"
                                                        },
                                                        "current_price": {
                                                            "type": "number",
                                                            "example": 208.62,
                                                            "description": "現在の株価"
                                                        },
                                                        "price_change_direction": {
                                                            "type": "string",
                                                            "example": "up",
                                                            "description": "価格変化の方向"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/tickerDetail": {
                "get": {
                    "summary": "詳細情報取得（統合版）",
                    "description": "指定されたティッカーシンボルの全ての情報を統合して取得します（価格、履歴、ニュース、配当、オプション、財務、ESG、株主情報など）",
                    "parameters": [
                        {
                            "name": "ticker",
                            "in": "query",
                            "required": True,
                            "description": "ティッカーシンボル（例: AAPL, MSFT, 7203.T）",
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "period",
                            "in": "query",
                            "required": False,
                            "description": "履歴期間（デフォルト: 1mo）",
                            "schema": {
                                "type": "string",
                                "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
                                "default": "1mo"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "ticker": {
                                                "type": "string",
                                                "example": "AAPL",
                                                "description": "ティッカーシンボル"
                                            },
                                            "info": {
                                                "type": "object",
                                                "description": "企業基本情報"
                                            },
                                            "fast_info": {
                                                "type": "object",
                                                "description": "高速取得情報"
                                            },
                                            "price": {
                                                "type": "object",
                                                "description": "株価情報"
                                            },
                                            "history": {
                                                "type": "array",
                                                "description": "株価履歴"
                                            },
                                            "news": {
                                                "type": "array",
                                                "description": "関連ニュース"
                                            },
                                            "dividends": {
                                                "type": "array",
                                                "description": "配当履歴"
                                            },
                                            "options": {
                                                "type": "object",
                                                "description": "オプション情報"
                                            },
                                            "financials": {
                                                "type": "object",
                                                "description": "財務諸表（損益計算書、貸借対照表、キャッシュフロー）"
                                            },
                                            "analysts": {
                                                "type": "object",
                                                "description": "アナリスト予想"
                                            },
                                            "isin": {
                                                "type": "string",
                                                "description": "国際証券識別番号"
                                            },
                                            "recommendations": {
                                                "type": "array",
                                                "description": "アナリスト推奨履歴"
                                            },
                                            "calendar": {
                                                "type": "array",
                                                "description": "イベントカレンダー（決算日など）"
                                            },
                                            "earnings_dates": {
                                                "type": "array",
                                                "description": "過去/未来の決算日"
                                            },
                                            "sustainability": {
                                                "type": "object",
                                                "description": "ESG情報"
                                            },
                                            "holders": {
                                                "type": "object",
                                                "description": "株主情報（大株主、機関投資家、投資信託）"
                                            },
                                            "shares": {
                                                "type": "object",
                                                "description": "株式数詳細"
                                            },
                                            "analysis": {
                                                "type": "object",
                                                "description": "アナリスト分析"
                                            },
                                            "splits": {
                                                "type": "array",
                                                "description": "株式分割履歴"
                                            },
                                            "earnings": {
                                                "type": "object",
                                                "description": "決算情報（EPS、P/E比など）"
                                            },
                                            "upgrades_downgrades": {
                                                "type": "array",
                                                "description": "格付け変更履歴"
                                            },
                                            "execution_info": {
                                                "type": "object",
                                                "description": "実行環境情報"
                                            },
                                            "timestamp": {
                                                "type": "string",
                                                "format": "date-time",
                                                "description": "データ取得時刻"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/chart": {
                "get": {
                    "summary": "チャート画像生成",
                    "description": "指定されたティッカーシンボルの株価チャートを画像で生成します",
                    "parameters": [
                        {
                            "name": "ticker",
                            "in": "query",
                            "required": True,
                            "description": "ティッカーシンボル（例: AAPL, MSFT, 7203.T）",
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "period",
                            "in": "query",
                            "required": False,
                            "description": "期間（デフォルト: 1mo）",
                            "schema": {
                                "type": "string",
                                "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
                                "default": "1mo"
                            }
                        },
                        {
                            "name": "type",
                            "in": "query",
                            "required": False,
                            "description": "チャートタイプ（デフォルト: line）",
                            "schema": {
                                "type": "string",
                                "enum": ["line", "candle"],
                                "default": "line"
                            }
                        },
                        {
                            "name": "size",
                            "in": "query",
                            "required": False,
                            "description": "画像サイズ（デフォルト: 800x400）",
                            "schema": {
                                "type": "string",
                                "default": "800x400"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "成功",
                            "content": {
                                "image/png": {
                                    "schema": {
                                        "type": "string",
                                        "format": "binary"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/ticker/basic": {
                "get": {
                    "summary": "基本情報取得",
                    "description": "指定されたティッカーシンボルの基本情報を取得します",
                    "parameters": [
                        {"name": "ticker", "in": "query", "required": True, "description": "ティッカーシンボル（例: AAPL, MSFT, 7203.T）", "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"ticker": {"type": "string"}, "info": {"type": "object"}, "fast_info": {"type": "object"}, "logo_url": {"type": "string"}, "isin": {"type": "string"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/ticker/price": {
                "get": {
                    "summary": "株価情報取得",
                    "description": "指定されたティッカーシンボルの現在の株価情報を取得します",
                    "parameters": [
                        {"name": "ticker", "in": "query", "required": True, "description": "ティッカーシンボル", "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"ticker": {"type": "string"}, "price": {"type": "object"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/ticker/history": {
                "get": {
                    "summary": "株価履歴取得",
                    "description": "指定されたティッカーシンボルの株価履歴を取得します",
                    "parameters": [
                        {"name": "ticker", "in": "query", "required": True, "description": "ティッカーシンボル", "schema": {"type": "string"}},
                        {"name": "period", "in": "query", "required": False, "description": "履歴期間（デフォルト: 1mo）", "schema": {"type": "string", "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"], "default": "1mo"}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"ticker": {"type": "string"}, "period": {"type": "string"}, "history": {"type": "array"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/ticker/financials": {
                "get": {
                    "summary": "財務情報取得",
                    "description": "指定されたティッカーシンボルの財務諸表・決算情報を取得します",
                    "parameters": [
                        {"name": "ticker", "in": "query", "required": True, "description": "ティッカーシンボル", "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"ticker": {"type": "string"}, "financials": {"type": "object"}, "earnings": {"type": "object"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/ticker/analysts": {
                "get": {
                    "summary": "アナリスト情報取得",
                    "description": "指定されたティッカーシンボルのアナリスト予想・分析情報を取得します",
                    "parameters": [
                        {"name": "ticker", "in": "query", "required": True, "description": "ティッカーシンボル", "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"ticker": {"type": "string"}, "analysts": {"type": "object"}, "recommendations": {"type": "array"}, "analysis": {"type": "object"}, "upgrades_downgrades": {"type": "array"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/ticker/holders": {
                "get": {
                    "summary": "株主情報取得",
                    "description": "指定されたティッカーシンボルの株主情報を取得します",
                    "parameters": [
                        {"name": "ticker", "in": "query", "required": True, "description": "ティッカーシンボル", "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"ticker": {"type": "string"}, "holders": {"type": "object"}, "shares": {"type": "object"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/ticker/events": {
                "get": {
                    "summary": "イベント情報取得",
                    "description": "指定されたティッカーシンボルのイベント情報（決算日、配当、分割など）を取得します",
                    "parameters": [
                        {"name": "ticker", "in": "query", "required": True, "description": "ティッカーシンボル", "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"ticker": {"type": "string"}, "calendar": {"type": "array"}, "earnings_dates": {"type": "array"}, "dividends": {"type": "array"}, "splits": {"type": "array"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/ticker/news": {
                "get": {
                    "summary": "ニュース情報取得",
                    "description": "指定されたティッカーシンボルの関連ニュースを取得します",
                    "parameters": [
                        {"name": "ticker", "in": "query", "required": True, "description": "ティッカーシンボル", "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"ticker": {"type": "string"}, "news": {"type": "array"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/ticker/options": {
                "get": {
                    "summary": "オプション情報取得",
                    "description": "指定されたティッカーシンボルのオプション情報を取得します",
                    "parameters": [
                        {"name": "ticker", "in": "query", "required": True, "description": "ティッカーシンボル", "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"ticker": {"type": "string"}, "options": {"type": "array"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/ticker/sustainability": {
                "get": {
                    "summary": "ESG情報取得",
                    "description": "指定されたティッカーシンボルのESG（環境・社会・ガバナンス）情報を取得します",
                    "parameters": [
                        {"name": "ticker", "in": "query", "required": True, "description": "ティッカーシンボル", "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"ticker": {"type": "string"}, "sustainability": {"type": "object"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/home": {
                "get": {
                    "summary": "ホーム画面情報取得",
                    "description": "株価指数、主要ETF、セクター情報などのホーム画面用情報を取得します",
                    "parameters": [],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"indices": {"type": "object"}, "etfs": {"type": "object"}, "sectors": {"type": "object"}, "execution_info": {"type": "object"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/news/rss": {
                "get": {
                    "summary": "Yahoo Finance RSSニュース取得",
                    "description": "Yahoo FinanceのRSSフィードから最新ニュースを取得します",
                    "parameters": [
                        {"name": "limit", "in": "query", "required": False, "description": "取得件数（デフォルト10）", "schema": {"type": "integer", "default": 10}}
                    ],
                    "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object", "properties": {"status": {"type": "string"}, "data": {"type": "array"}, "count": {"type": "integer"}, "timestamp": {"type": "string", "format": "date-time"}}}}}}}
                }
            },
            "/rankings/stocks": {
                "get": {
                    "summary": "株価関連ランキング取得",
                    "description": "指定された市場の株価関連ランキングを取得します",
                    "parameters": [
                        {"name": "type", "in": "query", "required": True, "description": "ランキング種別（例: gainers, losers, volume, market-cap）", "schema": {"type": "string", "enum": ["gainers", "losers", "volume", "market-cap"]}},
                        {"name": "market", "in": "query", "required": True, "description": "市場（例: sp500, nasdaq100）", "schema": {"type": "string", "enum": ["sp500", "nasdaq100"]}},
                        {"name": "limit", "in": "query", "required": False, "description": "取得件数（デフォルト: 10、最大: 50）", "schema": {"type": "integer", "default": 10, "maximum": 50}}
                    ],
                    "responses": {
                        "200": {
                            "description": "成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {
                                                "type": "string",
                                                "description": "ステータス"
                                            },
                                            "type": {
                                                "type": "string",
                                                "description": "ランキング種別"
                                            },
                                            "market": {
                                                "type": "string",
                                                "description": "市場"
                                            },
                                            "data": {
                                                "type": "array",
                                                "description": "ランキングデータ",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "symbol": {
                                                            "type": "string",
                                                            "description": "銘柄シンボル"
                                                        },
                                                        "name": {
                                                            "type": "string",
                                                            "description": "銘柄名"
                                                        },
                                                        "current_price": {
                                                            "type": "number",
                                                            "description": "現在の株価"
                                                        },
                                                        "previous_close": {
                                                            "type": "number",
                                                            "description": "前日の終値"
                                                        },
                                                        "price_change": {
                                                            "type": "number",
                                                            "description": "価格変化"
                                                        },
                                                        "price_change_percent": {
                                                            "type": "number",
                                                            "description": "価格変化率"
                                                        },
                                                        "volume": {
                                                            "type": "integer",
                                                            "description": "出来高"
                                                        },
                                                        "market_cap": {
                                                            "type": "integer",
                                                            "description": "時価総額"
                                                        },
                                                        "currency": {
                                                            "type": "string",
                                                            "description": "通貨コード"
                                                        }
                                                    }
                                                }
                                            },
                                            "chart_image": {
                                                "type": "string",
                                                "description": "ランキングチャート画像"
                                            },
                                            "metadata": {
                                                "type": "object",
                                                "properties": {
                                                    "total_stocks": {
                                                        "type": "integer",
                                                        "description": "ランキング銘柄数"
                                                    },
                                                    "limit": {
                                                        "type": "integer",
                                                        "description": "取得件数"
                                                    },
                                                    "last_updated": {
                                                        "type": "string",
                                                        "format": "date-time",
                                                        "description": "最終更新日時"
                                                    }
                                                }
                                            },
                                            "execution_info": {
                                                "type": "object",
                                                "description": "実行環境情報"
                                            },
                                            "timestamp": {
                                                "type": "string",
                                                "format": "date-time",
                                                "description": "データ取得日時"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/rankings/sectors": {
                "get": {
                    "summary": "セクター・業界ランキング取得",
                    "description": "指定されたセクターの業界ランキングを取得します",
                    "parameters": [
                        {"name": "type", "in": "query", "required": True, "description": "ランキング種別（例: performance, constituent）", "schema": {"type": "string", "enum": ["performance", "constituent"]}},
                        {"name": "sector", "in": "query", "required": True, "description": "セクター（例: XLK, XLF）", "schema": {"type": "string", "enum": ["XLK", "XLF", "XLE", "XLV", "XLI", "XLP", "XLY", "XLU", "XLRE"]}},
                        {"name": "limit", "in": "query", "required": False, "description": "取得件数（デフォルト: 10、最大: 20）", "schema": {"type": "integer", "default": 10, "maximum": 20}}
                    ],
                    "responses": {
                        "200": {
                            "description": "成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {
                                                "type": "string",
                                                "description": "ステータス"
                                            },
                                            "type": {
                                                "type": "string",
                                                "description": "ランキング種別"
                                            },
                                            "sector": {
                                                "type": "string",
                                                "description": "セクター"
                                            },
                                            "data": {
                                                "type": "array",
                                                "description": "ランキングデータ",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "symbol": {
                                                            "type": "string",
                                                            "description": "銘柄シンボル"
                                                        },
                                                        "name": {
                                                            "type": "string",
                                                            "description": "銘柄名"
                                                        },
                                                        "current_price": {
                                                            "type": "number",
                                                            "description": "現在の株価"
                                                        },
                                                        "previous_close": {
                                                            "type": "number",
                                                            "description": "前日の終値"
                                                        },
                                                        "price_change": {
                                                            "type": "number",
                                                            "description": "価格変化"
                                                        },
                                                        "price_change_percent": {
                                                            "type": "number",
                                                            "description": "価格変化率"
                                                        },
                                                        "constituent_change_avg": {
                                                            "type": "number",
                                                            "description": "構成銘柄平均変化率"
                                                        },
                                                        "constituent_count": {
                                                            "type": "integer",
                                                            "description": "構成銘柄数"
                                                        },
                                                        "currency": {
                                                            "type": "string",
                                                            "description": "通貨コード"
                                                        }
                                                    }
                                                }
                                            },
                                            "chart_image": {
                                                "type": "string",
                                                "description": "ランキングチャート画像"
                                            },
                                            "metadata": {
                                                "type": "object",
                                                "properties": {
                                                    "total_sectors": {
                                                        "type": "integer",
                                                        "description": "ランキングセクター数"
                                                    },
                                                    "limit": {
                                                        "type": "integer",
                                                        "description": "取得件数"
                                                    },
                                                    "last_updated": {
                                                        "type": "string",
                                                        "format": "date-time",
                                                        "description": "最終更新日時"
                                                    }
                                                }
                                            },
                                            "execution_info": {
                                                "type": "object",
                                                "description": "実行環境情報"
                                            },
                                            "timestamp": {
                                                "type": "string",
                                                "format": "date-time",
                                                "description": "データ取得日時"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/rankings/crypto": {
                "get": {
                    "summary": "暗号通貨ランキング取得",
                    "description": "指定された暗号通貨のランキングを取得します",
                    "parameters": [
                        {"name": "limit", "in": "query", "required": True, "description": "取得件数（デフォルト: 10、最大: 20）", "schema": {"type": "integer", "default": 10, "maximum": 20}},
                        {"name": "sort", "in": "query", "required": False, "description": "ソート基準（デフォルト: change、選択可能: change, price, volume, market_cap）", "schema": {"type": "string", "enum": ["change", "price", "volume", "market_cap"]}}
                    ],
                    "responses": {
                        "200": {
                            "description": "成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {
                                                "type": "string",
                                                "description": "ステータス"
                                            },
                                            "type": {
                                                "type": "string",
                                                "description": "ランキング種別"
                                            },
                                            "data": {
                                                "type": "array",
                                                "description": "ランキングデータ",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "symbol": {
                                                            "type": "string",
                                                            "description": "銘柄シンボル"
                                                        },
                                                        "name": {
                                                            "type": "string",
                                                            "description": "銘柄名"
                                                        },
                                                        "price": {
                                                            "type": "number",
                                                            "description": "現在の価格"
                                                        },
                                                        "change": {
                                                            "type": "number",
                                                            "description": "価格変化"
                                                        },
                                                        "change_percent": {
                                                            "type": "number",
                                                            "description": "価格変化率"
                                                        },
                                                        "volume": {
                                                            "type": "integer",
                                                            "description": "出来高"
                                                        },
                                                        "market_cap": {
                                                            "type": "integer",
                                                            "description": "時価総額"
                                                        },
                                                        "rank": {
                                                            "type": "integer",
                                                            "description": "ランク"
                                                        }
                                                    }
                                                }
                                            },
                                            "metadata": {
                                                "type": "object",
                                                "properties": {
                                                    "total_cryptos": {
                                                        "type": "integer",
                                                        "description": "ランキング銘柄数"
                                                    },
                                                    "limit": {
                                                        "type": "integer",
                                                        "description": "取得件数"
                                                    },
                                                    "sort_by": {
                                                        "type": "string",
                                                        "description": "ソート基準"
                                                    },
                                                    "last_updated": {
                                                        "type": "string",
                                                        "format": "date-time",
                                                        "description": "最終更新日時"
                                                    }
                                                }
                                            },
                                            "execution_info": {
                                                "type": "object",
                                                "description": "実行環境情報"
                                            },
                                            "timestamp": {
                                                "type": "string",
                                                "format": "date-time",
                                                "description": "データ取得日時"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/markets/indices": {
                "get": {
                    "summary": "主要指数一覧取得",
                    "description": "指定された主要指数の一覧を取得します",
                    "parameters": [
                        {"name": "limit", "in": "query", "required": False, "description": "取得件数（デフォルト: 10、最大: 20）", "schema": {"type": "integer", "default": 10, "maximum": 20}}
                    ],
                    "responses": {
                        "200": {
                            "description": "成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {
                                                "type": "string",
                                                "description": "ステータス"
                                            },
                                            "type": {
                                                "type": "string",
                                                "description": "ランキング種別"
                                            },
                                            "data": {
                                                "type": "array",
                                                "description": "ランキングデータ",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "name": {
                                                            "type": "string",
                                                            "description": "指数名"
                                                        },
                                                        "symbol": {
                                                            "type": "string",
                                                            "description": "指数シンボル"
                                                        },
                                                        "value": {
                                                            "type": "number",
                                                            "description": "現在の値"
                                                        },
                                                        "change": {
                                                            "type": "number",
                                                            "description": "価格変化"
                                                        },
                                                        "change_percent": {
                                                            "type": "number",
                                                            "description": "価格変化率"
                                                        },
                                                        "volume": {
                                                            "type": "integer",
                                                            "description": "出来高"
                                                        },
                                                        "rank": {
                                                            "type": "integer",
                                                            "description": "ランク"
                                                        }
                                                    }
                                                }
                                            },
                                            "metadata": {
                                                "type": "object",
                                                "properties": {
                                                    "total_indices": {
                                                        "type": "integer",
                                                        "description": "ランキング銘柄数"
                                                    },
                                                    "limit": {
                                                        "type": "integer",
                                                        "description": "取得件数"
                                                    },
                                                    "last_updated": {
                                                        "type": "string",
                                                        "format": "date-time",
                                                        "description": "最終更新日時"
                                                    }
                                                }
                                            },
                                            "execution_info": {
                                                "type": "object",
                                                "description": "実行環境情報"
                                            },
                                            "timestamp": {
                                                "type": "string",
                                                "format": "date-time",
                                                "description": "データ取得日時"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/markets/currencies": {
                "get": {
                    "summary": "為替レート取得",
                    "description": "指定された通貨ペアの為替レートを取得します",
                    "parameters": [
                        {"name": "limit", "in": "query", "required": False, "description": "取得件数（デフォルト: 10、最大: 20）", "schema": {"type": "integer", "default": 10, "maximum": 20}}
                    ],
                    "responses": {
                        "200": {
                            "description": "成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {
                                                "type": "string",
                                                "description": "ステータス"
                                            },
                                            "type": {
                                                "type": "string",
                                                "description": "ランキング種別"
                                            },
                                            "data": {
                                                "type": "array",
                                                "description": "ランキングデータ",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "pair": {
                                                            "type": "string",
                                                            "description": "通貨ペア"
                                                        },
                                                        "symbol": {
                                                            "type": "string",
                                                            "description": "通貨シンボル"
                                                        },
                                                        "rate": {
                                                            "type": "number",
                                                            "description": "レート"
                                                        },
                                                        "change": {
                                                            "type": "number",
                                                            "description": "変化"
                                                        },
                                                        "change_percent": {
                                                            "type": "number",
                                                            "description": "変化率"
                                                        },
                                                        "rank": {
                                                            "type": "integer",
                                                            "description": "ランク"
                                                        }
                                                    }
                                                }
                                            },
                                            "metadata": {
                                                "type": "object",
                                                "properties": {
                                                    "total_pairs": {
                                                        "type": "integer",
                                                        "description": "ランキング銘柄数"
                                                    },
                                                    "limit": {
                                                        "type": "integer",
                                                        "description": "取得件数"
                                                    },
                                                    "last_updated": {
                                                        "type": "string",
                                                        "format": "date-time",
                                                        "description": "最終更新日時"
                                                    }
                                                }
                                            },
                                            "execution_info": {
                                                "type": "object",
                                                "description": "実行環境情報"
                                            },
                                            "timestamp": {
                                                "type": "string",
                                                "format": "date-time",
                                                "description": "データ取得日時"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/markets/commodities": {
                "get": {
                    "summary": "商品価格取得",
                    "description": "指定された商品の価格を取得します",
                    "parameters": [
                        {"name": "limit", "in": "query", "required": False, "description": "取得件数（デフォルト: 10、最大: 20）", "schema": {"type": "integer", "default": 10, "maximum": 20}}
                    ],
                    "responses": {
                        "200": {
                            "description": "成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {
                                                "type": "string",
                                                "description": "ステータス"
                                            },
                                            "type": {
                                                "type": "string",
                                                "description": "ランキング種別"
                                            },
                                            "data": {
                                                "type": "array",
                                                "description": "ランキングデータ",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "name": {
                                                            "type": "string",
                                                            "description": "商品名"
                                                        },
                                                        "symbol": {
                                                            "type": "string",
                                                            "description": "商品シンボル"
                                                        },
                                                        "price": {
                                                            "type": "number",
                                                            "description": "現在の価格"
                                                        },
                                                        "change": {
                                                            "type": "number",
                                                            "description": "価格変化"
                                                        },
                                                        "change_percent": {
                                                            "type": "number",
                                                            "description": "価格変化率"
                                                        },
                                                        "volume": {
                                                            "type": "integer",
                                                            "description": "出来高"
                                                        },
                                                        "rank": {
                                                            "type": "integer",
                                                            "description": "ランク"
                                                        }
                                                    }
                                                }
                                            },
                                            "metadata": {
                                                "type": "object",
                                                "properties": {
                                                    "total_commodities": {
                                                        "type": "integer",
                                                        "description": "ランキング銘柄数"
                                                    },
                                                    "limit": {
                                                        "type": "integer",
                                                        "description": "取得件数"
                                                    },
                                                    "last_updated": {
                                                        "type": "string",
                                                        "format": "date-time",
                                                        "description": "最終更新日時"
                                                    }
                                                }
                                            },
                                            "execution_info": {
                                                "type": "object",
                                                "description": "実行環境情報"
                                            },
                                            "timestamp": {
                                                "type": "string",
                                                "format": "date-time",
                                                "description": "データ取得日時"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/markets/status": {
                "get": {
                    "summary": "市場開閉状況取得",
                    "description": "指定された市場の開閉状況を取得します",
                    "parameters": [
                        {"name": "limit", "in": "query", "required": False, "description": "取得件数（デフォルト: 10、最大: 20）", "schema": {"type": "integer", "default": 10, "maximum": 20}}
                    ],
                    "responses": {
                        "200": {
                            "description": "成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {
                                                "type": "string",
                                                "description": "ステータス"
                                            },
                                            "data": {
                                                "type": "array",
                                                "description": "市場開閉状況データ",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "market": {
                                                            "type": "string",
                                                            "description": "市場名"
                                                        },
                                                        "timezone": {
                                                            "type": "string",
                                                            "description": "タイムゾーン"
                                                        },
                                                        "local_time": {
                                                            "type": "string",
                                                            "format": "date-time",
                                                            "description": "現地時間"
                                                        },
                                                        "is_open": {
                                                            "type": "boolean",
                                                            "description": "市場が開いているか"
                                                        },
                                                        "is_business_day": {
                                                            "type": "boolean",
                                                            "description": "営業日か"
                                                        },
                                                        "open_time": {
                                                            "type": "string",
                                                            "format": "time",
                                                            "description": "市場開始時間"
                                                        },
                                                        "close_time": {
                                                            "type": "string",
                                                            "format": "time",
                                                            "description": "市場終了時間"
                                                        },
                                                        "rank": {
                                                            "type": "integer",
                                                            "description": "ランク"
                                                        }
                                                    }
                                                }
                                            },
                                            "metadata": {
                                                "type": "object",
                                                "properties": {
                                                    "total_markets": {
                                                        "type": "integer",
                                                        "description": "ランキング銘柄数"
                                                    },
                                                    "limit": {
                                                        "type": "integer",
                                                        "description": "取得件数"
                                                    },
                                                    "last_updated": {
                                                        "type": "string",
                                                        "format": "date-time",
                                                        "description": "最終更新日時"
                                                    }
                                                }
                                            },
                                            "execution_info": {
                                                "type": "object",
                                                "description": "実行環境情報"
                                            },
                                            "timestamp": {
                                                "type": "string",
                                                "format": "date-time",
                                                "description": "データ取得日時"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    # Swagger UIのHTML
    html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YFinance API - Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}
        *, *:before, *:after {{
            box-sizing: inherit;
        }}
        body {{
            margin:0;
            background: #fafafa;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                spec: {json.dumps(swagger_spec)},
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            }});
        }};
    </script>
</body>
</html>
"""
    return html

def get_stock_chart_api(ticker, period='1mo', size='800x400', chart_type='line'):
    """株価チャート画像を生成し base64 文字列で返却する。エラー時は (None, error) を返す"""
    try:
        import matplotlib
        matplotlib.use('Agg')  # バックエンドを非GUIに
        import matplotlib.pyplot as plt
        from io import BytesIO
        import base64

        # サイズ解析
        try:
            width, height = map(int, size.lower().split('x'))
        except Exception:
            width, height = 800, 400

        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty:
            return None, f'履歴データが取得できませんでした: {ticker}'

        if chart_type == 'candle' and 'Open' in hist.columns:
            # ローソク足（新しいmplfinance API使用）
            try:
                import mplfinance as mpf
                buf = BytesIO()
                mpf.plot(hist, type='candle', style='charles',
                        figsize=(width/100, height/100),
                        title=f'{ticker} {period} candlestick',
                        savefig=dict(fname=buf, format='png', dpi=100))
                buf.seek(0)
                img_base64 = base64.b64encode(buf.read()).decode('utf-8')
                return img_base64, None
            except Exception:
                # フォールバック: 折れ線グラフ
                pass

        # 折れ線グラフ（デフォルトまたはフォールバック）
        plt.figure(figsize=(width/100, height/100))
        plt.plot(hist.index, hist['Close'], label='Close')
        plt.title(f'{ticker} {period} close price')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.tight_layout()

        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return img_base64, None
    except Exception as e:
        return None, str(e)

def clean_html(text):
    if not text:
        return ""
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    text = ' '.join(text.split())
    return text

def generate_news_id(title, url):
    content = f"{title}_{url}".encode('utf-8')
    return hashlib.md5(content).hexdigest()[:12]

def parse_published_date(entry):
    published_date = None
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        try:
            published_date = datetime(*entry.published_parsed[:6])
        except:
            pass
    if not published_date and hasattr(entry, 'published'):
        try:
            published_date = entry.published
        except:
            pass
    if not published_date and hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        try:
            published_date = datetime(*entry.updated_parsed[:6])
        except:
            pass
    return published_date

def fetch_rss_feed(source):
    try:
        feed = feedparser.parse(source['url'])
        articles = []
        for entry in feed.entries:
            title = clean_html(entry.get('title', ''))
            if not title:
                continue
            url = entry.get('link', '')
            summary = clean_html(entry.get('summary', entry.get('description', '')))
            published_date = parse_published_date(entry)
            author = entry.get('author', '')
            image_url = None
            if hasattr(entry, 'media_content'):
                for media in entry.media_content:
                    if media.get('type', '').startswith('image'):
                        image_url = media.get('url')
                        break
            if not image_url and hasattr(entry, 'enclosures'):
                for enclosure in entry.enclosures:
                    if enclosure.type.startswith('image'):
                        image_url = enclosure.href
                        break
            tags = []
            if hasattr(entry, 'tags'):
                tags = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
            article = {
                'id': generate_news_id(title, url),
                'title': title,
                'summary': summary[:500] + '...' if len(summary) > 500 else summary,
                'url': url,
                'source': source['name'],
                'category': source['category'],
                'published_at': published_date.isoformat() if isinstance(published_date, datetime) else published_date,
                'author': author,
                'image_url': image_url,
                'tags': tags
            }
            articles.append(article)
        return articles
    except Exception as e:
        return []

def lamuda_get_rss_news_api(query_parameters):
    category = query_parameters.get('category', 'all')
    source_filter = query_parameters.get('source', '')
    limit = min(int(query_parameters.get('limit', 50)), 200)
    sort = query_parameters.get('sort', 'published_desc')
    target_sources = RSS_SOURCES
    if category != 'all':
        target_sources = [s for s in target_sources if s['category'] == category]
    if source_filter:
        target_sources = [s for s in target_sources if source_filter.lower() in s['name'].lower()]
    all_articles = []
    for source in target_sources:
        all_articles.extend(fetch_rss_feed(source))
    unique_articles = {}
    for article in all_articles:
        title_key = article['title'].lower().strip()
        if title_key not in unique_articles:
            unique_articles[title_key] = article
        else:
            existing = unique_articles[title_key]
            if article['published_at'] and existing['published_at']:
                try:
                    if isinstance(article['published_at'], str):
                        article_date = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))
                    else:
                        article_date = article['published_at']
                    if isinstance(existing['published_at'], str):
                        existing_date = datetime.fromisoformat(existing['published_at'].replace('Z', '+00:00'))
                    else:
                        existing_date = existing['published_at']
                    if article_date > existing_date:
                        unique_articles[title_key] = article
                except:
                    pass
    final_articles = list(unique_articles.values())
    try:
        if sort == 'published_desc':
            final_articles.sort(key=lambda x: x['published_at'] or '', reverse=True)
        elif sort == 'published_asc':
            final_articles.sort(key=lambda x: x['published_at'] or '')
        elif sort == 'title_asc':
            final_articles.sort(key=lambda x: x['title'].lower())
    except Exception:
        pass
    final_articles = final_articles[:limit]
    return {
        'status': 'success',
        'data': final_articles,
        'metadata': {
            'total_sources': len(target_sources),
            'total_articles': len(final_articles),
            'sources_used': [s['name'] for s in target_sources],
            'category_filter': category,
            'source_filter': source_filter,
            'sort': sort,
            'last_updated': datetime.now().isoformat()
        },
        'timestamp': datetime.now().isoformat()
    }

def get_stock_rankings_api(query_parameters):
    """株価関連ランキング取得API（改善版）"""
    try:
        ranking_type = query_parameters.get('type', 'gainers')
        limit = min(int(query_parameters.get('limit', 10)), 50)
        market = query_parameters.get('market', 'us')

        # 主要銘柄から取得
        stocks = get_multiple_stock_data(MAJOR_STOCKS)

        if ranking_type == 'gainers':
            # 上昇銘柄のみフィルタ
            rankings = [stock for stock in stocks if stock['change_percent'] > 0]
            rankings.sort(key=lambda x: x['change_percent'], reverse=True)
        elif ranking_type == 'losers':
            # 下落銘柄のみフィルタ
            rankings = [stock for stock in stocks if stock['change_percent'] < 0]
            rankings.sort(key=lambda x: x['change_percent'])
        elif ranking_type == 'volume':
            # 出来高でソート
            rankings = stocks
            rankings.sort(key=lambda x: x['volume'], reverse=True)
        elif ranking_type == 'market-cap':
            # 時価総額データがある銘柄のみ
            rankings = [stock for stock in stocks if stock.get('market_cap')]
            rankings.sort(key=lambda x: x['market_cap'], reverse=True)
        else:
            return {'error': f'無効なランキング種別: {ranking_type}'}

        # 制限数で切り取り
        rankings = rankings[:limit]

        # ランク付け
        for i, stock in enumerate(rankings):
            stock['rank'] = i + 1

        # 画像生成
        chart_image = generate_ranking_chart(rankings, ranking_type)

        return {
            'status': 'success',
            'type': ranking_type,
            'market': market,
            'data': rankings,
            'chart_image': chart_image,
            'metadata': {
                'total_stocks': len(rankings),
                'limit': limit,
                'last_updated': datetime.now().isoformat()
            },
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {'error': f'ランキング取得エラー: {str(e)}'}

def get_sector_rankings_api(query_parameters):
    """セクター・業界ランキング取得API（改善版）"""
    try:
        limit = min(int(query_parameters.get('limit', 10)), 20)

        sector_data = []

        for sector_name, etf_symbol in SECTOR_ETFS.items():
            try:
                ticker = yf.Ticker(etf_symbol)
                hist = ticker.history(period="2d")
                info = ticker.info

                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    change = current_price - prev_price
                    change_percent = (change / prev_price) * 100

                    sector_data.append({
                        'sector': sector_name,
                        'symbol': etf_symbol,
                        'name': info.get('longName', f'{sector_name} Sector ETF'),
                        'price': round(float(current_price), 2),
                        'change': round(float(change), 2),
                        'change_percent': round(float(change_percent), 2),
                        'volume': int(hist['Volume'].iloc[-1]) if hist['Volume'].iloc[-1] else 0
                    })
            except Exception as e:
                continue

        # パフォーマンス順でソート
        sector_data.sort(key=lambda x: x['change_percent'], reverse=True)

        # ランク付け
        for i, sector in enumerate(sector_data[:limit]):
            sector['rank'] = i + 1

        # 画像生成
        chart_image = generate_sector_chart(sector_data[:limit], 'performance')

        return {
            'status': 'success',
            'type': 'performance',
            'data': sector_data[:limit],
            'chart_image': chart_image,
            'metadata': {
                'total_sectors': len(sector_data),
                'limit': limit,
                'last_updated': datetime.now().isoformat()
            },
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {'error': f'セクターランキング取得エラー: {str(e)}'}

def get_crypto_rankings_api(query_parameters):
    """暗号通貨ランキング取得API"""
    try:
        limit = min(int(query_parameters.get('limit', 10)), 20)
        sort_by = query_parameters.get('sort', 'change')  # change, price, volume, market_cap

        crypto_data = []

        for symbol in CRYPTO_SYMBOLS:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                info = ticker.info

                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    change = current_price - prev_price
                    change_percent = (change / prev_price) * 100

                    crypto_data.append({
                        'symbol': symbol,
                        'name': symbol.replace('-USD', ''),
                        'price': round(float(current_price), 2),
                        'change': round(float(change), 2),
                        'change_percent': round(float(change_percent), 2),
                        'volume': int(hist['Volume'].iloc[-1]) if hist['Volume'].iloc[-1] else 0,
                        'market_cap': info.get('marketCap')
                    })
            except Exception as e:
                continue

        # ソート
        if sort_by == 'change':
            crypto_data.sort(key=lambda x: x['change_percent'], reverse=True)
        elif sort_by == 'price':
            crypto_data.sort(key=lambda x: x['price'], reverse=True)
        elif sort_by == 'volume':
            crypto_data.sort(key=lambda x: x['volume'], reverse=True)
        elif sort_by == 'market_cap':
            crypto_data = [c for c in crypto_data if c.get('market_cap')]
            crypto_data.sort(key=lambda x: x['market_cap'], reverse=True)

        # ランク付け
        for i, crypto in enumerate(crypto_data[:limit]):
            crypto['rank'] = i + 1

        return {
            'status': 'success',
            'type': 'crypto',
            'data': crypto_data[:limit],
            'metadata': {
                'sort_by': sort_by,
                'total_cryptos': len(crypto_data),
                'last_updated': datetime.now().isoformat()
            },
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {'error': f'暗号通貨ランキング取得エラー: {str(e)}'}

def get_markets_indices_api(query_parameters):
    """主要指数一覧取得API"""
    try:
        indices_data = []

        for index_name, symbol in MAJOR_INDICES.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")

                if len(hist) >= 2:
                    current_value = hist['Close'].iloc[-1]
                    prev_value = hist['Close'].iloc[-2]
                    change = current_value - prev_value
                    change_percent = (change / prev_value) * 100

                    indices_data.append({
                        'name': index_name,
                        'symbol': symbol,
                        'value': round(float(current_value), 2),
                        'change': round(float(change), 2),
                        'change_percent': round(float(change_percent), 2),
                        'volume': int(hist['Volume'].iloc[-1]) if hist['Volume'].iloc[-1] else 0
                    })
            except Exception as e:
                continue

        return {
            'status': 'success',
            'data': indices_data,
            'metadata': {
                'total_indices': len(indices_data),
                'last_updated': datetime.now().isoformat()
            },
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {'error': f'指数データ取得エラー: {str(e)}'}

def get_markets_currencies_api(query_parameters):
    """為替レート取得API"""
    try:
        currency_data = []

        for pair_name, symbol in CURRENCY_PAIRS.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")

                if len(hist) >= 2:
                    current_rate = hist['Close'].iloc[-1]
                    prev_rate = hist['Close'].iloc[-2]
                    change = current_rate - prev_rate
                    change_percent = (change / prev_rate) * 100

                    currency_data.append({
                        'pair': pair_name,
                        'symbol': symbol,
                        'rate': round(float(current_rate), 4),
                        'change': round(float(change), 4),
                        'change_percent': round(float(change_percent), 2)
                    })
            except Exception as e:
                continue

        return {
            'status': 'success',
            'data': currency_data,
            'metadata': {
                'total_pairs': len(currency_data),
                'last_updated': datetime.now().isoformat()
            },
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {'error': f'為替データ取得エラー: {str(e)}'}

def get_markets_commodities_api(query_parameters):
    """商品価格取得API"""
    try:
        commodity_data = []

        for commodity_name, symbol in COMMODITIES.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")

                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    change = current_price - prev_price
                    change_percent = (change / prev_price) * 100

                    commodity_data.append({
                        'name': commodity_name,
                        'symbol': symbol,
                        'price': round(float(current_price), 2),
                        'change': round(float(change), 2),
                        'change_percent': round(float(change_percent), 2),
                        'volume': int(hist['Volume'].iloc[-1]) if hist['Volume'].iloc[-1] else 0
                    })
            except Exception as e:
                continue

        return {
            'status': 'success',
            'data': commodity_data,
            'metadata': {
                'total_commodities': len(commodity_data),
                'last_updated': datetime.now().isoformat()
            },
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {'error': f'商品データ取得エラー: {str(e)}'}

def get_markets_status_api(query_parameters):
    """市場開閉状況取得API"""
    try:
        # 主要市場の営業時間
        markets = [
            {
                'name': 'NYSE/NASDAQ',
                'timezone': 'US/Eastern',
                'open_time': '09:30',
                'close_time': '16:00',
                'days': [0, 1, 2, 3, 4]  # Monday-Friday
            },
            {
                'name': 'Tokyo Stock Exchange',
                'timezone': 'Asia/Tokyo',
                'open_time': '09:00',
                'close_time': '15:00',
                'days': [0, 1, 2, 3, 4]
            },
            {
                'name': 'London Stock Exchange',
                'timezone': 'Europe/London',
                'open_time': '08:00',
                'close_time': '16:30',
                'days': [0, 1, 2, 3, 4]
            }
        ]

        market_status = []

        for market in markets:
            try:
                # 簡易的な時間計算（pytzなし）
                from datetime import datetime, timedelta
                import time

                # UTC時間を取得
                utc_now = datetime.utcnow()

                # タイムゾーンオフセット（簡易版）
                tz_offsets = {
                    'US/Eastern': -5,
                    'Asia/Tokyo': 9,
                    'Europe/London': 0
                }

                offset = tz_offsets.get(market['timezone'], 0)
                local_time = utc_now + timedelta(hours=offset)

                # 現在の曜日が営業日かチェック
                is_business_day = local_time.weekday() in market['days']

                # 営業時間内かチェック
                open_time = datetime.strptime(market['open_time'], '%H:%M').time()
                close_time = datetime.strptime(market['close_time'], '%H:%M').time()

                is_open = (is_business_day and
                          open_time <= local_time.time() <= close_time)

                market_status.append({
                    'market': market['name'],
                    'timezone': market['timezone'],
                    'local_time': local_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'is_open': is_open,
                    'is_business_day': is_business_day,
                    'open_time': market['open_time'],
                    'close_time': market['close_time']
                })

            except Exception as e:
                continue

        return {
            'status': 'success',
            'data': market_status,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {'error': f'市場状況取得エラー: {str(e)}'}

def safe_get_stock_data(symbol):
    """安全に株価データを取得"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d")
        info = ticker.info

        if len(hist) < 2:
            return None

        current_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2]
        change = current_price - prev_price
        change_percent = (change / prev_price) * 100

        return {
            'symbol': symbol,
            'name': info.get('longName', info.get('shortName', symbol)),
            'price': round(float(current_price), 2),
            'change': round(float(change), 2),
            'change_percent': round(float(change_percent), 2),
            'volume': int(hist['Volume'].iloc[-1]) if hist['Volume'].iloc[-1] else 0,
            'market_cap': info.get('marketCap'),
            'sector': info.get('sector', 'Unknown')
        }
    except Exception as e:
        return None

def get_multiple_stock_data(symbols):
    """複数銘柄のデータを効率的に取得"""
    try:
        # yfinanceで複数銘柄を一度に取得
        tickers = yf.Tickers(' '.join(symbols))

        results = []
        for symbol in symbols:
            try:
                ticker = tickers.tickers[symbol]
                hist = ticker.history(period="2d")
                info = ticker.info

                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    change = current_price - prev_price
                    change_percent = (change / prev_price) * 100

                    data = {
                        'symbol': symbol,
                        'name': info.get('longName', info.get('shortName', symbol)),
                        'price': round(float(current_price), 2),
                        'change': round(float(change), 2),
                        'change_percent': round(float(change_percent), 2),
                        'volume': int(hist['Volume'].iloc[-1]) if hist['Volume'].iloc[-1] else 0,
                        'market_cap': info.get('marketCap'),
                        'sector': info.get('sector', 'Unknown')
                    }
                    results.append(data)
            except Exception as e:
                continue

        return results
    except Exception as e:
        # フォールバック: 個別取得
        results = []
        for symbol in symbols:
            data = safe_get_stock_data(symbol)
            if data:
                results.append(data)
        return results

def generate_ranking_chart(rankings, ranking_type):
    """ランキングチャート画像生成"""
    try:
        if not rankings:
            return None

        plt.figure(figsize=(12, 8))

        symbols = [item['symbol'] for item in rankings]
        values = []

        if ranking_type in ['gainers', 'losers']:
            values = [item['price_change_percent'] for item in rankings]
            ylabel = 'Price Change (%)'
            title = f'Top {len(rankings)} {ranking_type.title()}'
        elif ranking_type == 'volume':
            values = [item['volume'] / 1000000 for item in rankings]  # 百万単位
            ylabel = 'Volume (Millions)'
            title = f'Top {len(rankings)} Volume Leaders'
        elif ranking_type == 'market-cap':
            values = [item['market_cap'] / 1000000000 for item in rankings]  # 十億単位
            ylabel = 'Market Cap (Billions)'
            title = f'Top {len(rankings)} Market Cap Leaders'

        colors = ['green' if x >= 0 else 'red' for x in values] if ranking_type in ['gainers', 'losers'] else ['blue'] * len(values)

        bars = plt.barh(symbols, values, color=colors)
        plt.xlabel(ylabel)
        plt.title(title)
        plt.gca().invert_yaxis()

        # 値ラベルを追加
        for i, (bar, value) in enumerate(zip(bars, values)):
            plt.text(bar.get_width() + (max(values) * 0.01), bar.get_y() + bar.get_height()/2,
                    f'{value:.1f}', va='center')

        plt.tight_layout()

        # 画像をBase64エンコード
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')

        return img_base64

    except Exception as e:
        return None

def generate_sector_chart(sector_data, ranking_type):
    """セクターランキングチャート画像生成"""
    try:
        if not sector_data:
            return None

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

        sectors = [item['name'] for item in sector_data]
        etf_values = [item['price_change_percent'] for item in sector_data]
        constituent_values = [item['constituent_change_avg'] for item in sector_data]

        # ETFパフォーマンス
        colors1 = ['green' if x >= 0 else 'red' for x in etf_values]
        bars1 = ax1.barh(sectors, etf_values, color=colors1)
        ax1.set_xlabel('ETF Price Change (%)')
        ax1.set_title('Sector ETF Performance')
        ax1.invert_yaxis()

        # 構成銘柄平均パフォーマンス
        colors2 = ['green' if x >= 0 else 'red' for x in constituent_values]
        bars2 = ax2.barh(sectors, constituent_values, color=colors2)
        ax2.set_xlabel('Constituent Average Change (%)')
        ax2.set_title('Sector Constituent Performance')
        ax2.invert_yaxis()

        # 値ラベルを追加
        for bar, value in zip(bars1, etf_values):
            ax1.text(bar.get_width() + (max(etf_values) * 0.01), bar.get_y() + bar.get_height()/2,
                    f'{value:.1f}', va='center')

        for bar, value in zip(bars2, constituent_values):
            ax2.text(bar.get_width() + (max(constituent_values) * 0.01), bar.get_y() + bar.get_height()/2,
                    f'{value:.1f}', va='center')

        plt.tight_layout()

        # 画像をBase64エンコード
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')

        return img_base64

    except Exception as e:
        return None
