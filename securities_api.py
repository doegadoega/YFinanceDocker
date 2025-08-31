#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import uuid

from botocore.exceptions import ClientError

# 既存のユーザー管理・JWT・DynamoDBユーティリティを再利用
from lambda_function import (  # type: ignore
    _get_users_table,
    _get_authorized_email,
    _get_json_body,
    handle_auth_login,
    handle_auth_register,
)


# =============
# 共通レスポンス
# =============
def _cors_headers() -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    }


def _response(status: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status,
        "headers": _cors_headers(),
        "body": json.dumps(payload, ensure_ascii=False),
    }


def _no_content() -> Dict[str, Any]:
    return {"statusCode": 204, "headers": _cors_headers(), "body": ""}


def _path(event: Dict[str, Any]) -> str:
    return (event.get("rawPath") or event.get("path") or "").rstrip("/") or "/"


def _method(event: Dict[str, Any]) -> str:
    return (event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method") or "").upper()


# =============
# データモデル（DynamoDB 上のユーザーアイテム内に格納）
# =============
def _ensure_user(email: str) -> Dict[str, Any]:
    table = _get_users_table()
    res = table.get_item(Key={"email": email})
    if "Item" in res and res["Item"]:
        return res["Item"]
    # 未登録であれば最小項目で作成
    item = {
        "email": email,
        "name": "",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "profile": {},
        "base": {},
        "securities": {},
        "holdings": [],
        "favorites": [],
        "transactions": [],
    }
    table.put_item(Item=item)
    return item


def _require_auth_email(event: Dict[str, Any]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    email = _get_authorized_email(event)
    if not email:
        return None, _response(401, {"error": "未認証です"})
    _ensure_user(email)
    return email, None


# =============
# ルート実装
# =============
def _handle_options() -> Dict[str, Any]:
    return _no_content()


def _handle_user_register(event: Dict[str, Any]) -> Dict[str, Any]:
    # user_id を email として扱う
    body = _get_json_body(event) or {}
    if body.get("user_id") and not body.get("email"):
        body["email"] = str(body.get("user_id")).strip().lower()
    # event を再構築
    new_event = dict(event)
    new_event["body"] = json.dumps(body, ensure_ascii=False)
    new_event["isBase64Encoded"] = False
    result = handle_auth_register(new_event)
    if result.get("error"):
        return _response(400, result)
    return _response(201, result)


def _handle_user_login(event: Dict[str, Any]) -> Dict[str, Any]:
    # user_id を email として扱う
    body = _get_json_body(event) or {}
    if body.get("user_id") and not body.get("email"):
        body["email"] = str(body.get("user_id")).strip().lower()
    # event を再構築
    new_event = dict(event)
    new_event["body"] = json.dumps(body, ensure_ascii=False)
    new_event["isBase64Encoded"] = False
    result = handle_auth_login(new_event)
    if result.get("error"):
        return _response(401, result)
    return _response(200, result)


def _handle_user_base_get(event: Dict[str, Any]) -> Dict[str, Any]:
    email, err = _require_auth_email(event)
    if err:
        return err
    table = _get_users_table()
    res = table.get_item(Key={"email": email})
    user = res.get("Item") or {}
    base = user.get("base") or {}
    # email フィールドは常に返す
    base_out = {"email": email, **base}
    return _response(200, base_out)


def _handle_user_base_put(event: Dict[str, Any]) -> Dict[str, Any]:
    email, err = _require_auth_email(event)
    if err:
        return err
    data = _get_json_body(event)
    # 指定プロパティのみ受け入れ
    allowed = {
        "first_name",
        "family_name",
        "first_name_kana",
        "family_name_kana",
        "email",
        "phone_number",
    }
    incoming = {k: v for k, v in (data or {}).items() if k in allowed}
    table = _get_users_table()
    cur = table.get_item(Key={"email": email}).get("Item") or {}
    base = {**(cur.get("base") or {}), **incoming}
    base["updated_at"] = datetime.utcnow().isoformat()
    table.update_item(
        Key={"email": email},
        UpdateExpression="SET #b = :b, updated_at = :u",
        ExpressionAttributeNames={"#b": "base"},
        ExpressionAttributeValues={":b": base, ":u": datetime.utcnow().isoformat()},
    )
    return _response(204, {"status": "ok"})


def _handle_user_base_delete_via_post(event: Dict[str, Any]) -> Dict[str, Any]:
    email, err = _require_auth_email(event)
    if err:
        return err
    data = _get_json_body(event) or {}
    if not data.get("confirm"):
        return _response(400, {"error": "confirm=true が必要です"})
    table = _get_users_table()
    try:
        table.delete_item(Key={"email": email})
        return _response(202, {"status": "accepted", "message": "削除を受け付けました"})
    except ClientError as e:
        return _response(500, {"error": e.response.get("Error", {}).get("Message", str(e))})


def _handle_user_securities(event: Dict[str, Any]) -> Dict[str, Any]:
    email, err = _require_auth_email(event)
    if err:
        return err
    method = _method(event)
    table = _get_users_table()
    if method == "GET":
        d = table.get_item(Key={"email": email}).get("Item") or {}
        return _response(200, d.get("securities") or {})
    data = _get_json_body(event) or {}
    if method in ("POST", "PUT"):
        d = table.get_item(Key={"email": email}).get("Item") or {}
        new_val = {**(d.get("securities") or {}), **data}
        table.update_item(
            Key={"email": email},
            UpdateExpression="SET securities = :s, updated_at = :u",
            ExpressionAttributeValues={":s": new_val, ":u": datetime.utcnow().isoformat()},
        )
        return _response(200, new_val)
    if method == "DELETE":
        table.update_item(
            Key={"email": email},
            UpdateExpression="REMOVE securities SET updated_at = :u",
            ExpressionAttributeValues={":u": datetime.utcnow().isoformat()},
        )
        return _no_content()
    return _response(405, {"error": "method not allowed"})


def _handle_user_holdings_get(event: Dict[str, Any]) -> Dict[str, Any]:
    email, err = _require_auth_email(event)
    if err:
        return err
    table = _get_users_table()
    d = table.get_item(Key={"email": email}).get("Item") or {}
    return _response(200, d.get("holdings") or [])


def _handle_user_favorites(event: Dict[str, Any], symbol: Optional[str]) -> Dict[str, Any]:
    email, err = _require_auth_email(event)
    if err:
        return err
    method = _method(event)
    table = _get_users_table()
    if method == "GET" and symbol is None:
        d = table.get_item(Key={"email": email}).get("Item") or {}
        return _response(200, d.get("favorites") or [])
    if method == "POST" and symbol is None:
        data = _get_json_body(event) or {}
        sym = (data.get("symbol") or "").strip().upper()
        if not sym:
            return _response(400, {"error": "symbol は必須です"})
        d = table.get_item(Key={"email": email}).get("Item") or {}
        favs: List[Dict[str, Any]] = list(d.get("favorites") or [])
        if all(x.get("symbol") != sym for x in favs):
            favs.append({"symbol": sym})
            table.update_item(
                Key={"email": email},
                UpdateExpression="SET favorites = :f, updated_at = :u",
                ExpressionAttributeValues={":f": favs, ":u": datetime.utcnow().isoformat()},
            )
        return _response(201, {"status": "created"})
    if method == "DELETE" and symbol:
        sym = symbol.strip().upper()
        d = table.get_item(Key={"email": email}).get("Item") or {}
        favs: List[Dict[str, Any]] = [x for x in (d.get("favorites") or []) if x.get("symbol") != sym]
        table.update_item(
            Key={"email": email},
            UpdateExpression="SET favorites = :f, updated_at = :u",
            ExpressionAttributeValues={":f": favs, ":u": datetime.utcnow().isoformat()},
        )
        return _no_content()
    return _response(405, {"error": "method not allowed"})


def _handle_user_transactions(event: Dict[str, Any]) -> Dict[str, Any]:
    email, err = _require_auth_email(event)
    if err:
        return err
    method = _method(event)
    table = _get_users_table()
    if method == "GET":
        d = table.get_item(Key={"email": email}).get("Item") or {}
        return _response(200, d.get("transactions") or [])
    if method == "POST":
        data = _get_json_body(event) or {}
        for req in ("symbol", "quantity", "side"):
            if req not in data:
                return _response(400, {"error": f"{req} は必須です"})
        txn = {
            "id": str(uuid.uuid4()),
            "symbol": str(data.get("symbol")).upper(),
            "price": float(data.get("price")) if data.get("price") is not None else None,
            "quantity": int(data.get("quantity")),
            "type": str(data.get("side")).upper(),
            "timestamp": datetime.utcnow().isoformat(),
        }
        d = table.get_item(Key={"email": email}).get("Item") or {}
        txns: List[Dict[str, Any]] = list(d.get("transactions") or [])
        txns.append(txn)
        table.update_item(
            Key={"email": email},
            UpdateExpression="SET transactions = :t, updated_at = :u",
            ExpressionAttributeValues={":t": txns, ":u": datetime.utcnow().isoformat()},
        )
        return _response(201, txn)
    if method == "DELETE":
        table.update_item(
            Key={"email": email},
            UpdateExpression="SET transactions = :t, updated_at = :u",
            ExpressionAttributeValues={":t": [], ":u": datetime.utcnow().isoformat()},
        )
        return _no_content()
    return _response(405, {"error": "method not allowed"})


# シンボルは PoC 用の静的データ（YFinance とは独立）
_SYMBOLS: List[Dict[str, Any]] = [
    {"symbol": "AAPL", "name": "Apple Inc.", "market": "NMS", "industry": "Consumer Electronics", "current_price": 0.0, "updated_at": ""},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "market": "NMS", "industry": "Software—Infrastructure", "current_price": 0.0, "updated_at": ""},
    {"symbol": "TSLA", "name": "Tesla, Inc.", "market": "NMS", "industry": "Auto Manufacturers", "current_price": 0.0, "updated_at": ""},
]


def _handle_symbols_get() -> Dict[str, Any]:
    return _response(200, _SYMBOLS)


def _handle_symbol_get(symbol: str) -> Dict[str, Any]:
    sym = symbol.strip().upper()
    for s in _SYMBOLS:
        if s.get("symbol") == sym:
            return _response(200, s)
    return _response(404, {"error": "symbol not found"})


# =============
# エントリポイント
# =============
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:  # noqa: D401
    method = _method(event)
    path = _path(event)

    if method == "OPTIONS":
        return _handle_options()

    # 公開系
    if path == "/user/register" and method == "POST":
        return _handle_user_register(event)
    if path == "/user/login" and method == "POST":
        return _handle_user_login(event)

    # 認証必須系
    if path == "/user/base":
        if method == "GET":
            return _handle_user_base_get(event)
        if method == "PUT":
            return _handle_user_base_put(event)
        if method == "POST":  # 非REST: POSTで削除
            return _handle_user_base_delete_via_post(event)
        return _response(405, {"error": "method not allowed"})

    if path == "/user/securities":
        return _handle_user_securities(event)

    if path == "/user/holdings" and method == "GET":
        return _handle_user_holdings_get(event)

    if path == "/user/favorites" and method in ("GET", "POST"):
        return _handle_user_favorites(event, None)

    if path.startswith("/user/favorites/") and method == "DELETE":
        _, _, sym = path.partition("/user/favorites/")
        return _handle_user_favorites(event, sym)

    if path == "/user/transactions":
        return _handle_user_transactions(event)

    if path == "/symbols" and method == "GET":
        return _handle_symbols_get()

    if path.startswith("/symbols/") and method == "GET":
        _, _, sym = path.partition("/symbols/")
        return _handle_symbol_get(sym)

    return _response(404, {"error": "not found"})


