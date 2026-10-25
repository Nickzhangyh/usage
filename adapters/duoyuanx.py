# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 lollapalooza <https://github.com/aqua5230>
#
# Part of "usage". Free software licensed under the GNU Affero General Public
# License v3.0 only; see the LICENSE file for full terms and the warranty disclaimer.

from __future__ import annotations

from typing import Any
from loaders.duoyuanx_loader import DuoyuanXQuotaResult


def format_duoyuanx_card(result: DuoyuanXQuotaResult | None, language: str = "en") -> dict[str, Any]:
    if result is None or not result.is_configured:
        return {
            "configured": False,
            "available": False,
            "name": "",
            "balance": 0.0,
            "formattedBalance": "--",
            "used": 0.0,
            "formattedUsed": "--",
            "totalAvailableQuota": 0,
            "totalGrantedQuota": 0,
            "totalUsedQuota": 0,
            "currency": "USD",
            "currencySymbol": "$",
            "unlimitedQuota": False,
            "expiresAt": 0,
            "errorMessage": None,
        }

    formatted_bal = f"{result.currency_symbol}{result.balance:.2f}"
    formatted_used = f"{result.currency_symbol}{result.used:.2f}"

    return {
        "configured": True,
        "available": result.is_available,
        "name": result.name,
        "balance": result.balance,
        "formattedBalance": formatted_bal,
        "used": result.used,
        "formattedUsed": formatted_used,
        "totalAvailableQuota": result.total_available_quota,
        "totalGrantedQuota": result.total_granted_quota,
        "totalUsedQuota": result.total_used_quota,
        "currency": result.currency,
        "currencySymbol": result.currency_symbol,
        "unlimitedQuota": result.unlimited_quota,
        "expiresAt": result.expires_at,
        "errorMessage": result.error_message,
    }


def format_menubar_title(result: DuoyuanXQuotaResult | None) -> str:
    if result is None or not result.is_configured or result.error_message:
        return "--"
    # Format e.g. $1.00 or $1
    if result.balance.is_integer():
        return f"{result.currency_symbol}{int(result.balance)}"
    return f"{result.currency_symbol}{result.balance:.2f}"
