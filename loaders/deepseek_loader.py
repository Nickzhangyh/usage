# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 lollapalooza <https://github.com/aqua5230>
#
# Part of "usage". Free software licensed under the GNU Affero General Public
# License v3.0 only; see the LICENSE file for full terms and the warranty disclaimer.

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

DEEPSEEK_DEFAULT_BASE_URL = "https://api.deepseek.com"
_TIMEOUT_SECONDS = 8.0

_CACHED_RESULT: DeepSeekQuotaResult | None = None
_LAST_FETCH_TIME: float = 0.0
_CACHE_TTL_SECONDS: float = 30.0


@dataclass(frozen=True, slots=True)
class DeepSeekQuotaResult:
    is_available: bool
    total_balance: float
    currency: str
    currency_symbol: str
    topped_up_balance: float | None
    granted_balance: float | None
    updated_at: float
    error_message: str | None = None
    is_configured: bool = True


def load_quota(
    api_key: str,
    base_url: str | None = None,
    force_refresh: bool = False,
) -> DeepSeekQuotaResult | None:
    global _CACHED_RESULT, _LAST_FETCH_TIME

    key = (api_key or "").strip()
    if not key:
        return None

    now = time.time()
    if not force_refresh and _CACHED_RESULT is not None and (now - _LAST_FETCH_TIME) < _CACHE_TTL_SECONDS:
        return _CACHED_RESULT

    raw_base = (base_url or "").strip().rstrip("/")
    if not raw_base:
        raw_base = DEEPSEEK_DEFAULT_BASE_URL

    result = _fetch_balance(key, raw_base)
    if result is not None:
        _CACHED_RESULT = result
        _LAST_FETCH_TIME = now
    return result


def _fetch_balance(api_key: str, base_url: str) -> DeepSeekQuotaResult:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "UsageApp/1.0",
    }

    # 1. Try official DeepSeek balance endpoint: /user/balance
    ds_url = f"{base_url}/user/balance"
    try:
        data = _http_get_json(ds_url, headers)
        if isinstance(data, dict) and "balance_infos" in data:
            infos = data.get("balance_infos")
            if isinstance(infos, list) and len(infos) > 0:
                first = infos[0]
                curr = str(first.get("currency", "CNY")).upper()
                symbol = "¥" if curr in ("CNY", "RMB") else "$"
                total = float(first.get("total_balance", 0.0) or 0.0)
                topped = float(first.get("topped_up_balance", 0.0) or 0.0)
                granted = float(first.get("granted_balance", 0.0) or 0.0)
                is_avail = bool(data.get("is_available", True))
                return DeepSeekQuotaResult(
                    is_available=is_avail,
                    total_balance=total,
                    currency=curr,
                    currency_symbol=symbol,
                    topped_up_balance=topped,
                    granted_balance=granted,
                    updated_at=time.time(),
                )
    except Exception as exc:
        logger.debug("DeepSeek /user/balance probe failed: %s", exc)

    # 2. Try NewAPI / OneAPI user self endpoint: /api/user/self
    clean_base = base_url[:-3] if base_url.endswith("/v1") else base_url
    oneapi_url = f"{clean_base}/api/user/self"
    try:
        data = _http_get_json(oneapi_url, headers)
        if isinstance(data, dict) and (data.get("success") is True or "data" in data):
            user_data = data.get("data", {}) if isinstance(data.get("data"), dict) else data
            quota = float(user_data.get("quota", 0.0) or 0.0)
            balance = quota / 500000.0
            return DeepSeekQuotaResult(
                is_available=balance > 0,
                total_balance=round(balance, 2),
                currency="USD",
                currency_symbol="$",
                topped_up_balance=None,
                granted_balance=None,
                updated_at=time.time(),
            )
    except Exception as exc:
        logger.debug("OneAPI /api/user/self probe failed: %s", exc)

    # 3. Try OpenAI-compatible /v1/dashboard/billing/subscription
    sub_url = f"{clean_base}/v1/dashboard/billing/subscription"
    try:
        data = _http_get_json(sub_url, headers)
        if isinstance(data, dict) and "hard_limit_usd" in data:
            hard_limit = float(data.get("hard_limit_usd", 0.0) or 0.0)
            usage_url = f"{clean_base}/v1/dashboard/billing/usage"
            total_usage = 0.0
            try:
                usage_data = _http_get_json(usage_url, headers)
                if isinstance(usage_data, dict):
                    total_usage = float(usage_data.get("total_usage", 0.0) or 0.0) / 100.0
            except Exception:
                pass
            rem = max(0.0, hard_limit - total_usage)
            return DeepSeekQuotaResult(
                is_available=rem > 0,
                total_balance=round(rem, 2),
                currency="USD",
                currency_symbol="$",
                topped_up_balance=None,
                granted_balance=None,
                updated_at=time.time(),
            )
    except Exception as exc:
        logger.debug("OpenAI billing probe failed: %s", exc)

    return DeepSeekQuotaResult(
        is_available=False,
        total_balance=0.0,
        currency="CNY",
        currency_symbol="¥",
        topped_up_balance=None,
        granted_balance=None,
        updated_at=time.time(),
        error_message="Query failed: please check API Key / Base URL",
    )


def _http_get_json(url: str, headers: dict[str, str]) -> Any:
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)
