# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 lollapalooza <https://github.com/aqua5230>
#
# Part of "usage". Free software licensed under the GNU Affero General Public
# License v3.0 only; see the LICENSE file for full terms and the warranty disclaimer.

from __future__ import annotations

import json
import logging
import os
import shutil
import sqlite3
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 12.0
_CACHED_RESULT: ManusQuotaResult | None = None
_CACHED_TOKEN: str | None = None
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
    global _CACHED_TOKEN
    cookie_path = os.path.expanduser("~/Library/Application Support/Manus/Cookies")
    if not os.path.exists(cookie_path):
        return _CACHED_TOKEN

    # 1. Try reading directly with read-only mode and 5s timeout
    try:
        uri = f"file://{cookie_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=5.0)
        c = conn.cursor()
        c.execute("SELECT value FROM cookies WHERE host_key LIKE '%manus.im%' AND name = 'session_id'")
        row = c.fetchone()
        conn.close()
        if row and row[0]:
            _CACHED_TOKEN = str(row[0])
            return _CACHED_TOKEN
    except Exception as exc:
        logger.debug("Direct read of Manus cookies failed (possibly locked): %s", exc)

    # 2. If locked by Manus Studio writing transactions, snapshot to temp file and read
    snap_path = "/tmp/manus_cookies_snap.db"
    try:
        shutil.copy2(cookie_path, snap_path)
        wal_path = cookie_path + "-wal"
        if os.path.exists(wal_path):
            try:
                shutil.copy2(wal_path, snap_path + "-wal")
            except Exception:
                pass
        conn = sqlite3.connect(snap_path, timeout=3.0)
        c = conn.cursor()
        c.execute("SELECT value FROM cookies WHERE host_key LIKE '%manus.im%' AND name = 'session_id'")
        row = c.fetchone()
        conn.close()
        if row and row[0]:
            _CACHED_TOKEN = str(row[0])
            return _CACHED_TOKEN
    except Exception as exc:
        logger.debug("Snapshot read of Manus cookies failed: %s", exc)
    finally:
        try:
            if os.path.exists(snap_path):
                os.remove(snap_path)
            if os.path.exists(snap_path + "-wal"):
                os.remove(snap_path + "-wal")
        except Exception:
            pass

    # 3. Fallback to in-memory cached token
    return _CACHED_TOKEN


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

    # Resilient caching: if network or RPC fails but we have a valid previous result,
    # preserve the cached quota so the menu bar doesn't flicker or lose credits!
    if result is not None and result.is_available:
        _CACHED_RESULT = result
        _LAST_FETCH_TIME = now
        return result

    if _CACHED_RESULT is not None and _CACHED_RESULT.is_available:
        # Transient failure: keep last known good credits
        logger.warning(
            "Manus quota fetch failed (%s); keeping cached quota of %d credits",
            result.error_message if result else "unknown",
            _CACHED_RESULT.effective_credits,
        )
        return _CACHED_RESULT

    _CACHED_RESULT = result
    _LAST_FETCH_TIME = now
    return result


def _rpc_post_json(method: str, token: str) -> tuple[dict[str, Any] | None, str | None]:
    """Execute ConnectRPC call. Returns (data_dict, error_message)."""
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

    last_error: str | None = None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body), None
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                return None, "登录已过期，请重新登录 Manus"
            elif exc.code == 429:
                return None, "请求过于频繁，稍后自动重试"
            else:
                last_error = f"HTTP {exc.code}"
        except urllib.error.URLError as exc:
            reason = str(getattr(exc, "reason", exc))
            if "timed out" in reason.lower() or "handshake" in reason.lower():
                last_error = "网络连接超时，稍后重试"
            else:
                last_error = f"网络请求失败 ({reason})"
        except Exception as exc:
            last_error = f"请求异常: {exc}"

        if attempt == 0:
            time.sleep(0.5)

    logger.warning("Manus UserService/%s failed: %s", method, last_error)
    return None, last_error


def _fetch_manus_data(token: str) -> ManusQuotaResult:
    credits_data, err = _rpc_post_json("GetAvailableCredits", token)
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
            error_message=err or "Query failed: please check Manus login",
            is_configured=True,
        )

    # Optional user profile
    user_data, _ = _rpc_post_json("UserInfo", token)
    user_data = user_data or {}

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
