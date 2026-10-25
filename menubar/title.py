# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 lollapalooza <https://github.com/aqua5230>
#
# Part of "usage". Free software licensed under the GNU Affero General Public
# License v3.0 only; see the LICENSE file for full terms and the warranty disclaimer.

"""Menu bar title rendering."""

from __future__ import annotations

from typing import Any, Protocol

from AppKit import (
    NSAttributedString,
    NSFont,
    NSFontAttributeName,
    NSFontWeightBold,
    NSKernAttributeName,
    NSMutableAttributedString,
)

from menubar.chrome import (
    _agy_menubar_icon,
    _claude_menubar_icon,
    _codex_menubar_icon,
    _deepseek_menubar_icon,
    _duoyuanx_menubar_icon,
    _grok_menubar_icon,
    _manus_menubar_icon,
    _menubar_icon_attachment_string,
)
from menubar.state import PopoverState, _format_percent


class _TitleApp(Protocol):
    _menubar_text_cache: dict[str, Any]
    codex_5h_pct: float | None
    _last_button_title_key: tuple[str] | None
    _last_plain_title_key: tuple[str] | None
    status_item: Any


_MENUBAR_FONT: Any = None


def _menubar_font() -> Any:
    # Bold at the menu bar's own point size: the percentages have to carry the
    # strip on their own, against any wallpaper.
    global _MENUBAR_FONT
    if _MENUBAR_FONT is None:
        base = NSFont.menuBarFontOfSize_(0)
        _MENUBAR_FONT = NSFont.systemFontOfSize_weight_(base.pointSize(), NSFontWeightBold)
    return _MENUBAR_FONT


def _format_compact_credits(credits: int | float | None) -> str:
    if credits is None:
        return "--"
    val = float(credits)
    if val >= 1000000:
        return f"{val / 1000000.0:.1f}m"
    elif val >= 1000:
        return f"{val / 1000.0:.1f}k"
    elif val > 0:
        return f"{val / 1000.0:.1f}k"
    else:
        return "0"


def _menubar_text_string(app: _TitleApp, text: str) -> Any:
    cached = app._menubar_text_cache.get(text)
    if cached is not None:
        return cached
    attrs: dict[Any, Any] = {
        NSFontAttributeName: _menubar_font(),
    }
    if NSKernAttributeName is not None:
        attrs[NSKernAttributeName] = -0.3
    attributed = NSAttributedString.alloc().initWithString_attributes_(
        text,
        attrs,
    )
    app._menubar_text_cache[text] = attributed
    return attributed


def _format_menubar_percent(rem: float | None) -> str:
    if rem is None:
        return "--"
    val = max(0.0, min(100.0, float(rem)))
    rounded = int(round(val))
    if val > 0 and rounded == 0:
        rounded = 1
    return f"{rounded}%"


def _menubar_attributed_title(app: _TitleApp, state: PopoverState) -> Any:
    title = NSMutableAttributedString.alloc().init()
    if not state.hide_claude and getattr(state, "show_claude_menubar", True):
        claude_rem = (
            None
            if state.claude_session.percent is None
            else max(0.0, 100.0 - state.claude_session.percent)
        )
        claude_percent = _format_menubar_percent(claude_rem)
        title.appendAttributedString_(_menubar_icon_attachment_string(_claude_menubar_icon()))
        title.appendAttributedString_(_menubar_text_string(app, f" {claude_percent}"))
    if not state.hide_codex and getattr(state, "show_codex_menubar", True) and (app.codex_5h_pct is not None or state.hide_claude or not getattr(state, "show_claude_menubar", True)):
        codex_rem = (
            None
            if app.codex_5h_pct is None
            else max(0.0, 100.0 - float(app.codex_5h_pct))
        )
        codex_percent = _format_menubar_percent(codex_rem)
        if title.length() > 0:
            title.appendAttributedString_(_menubar_text_string(app, "  "))
        title.appendAttributedString_(_menubar_icon_attachment_string(_codex_menubar_icon()))
        title.appendAttributedString_(_menubar_text_string(app, f" {codex_percent}"))
    agy_session_percent = state.agy_session.percent
    agy_visible = not state.hide_agy and getattr(state, "show_agy_menubar", True) and agy_session_percent is not None
    if agy_visible:
        assert agy_session_percent is not None
        agy_rem = max(0.0, 100.0 - agy_session_percent)
        agy_percent = _format_menubar_percent(agy_rem)
        if title.length() > 0:
            title.appendAttributedString_(_menubar_text_string(app, "  "))
        title.appendAttributedString_(_menubar_icon_attachment_string(_agy_menubar_icon()))
        title.appendAttributedString_(_menubar_text_string(app, f" {agy_percent}"))
    grok_weekly_percent = state.grok_weekly.percent
    grok_visible = not state.hide_grok and getattr(state, "show_grok_menubar", True) and grok_weekly_percent is not None
    if grok_visible:
        assert grok_weekly_percent is not None
        grok_rem = max(0.0, 100.0 - grok_weekly_percent)
        grok_percent = _format_menubar_percent(grok_rem)
        if title.length() > 0:
            title.appendAttributedString_(_menubar_text_string(app, "  "))
        title.appendAttributedString_(_menubar_icon_attachment_string(_grok_menubar_icon()))
        title.appendAttributedString_(_menubar_text_string(app, f" {grok_percent}"))
    deepseek_data = state.deepseek
    deepseek_visible = (
        not state.hide_deepseek
        and getattr(state, "show_deepseek_menubar", False)
        and deepseek_data
        and deepseek_data.get("configured")
    )
    if deepseek_visible:
        int_bal = int(round(float(deepseek_data.get("totalBalance", 0.0) or 0.0)))
        sym = deepseek_data.get("currencySymbol", "¥")
        ds_text = f" {sym}{int_bal}"
        if title.length() > 0:
            title.appendAttributedString_(_menubar_text_string(app, "  "))
        title.appendAttributedString_(_menubar_icon_attachment_string(_deepseek_menubar_icon()))
        title.appendAttributedString_(_menubar_text_string(app, ds_text))
    manus_data = state.manus
    manus_visible = (
        not state.hide_manus
        and getattr(state, "show_manus_menubar", True)
        and manus_data
        and (
            manus_data.get("available")
            or int(manus_data.get("effectiveCredits", 0) or 0) > 0
            or manus_data.get("secondaryEffectiveCredits") is not None
        )
    )
    if manus_visible:
        c1 = int(manus_data.get("effectiveCredits", 0) or 0)
        c2 = manus_data.get("secondaryEffectiveCredits")
        if c2 is not None:
            manus_text = f" {_format_compact_credits(c1)}/{_format_compact_credits(c2)}"
        else:
            manus_text = f" {_format_compact_credits(c1)}"
        if title.length() > 0:
            title.appendAttributedString_(_menubar_text_string(app, "  "))
        title.appendAttributedString_(_menubar_icon_attachment_string(_manus_menubar_icon()))
        title.appendAttributedString_(_menubar_text_string(app, manus_text))
    duoyuanx_data = state.duoyuanx
    duoyuanx_visible = (
        not state.hide_duoyuanx
        and getattr(state, "show_duoyuanx_menubar", False)
        and duoyuanx_data
        and duoyuanx_data.get("configured")
    )
    if duoyuanx_visible:
        bal = float(duoyuanx_data.get("balance", 0.0) or 0.0)
        sym = duoyuanx_data.get("currencySymbol", "$")
        dyx_text = f" {sym}{int(bal)}" if bal.is_integer() else f" {sym}{bal:.2f}"
        if title.length() > 0:
            title.appendAttributedString_(_menubar_text_string(app, "  "))
        title.appendAttributedString_(_menubar_icon_attachment_string(_duoyuanx_menubar_icon()))
        title.appendAttributedString_(_menubar_text_string(app, dyx_text))
    if title.length() == 0:
        # All providers hidden or unchecked: keep a recognizable, clickable status item.
        title.appendAttributedString_(_menubar_icon_attachment_string(_claude_menubar_icon()))
    return title


