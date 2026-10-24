# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 lollapalooza <https://github.com/aqua5230>
#
# Part of "usage". Free software licensed under the GNU Affero General Public
# License v3.0 only; see the LICENSE file for full terms and the warranty disclaimer.

from __future__ import annotations

import time
from typing import Any
from loaders.manus_loader import ManusQuotaResult
from menubar.state import _t, format_human_time


def format_manus_card(result: ManusQuotaResult | None, language: str = "en") -> dict[str, Any]:
    if result is None or not result.is_configured:
        return {
            "configured": False,
            "available": False,
            "effectiveCredits": 0,
            "formattedCredits": "--",
            "totalCredits": 0,
            "periodicCredits": 0,
            "proMonthlyCredits": 0,
            "freeCredits": 0,
            "refreshCredits": 0,
            "maxRefreshCredits": 0,
            "membershipVersion": "pro",
            "planName": "Manus Pro",
            "userName": "",
            "email": "",
            "nextRefreshTime": "",
            "monthlyResetsAt": None,
            "resetText": "",
            "errorMessage": None,
        }

    plan_display = f"Manus {result.membership_version.capitalize()}" if result.membership_version else "Manus Pro"

    reset_text = ""
    if result.monthly_resets_at is not None:
        now = time.time()
        seconds_left = max(0.0, result.monthly_resets_at - now)
        if seconds_left <= 0:
            reset_text = _t(language, "reset_done")
        elif seconds_left < 60:
            reset_text = _t(language, "reset_imminent")
        else:
            reset_text = _t(language, "reset_in", time=format_human_time(seconds_left, language))

    sec_credits = result.secondary_effective_credits
    sec_formatted = f"{sec_credits:,}" if sec_credits is not None else None

    formatted_display = f"{result.effective_credits:,}"
    if sec_formatted is not None:
        formatted_display = f"{result.effective_credits:,} / {sec_formatted}"

    return {
        "configured": True,
        "available": result.is_available,
        "effectiveCredits": result.effective_credits,
        "formattedCredits": formatted_display,
        "primaryCredits": result.effective_credits,
        "secondaryEffectiveCredits": sec_credits,
        "secondaryFormattedCredits": sec_formatted,
        "secondaryMembershipVersion": result.secondary_membership_version,
        "secondaryUserName": result.secondary_user_name,
        "secondaryMonthlyResetsAt": result.secondary_monthly_resets_at,
        "secondaryErrorMessage": result.secondary_error_message,
        "totalCredits": result.total_credits,
        "periodicCredits": result.periodic_credits,
        "proMonthlyCredits": result.pro_monthly_credits,
        "freeCredits": result.free_credits,
        "refreshCredits": result.refresh_credits,
        "maxRefreshCredits": result.max_refresh_credits,
        "membershipVersion": result.membership_version,
        "planName": plan_display,
        "userName": result.user_name,
        "email": result.email,
        "nextRefreshTime": result.next_refresh_time,
        "monthlyResetsAt": result.monthly_resets_at,
        "resetText": reset_text,
        "errorMessage": result.error_message,
    }


def format_menubar_title(result: ManusQuotaResult | None) -> str:
    if result is None or not result.is_configured or not result.is_available or result.error_message:
        return "--"
    return str(int(result.effective_credits))
