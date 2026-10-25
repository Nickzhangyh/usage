# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 lollapalooza <https://github.com/aqua5230>
#
# Part of "usage". Free software licensed under the GNU Affero General Public
# License v3.0 only; see the LICENSE file for full terms and the warranty disclaimer.

from __future__ import annotations

import json
import logging
import os
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

DUOYUANX_DEFAULT_BASE_URL = "https://duoyuanx.com"
_TIMEOUT_SECONDS = 10.0

_CACHED_RESULT: DuoyuanXQuotaResult | None = None
_LAST_FETCH_TIME: float = 0.0
_CACHE_TTL_SECONDS: float = 60.0


def _get_ssl_context() -> ssl.SSLContext | None:
    try:
        ctx = ssl.create_default_context()
        if os.path.exists("/etc/ssl/cert.pem"):
            ctx.load_verify_locations(cafile="/etc/ssl/cert.pem")
        return ctx
    except Exception:
        return None


@dataclass(frozen=True, slots=True)
class DuoyuanXQuotaResult:
    is_available: bool
    name: str
    total_available_quota: int
    total_granted_quota: int
    total_used_quota: int
    balance: float
    used: float
    currency: str
    currency_symbol: str
    unlimited_quota: bool
    expires_at: int
    updated_at: float
    error_message: str | None = None
    is_configured: bool = True


def load_quota(
    api_key: str,
    base_url: str | None = None,
    force_refresh: bool = False,
) -> DuoyuanXQuotaResult | None:
    global _CACHED_RESULT, _LAST_FETCH_TIME

    key = (api_key or "").strip()
    if not key:
        return None

    now = time.time()
    if not force_refresh and _CACHED_RESULT is not None and (now - _LAST_FETCH_TIME) < _CACHE_TTL_SECONDS:
        return _CACHED_RESULT

    raw_base = (base_url or "").strip().rstrip("/")
    if not raw_base:
        raw_base = DUOYUANX_DEFAULT_BASE_URL

    result = _fetch_balance(key, raw_base)
    if result.is_available:
        _CACHED_RESULT = result
        _LAST_FETCH_TIME = now
        return result

    # If fetch failed but we have a valid cache, keep the cache
    if _CACHED_RESULT is not None and _CACHED_RESULT.is_available:
        logger.warning(
            "DuoyuanX quota fetch failed (%s); retaining cached quota",
            result.error_message or "unknown",
        )
        return _CACHED_RESULT

    _CACHED_RESULT = result
    _LAST_FETCH_TIME = now
    return result


def _fetch_balance(api_key: str, base_url: str) -> DuoyuanXQuotaResult:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "UsageApp/1.0",
    }

    clean_base = base_url[:-3] if base_url.endswith("/v1") else base_url

    # 1. Primary endpoint from docs: /api/usage/token/
    token_url = f"{clean_base}/api/usage/token/"
    for attempt in range(2):
        try:
            data = _http_get_json(token_url, headers)
            if isinstance(data, dict) and (data.get("code") is True or data.get("success") is True or "data" in data):
                info = data.get("data") if isinstance(data.get("data"), dict) else data
                avail_q = int(info.get("total_available", 0) or 0)
                grant_q = int(info.get("total_granted", 0) or 0)
                used_q = int(info.get("total_used", 0) or 0)
                name = str(info.get("name", "token") or "token")
                unlimited = bool(info.get("unlimited_quota", False))
                expires = int(info.get("expires_at", 0) or 0)

                balance = round(avail_q / 500000.0, 2)
                used = round(used_q / 500000.0, 2)

                return DuoyuanXQuotaResult(
                    is_available=True,
                    name=name,
                    total_available_quota=avail_q,
                    total_granted_quota=grant_q,
                    total_used_quota=used_q,
                    balance=balance,
                    used=used,
                    currency="USD",
                    currency_symbol="$",
                    unlimited_quota=unlimited,
                    expires_at=expires,
                    updated_at=time.time(),
                )
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                return DuoyuanXQuotaResult(
                    is_available=False,
                    name="",
                    total_available_quota=0,
                    total_granted_quota=0,
                    total_used_quota=0,
                    balance=0.0,
                    used=0.0,
                    currency="USD",
                    currency_symbol="$",
                    unlimited_quota=False,
                    expires_at=0,
                    updated_at=time.time(),
                    error_message="API Key 无效或未授权",
                )
            logger.debug("DuoyuanX /api/usage/token/ returned %d", exc.code)
            break
        except Exception as exc:
            logger.debug("DuoyuanX /api/usage/token/ attempt %d failed: %s", attempt, exc)
            time.sleep(0.3)

    # 2. Fallback: OpenAI-compatible /v1/dashboard/billing/subscription & usage
    sub_url = f"{clean_base}/v1/dashboard/billing/subscription"
    try:
        sub_data = _http_get_json(sub_url, headers)
        if isinstance(sub_data, dict) and "hard_limit_usd" in sub_data:
            hard_limit = float(sub_data.get("hard_limit_usd", 0.0) or 0.0)
            usage_url = f"{clean_base}/v1/dashboard/billing/usage"
            total_usage = 0.0
            try:
                usage_data = _http_get_json(usage_url, headers)
                if isinstance(usage_data, dict):
                    total_usage = float(usage_data.get("total_usage", 0.0) or 0.0) / 100.0
            except Exception:
                pass
            rem = max(0.0, hard_limit - total_usage)
            return DuoyuanXQuotaResult(
                is_available=True,
                name="duoyuanx",
                total_available_quota=int(rem * 500000),
                total_granted_quota=int(hard_limit * 500000),
                total_used_quota=int(total_usage * 500000),
                balance=round(rem, 2),
                used=round(total_usage, 2),
                currency="USD",
                currency_symbol="$",
                unlimited_quota=False,
                expires_at=int(sub_data.get("access_until", 0) or 0),
                updated_at=time.time(),
            )
    except Exception as exc:
        logger.debug("DuoyuanX fallback subscription probe failed: %s", exc)

    return DuoyuanXQuotaResult(
        is_available=False,
        name="",
        total_available_quota=0,
        total_granted_quota=0,
        total_used_quota=0,
        balance=0.0,
        used=0.0,
        currency="USD",
        currency_symbol="$",
        unlimited_quota=False,
        expires_at=0,
        updated_at=time.time(),
        error_message="Query failed: please check API Key / Base URL",
    )


def _http_get_json(url: str, headers: dict[str, str]) -> Any:
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS, context=_get_ssl_context()) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)
