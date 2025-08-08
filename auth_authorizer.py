#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom Lambda Authorizer for API Gateway (REQUEST/TOKEN compatible)
- Validates HMAC-SHA256 JWT from Authorization header: "Bearer <token>"
- Returns IAM policy (Allow/Deny) and exposes email in context

No external libraries; uses only Python stdlib.
"""

import os
import json
import time
import hmac
import hashlib
import base64
from typing import Dict, Any


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data_str: str) -> bytes:
    padding = '=' * (-len(data_str) % 4)
    return base64.urlsafe_b64decode(data_str + padding)


def _jwt_verify(token: str, secret: str) -> Dict[str, Any]:
    try:
        header_b64, payload_b64, signature_b64 = token.split('.')
    except ValueError:
        raise ValueError("invalid token format")

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    try:
        sig = _b64url_decode(signature_b64)
    except Exception:
        raise ValueError("invalid signature encoding")

    if not hmac.compare_digest(sig, expected_sig):
        raise ValueError("signature mismatch")

    try:
        payload_json = _b64url_decode(payload_b64)
        payload = json.loads(payload_json)
    except Exception:
        raise ValueError("invalid payload")

    exp = payload.get("exp")
    if isinstance(exp, (int, float)) and time.time() > float(exp):
        raise ValueError("token expired")

    return payload


def _generate_policy(principal_id: str, effect: str, resource: str, context: Dict[str, Any]):
    if effect not in ("Allow", "Deny"):
        effect = "Deny"
    policy = {
        "principalId": principal_id or "user",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": resource,
                }
            ],
        },
        "context": {k: (str(v) if v is not None else "") for k, v in context.items()},
    }
    return policy


def lambda_handler(event, context):  # noqa: D401
    """Entry point for API Gateway Lambda Authorizer."""
    secret = os.environ.get("JWT_SECRET", "")
    if not secret:
        # If no secret configured, deny by default
        print("[Authorizer] missing JWT_SECRET")
        return _generate_policy("anonymous", "Deny", event.get("methodArn", "*"), {"reason": "no_secret"})

    # Support TOKEN and REQUEST authorizer inputs
    token = None
    if isinstance(event, dict):
        print(f"[Authorizer] invoked type={event.get('type')} keys={list(event.keys())[:6]}")
        token = event.get("authorizationToken")
        # TOKENタイプでは authorizationToken に "Bearer ..." がそのまま入るケースがある
        if token and token.lower().startswith("bearer "):
            token = token.split(" ", 1)[1].strip()
        if not token:
            # REQUEST type: check headers
            headers = event.get("headers") or {}
            authz = headers.get("Authorization") or headers.get("authorization")
            if authz and authz.lower().startswith("bearer "):
                token = authz.split(" ", 1)[1].strip()

    if not token:
        print("[Authorizer] no token found")
        return _generate_policy("anonymous", "Deny", event.get("methodArn", "*"), {"reason": "no_token"})

    try:
        payload = _jwt_verify(token, secret)
        email = payload.get("sub") or payload.get("email") or "user"
        print(f"[Authorizer] verified email={email}")
        return _generate_policy(email, "Allow", event.get("methodArn", "*"), {"email": email})
    except Exception as e:  # pylint: disable=broad-except
        print(f"[Authorizer] verification failed: {e}")
        return _generate_policy("anonymous", "Deny", event.get("methodArn", "*"), {"reason": str(e)})


