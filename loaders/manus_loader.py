# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 lollapalooza <https://github.com/aqua5230>
#
# Part of "usage". Free software licensed under the GNU Affero General Public
# License v3.0 only; see the LICENSE file for full terms and the warranty disclaimer.

from __future__ import annotations

import calendar
from datetime import datetime, timezone
import json
import logging
import os
import shutil
import sqlite3
import ssl
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


def _get_ssl_context() -> ssl.SSLContext | None:
    try:
        ctx = ssl.create_default_context()
        if os.path.exists("/etc/ssl/cert.pem"):
            ctx.load_verify_locations(cafile="/etc/ssl/cert.pem")
        return ctx
    except Exception:
        return None


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
    monthly_resets_at: float | None = None
    error_message: str | None = None
    is_configured: bool = True
    secondary_effective_credits: int | None = None
    secondary_membership_version: str = ""
    secondary_user_name: str = ""
    secondary_monthly_resets_at: float | None = None
    secondary_error_message: str | None = None


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
    web_token: str | None = None,
    force_refresh: bool = False,
) -> ManusQuotaResult | None:
    global _CACHED_RESULT, _LAST_FETCH_TIME

    token1 = (api_token or "").strip()
    token2 = (web_token or "").strip()

    if not token2 and token1 and ("," in token1 or "\n" in token1):
        parts = [p.strip() for p in token1.replace("\n", ",").split(",") if p.strip()]
        if len(parts) >= 2:
            token1 = parts[0]
            token2 = parts[1]

    if not token1:
        token1 = _read_local_session_cookie() or ""

    if not token1 and not token2:
        return None

    now = time.time()
    if not force_refresh and _CACHED_RESULT is not None and (now - _LAST_FETCH_TIME) < _CACHE_TTL_SECONDS:
        return _CACHED_RESULT

    res1: ManusQuotaResult | None = None
    if token1:
        res1 = _fetch_manus_data(token1)

    res2: ManusQuotaResult | None = None
    if token2:
        res2 = _fetch_manus_data(token2)

    if res1 is None and res2 is None:
        return None

    merged_res: ManusQuotaResult | None = None
    if res1 is not None and res2 is not None:
        merged_res = ManusQuotaResult(
            is_available=res1.is_available or res2.is_available,
            effective_credits=res1.effective_credits,
            total_credits=res1.total_credits,
            periodic_credits=res1.periodic_credits,
            pro_monthly_credits=res1.pro_monthly_credits,
            free_credits=res1.free_credits,
            refresh_credits=res1.refresh_credits,
            max_refresh_credits=res1.max_refresh_credits,
            next_refresh_time=res1.next_refresh_time,
            refresh_interval=res1.refresh_interval,
            membership_version=res1.membership_version,
            user_name=res1.user_name,
            email=res1.email,
            updated_at=now,
            monthly_resets_at=res1.monthly_resets_at,
            error_message=res1.error_message if not res1.is_available else None,
            is_configured=True,
            secondary_effective_credits=res2.effective_credits if res2.is_available else None,
            secondary_membership_version=res2.membership_version if res2.is_available else "",
            secondary_user_name=res2.user_name if res2.is_available else "",
            secondary_monthly_resets_at=res2.monthly_resets_at if res2.is_available else None,
            secondary_error_message=res2.error_message if not res2.is_available else None,
        )
    elif res1 is not None:
        merged_res = res1
    else:
        merged_res = res2

    assert merged_res is not None
    if merged_res.is_available:
        _CACHED_RESULT = merged_res
        _LAST_FETCH_TIME = now
        return merged_res

    if _CACHED_RESULT is not None and _CACHED_RESULT.is_available:
        logger.warning(
            "Manus quota fetch failed (%s); keeping cached quota of %d credits",
            merged_res.error_message or "unknown",
            _CACHED_RESULT.effective_credits,
        )
        return _CACHED_RESULT

    _CACHED_RESULT = merged_res
    _LAST_FETCH_TIME = now
    return merged_res


def _rest_get_json(endpoint: str, token: str) -> tuple[dict[str, Any] | None, str | None]:
    for host in ("api.manus.im", "api.manus.ai"):
        url = f"https://{host}/{endpoint}"
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Manus/1.0.0 Chrome/120.0.0.0 Safari/537.36",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS, context=_get_ssl_context()) as resp:
                body = resp.read().decode("utf-8")
                parsed = json.loads(body)
                if isinstance(parsed, dict):
                    data = parsed.get("data") if isinstance(parsed.get("data"), dict) else parsed
                    return data, None
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                return None, "API Key 或 Token 无效/已过期"
            logger.debug("REST GET %s returned %d", url, exc.code)
        except Exception as exc:
            logger.debug("REST GET %s failed: %s", url, exc)
    return None, "API 请求失败"


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
            with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS, context=_get_ssl_context()) as resp:
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


