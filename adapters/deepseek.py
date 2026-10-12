# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 lollapalooza <https://github.com/aqua5230>
#
# Part of "usage". Free software licensed under the GNU Affero General Public
# License v3.0 only; see the LICENSE file for full terms and the warranty disclaimer.

from __future__ import annotations

from typing import Any
from loaders.deepseek_loader import DeepSeekQuotaResult


def format_deepseek_card(result: DeepSeekQuotaResult | None, language: str = "en") -> dict[str, Any]:
    if result is None or not result.is_configured:
        return {
            "configured": False,
            "available": False,
            "totalBalance": 0.0,
            "currency": "CNY",
            "currencySymbol": "¥",
            "formattedBalance": "--",
            "toppedUp": None,
            "granted": None,
            "errorMessage": None,
        }

    total_fmt = f"{result.currency_symbol}{result.total_balance:.2f}"
    return {
        "configured": True,
        "available": result.is_available,
        "totalBalance": result.total_balance,
        "currency": result.currency,
        "currencySymbol": result.currency_symbol,
        "formattedBalance": total_fmt,
        "toppedUp": f"{result.currency_symbol}{result.topped_up_balance:.2f}" if result.topped_up_balance is not None else None,
        "granted": f"{result.currency_symbol}{result.granted_balance:.2f}" if result.granted_balance is not None else None,
        "errorMessage": result.error_message,
    }


def format_menubar_title(result: DeepSeekQuotaResult | None) -> str:
    if result is None or not result.is_configured or result.error_message:
        return "--"
    # User requested: 货币符号 + 整数余额 (如 ¥25 或 )
    int_val = int(round(result.total_balance))
    return f"{result.currency_symbol}{int_val}"
