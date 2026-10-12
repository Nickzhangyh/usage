# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 lollapalooza <https://github.com/aqua5230>
#
# Part of "usage". Free software licensed under the GNU Affero General Public
# License v3.0 only; see the LICENSE file for full terms and the warranty disclaimer.

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 8.0
_CACHED_RESULT: ManusQuotaResult | None = None
_LAST_FETCH_TIME: float = 0.0
_CACHE_TTL_SECONDS: float = 30.0


@dataclass(frozen=True, slots=True)
class ManusQuotaResult:
    is_available: bool
    effective_credits: int
    total_credits: int
    periodic_credits: int
    pro_monthly_credits: int
    free_credits: int
    refresh_credits: int
    max_refresh_credits: int
    next_refresh_time: str
    refresh_interval: str
    membership_version: str
    user_name: str
    email: str
    updated_at: float
    error_message: str | None = None
    is_configured: bool = True


def _read_local_session_cookie() -> str | None:
    cookie_path = os.path.expanduser("~/Library/Application Support/Manus/Cookies")
    if not os.path.exists(cookie_path):
        return None
    uri = f"file://{cookie_path}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True)
        c = conn.cursor()
        c.execute("SELECT value FROM cookies WHERE host_key LIKE '%manus.im%' AND name = 'session_id'")
        row = c.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as exc:
        logger.debug("Failed to read Manus cookies directly: %s", exc)
        return None


def load_quota(
    api_token: str | None = None,
    force_refresh: bool = False,
) -> ManusQuotaResult | None:
    global _CACHED_RESULT, _LAST_FETCH_TIME

    token = (api_token or "").strip()
    if not token:
        token = _read_local_session_cookie() or ""

    if not token:
        return None

    now = time.time()
    if not force_refresh and _CACHED_RESULT is not None and (now - _LAST_FETCH_TIME) < _CACHE_TTL_SECONDS:
        return _CACHED_RESULT

    result = _fetch_manus_data(token)
    if result is not None:
        _CACHED_RESULT = result
        _LAST_FETCH_TIME = now
    return result


def _rpc_post_json(method: str, token: str) -> dict[str, Any] | None:
    url = f"https://api.manus.im/user.v1.UserService/{method}"
    req = urllib.request.Request(
        url,
        data=b"{}",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "Connect-Protocol-Version": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Manus/1.0.0 Chrome/120.0.0.0 Electron/28.0.0 Safari/537.36",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except Exception as exc:
        logger.debug("Manus UserService/%s call failed: %s", method, exc)
        return None


def _fetch_manus_data(token: str) -> ManusQuotaResult:
    credits_data = _rpc_post_json("GetAvailableCredits", token)
    if not credits_data or not isinstance(credits_data, dict):
        return ManusQuotaResult(
            is_available=False,
            effective_credits=0,
            total_credits=0,
            periodic_credits=0,
            pro_monthly_credits=0,
            free_credits=0,
            refresh_credits=0,
            max_refresh_credits=0,
            next_refresh_time="",
            refresh_interval="daily",
            membership_version="pro",
            user_name="",
            email="",
            updated_at=time.time(),
            error_message="Query failed: please check Manus login",
            is_configured=True,
        )

    # Optional user profile
    user_data = _rpc_post_json("UserInfo", token) or {}

    total = int(credits_data.get("totalCredits", 0) or 0)
    periodic = int(credits_data.get("periodicCredits", 0) or 0)
    pro_monthly = int(credits_data.get("proMonthlyCredits", 0) or 0)
    free = int(credits_data.get("freeCredits", 0) or 0)
    refresh = int(credits_data.get("refreshCredits", 0) or 0)
    max_refresh = int(credits_data.get("maxRefreshCredits", 0) or 0)
    next_refresh = str(credits_data.get("nextRefreshTime", "") or "")
    interval = str(credits_data.get("refreshInterval", "daily") or "daily")

    # Formula matching Manus frontend: effective credits = total - refreshCredits
    effective = max(0, total - refresh)

    membership = str(user_data.get("membershipVersion", "pro") or "pro")
    name = str(user_data.get("displayname", "") or user_data.get("nickname", "") or "")
    email = str(user_data.get("email", "") or "")

    return ManusQuotaResult(
        is_available=True,
        effective_credits=effective,
        total_credits=total,
        periodic_credits=periodic,
        pro_monthly_credits=pro_monthly,
        free_credits=free,
        refresh_credits=refresh,
        max_refresh_credits=max_refresh,
        next_refresh_time=next_refresh,
        refresh_interval=interval,
        membership_version=membership,
        user_name=name,
        email=email,
        updated_at=time.time(),
        error_message=None,
        is_configured=True,
    )