def _set_button_title(app: _TitleApp, state: PopoverState) -> None:
    title = _compose_title(app, state)
    title_key = (title,)
    if app._last_button_title_key == title_key:
        return

    button = app.status_item.button()
    plain_key = (title,)
    if app._last_plain_title_key != plain_key:
        button.setTitle_(title)
        app._last_plain_title_key = plain_key
    button.setAttributedTitle_(_menubar_attributed_title(app, state))
    app._last_button_title_key = title_key


def _compose_title(app: _TitleApp, state: PopoverState) -> str:
    parts: list[str] = []
    if not state.hide_claude and getattr(state, "show_claude_menubar", True):
        claude_rem = (
            None
            if state.claude_session.percent is None
            else max(0.0, 100.0 - state.claude_session.percent)
        )
        parts.append(_format_menubar_percent(claude_rem))
    if not state.hide_codex and getattr(state, "show_codex_menubar", True) and (app.codex_5h_pct is not None or state.hide_claude or not getattr(state, "show_claude_menubar", True)):
        codex_rem = (
            None
            if app.codex_5h_pct is None
            else max(0.0, 100.0 - float(app.codex_5h_pct))
        )
        parts.append(_format_menubar_percent(codex_rem))
    if not state.hide_agy and getattr(state, "show_agy_menubar", True) and state.agy_session.percent is not None:
        agy_rem = max(0.0, 100.0 - state.agy_session.percent)
        parts.append(_format_menubar_percent(agy_rem))
    if not state.hide_grok and getattr(state, "show_grok_menubar", True) and state.grok_weekly.percent is not None:
        grok_rem = max(0.0, 100.0 - state.grok_weekly.percent)
        parts.append(_format_menubar_percent(grok_rem))
    if (
        not state.hide_deepseek
        and getattr(state, "show_deepseek_menubar", False)
        and state.deepseek
        and state.deepseek.get("configured")
    ):
        int_bal = int(round(float(state.deepseek.get("totalBalance", 0.0) or 0.0)))
        sym = state.deepseek.get("currencySymbol", "¥")
        parts.append(f"{sym}{int_bal}")
    if (
        not state.hide_manus
        and getattr(state, "show_manus_menubar", True)
        and state.manus
        and (
            state.manus.get("available")
            or int(state.manus.get("effectiveCredits", 0) or 0) > 0
            or state.manus.get("secondaryEffectiveCredits") is not None
        )
    ):
        c1 = int(state.manus.get("effectiveCredits", 0) or 0)
        c2 = state.manus.get("secondaryEffectiveCredits")
        if c2 is not None:
            parts.append(f"{_format_compact_credits(c1)}/{_format_compact_credits(c2)}")
        else:
            parts.append(_format_compact_credits(c1))
    if (
        not state.hide_duoyuanx
        and getattr(state, "show_duoyuanx_menubar", False)
        and state.duoyuanx
        and state.duoyuanx.get("configured")
    ):
        bal = float(state.duoyuanx.get("balance", 0.0) or 0.0)
        sym = state.duoyuanx.get("currencySymbol", "$")
        parts.append(f"{sym}{int(bal)}" if bal.is_integer() else f"{sym}{bal:.2f}")
    # All providers hidden or unchecked: keep a recognizable, clickable status item.
    return " · ".join(parts) if parts else "usage"