def _compute_monthly_reset_ts(user_data: dict[str, Any], credits_data: dict[str, Any]) -> float | None:
    now_ts = time.time()
    now_dt = datetime.fromtimestamp(now_ts, timezone.utc)

    interval = str(user_data.get("membershipInterval", "")).lower()
    period_end_raw = user_data.get("currentPeriodEnd") or (user_data.get("membershipInfo") or {}).get("currentPeriodEnd")
    period_end_ts: float | None = None
    if period_end_raw:
        try:
            period_end_ts = float(period_end_raw)
        except (ValueError, TypeError):
            pass

    # If subscription is explicitly monthly and period end is in future, use it directly
    if interval == "monthly" and period_end_ts and period_end_ts > now_ts:
        return period_end_ts

    anchor_dt: datetime | None = None
    registered_at = user_data.get("registeredAt")
    if registered_at and isinstance(registered_at, str):
        try:
            anchor_dt = datetime.fromisoformat(registered_at.replace("Z", "+00:00"))
        except Exception:
            pass

    if not anchor_dt and period_end_ts:
        try:
            anchor_dt = datetime.fromtimestamp(period_end_ts, timezone.utc)
        except Exception:
            pass

    if not anchor_dt:
        return None

    day = anchor_dt.day
    hour = anchor_dt.hour
    minute = anchor_dt.minute
    second = anchor_dt.second

    # Check reset date in current month
    year = now_dt.year
    month = now_dt.month
    max_day = calendar.monthrange(year, month)[1]
    candidate = datetime(year, month, min(day, max_day), hour, minute, second, tzinfo=timezone.utc)
    if candidate > now_dt:
        return candidate.timestamp()

    # Otherwise next month
    if month == 12:
        year += 1
        month = 1
    else:
        month += 1
    max_day = calendar.monthrange(year, month)[1]
    candidate = datetime(year, month, min(day, max_day), hour, minute, second, tzinfo=timezone.utc)
    return candidate.timestamp()


def _fetch_manus_data(token: str) -> ManusQuotaResult:
    credits_data, err = _rpc_post_json("GetAvailableCredits", token)
    if not credits_data or not isinstance(credits_data, dict):
        rest_data, rest_err = _rest_get_json("v2/usage.availableCredits", token)
        if rest_data and isinstance(rest_data, dict):
            credits_data = rest_data
            err = None
        else:
            rest_data, _ = _rest_get_json("v1/user/credits", token)
            if rest_data and isinstance(rest_data, dict):
                credits_data = rest_data
                err = None

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
            monthly_resets_at=None,
            error_message=err or "Query failed: please check Manus login or API Key",
            is_configured=True,
        )

    # Optional user profile
    user_data, _ = _rpc_post_json("UserInfo", token)
    user_data = user_data or {}

    total = int(credits_data.get("total_credits") or credits_data.get("totalCredits") or 0)
    periodic = int(credits_data.get("periodic_credits") or credits_data.get("periodicCredits") or 0)
    pro_monthly = int(credits_data.get("pro_monthly_credits") or credits_data.get("proMonthlyCredits") or 0)
    free = int(credits_data.get("free_credits") or credits_data.get("freeCredits") or 0)
    refresh = int(credits_data.get("refresh_credits") or credits_data.get("refreshCredits") or 0)
    max_refresh = int(credits_data.get("max_refresh_credits") or credits_data.get("maxRefreshCredits") or 0)
    next_refresh = str(credits_data.get("next_refresh_time") or credits_data.get("nextRefreshTime") or "")
    interval = str(credits_data.get("refresh_interval") or credits_data.get("refreshInterval") or "daily")

    # Formula matching Manus frontend: effective credits = total - refreshCredits
    effective = max(0, total - refresh)

    membership = str(user_data.get("membershipVersion", "pro") or "pro")
    name = str(user_data.get("displayname", "") or user_data.get("nickname", "") or "")
    email = str(user_data.get("email", "") or "")
    monthly_resets_at = _compute_monthly_reset_ts(user_data, credits_data)

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
        monthly_resets_at=monthly_resets_at,
        error_message=None,
        is_configured=True,
    )
