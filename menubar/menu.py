# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 lollapalooza <https://github.com/aqua5230>
#
# Part of "usage". Free software licensed under the GNU Affero General Public
# License v3.0 only; see the LICENSE file for full terms and the warranty disclaimer.

from __future__ import annotations

from typing import Any, Protocol

from AppKit import NSMakePoint, NSMenu, NSMenuItem

from i18n import _t
from installer import login_item
from menubar.prefs import (
    _deepseek_menubar_enabled,
    _hide_agy_enabled,
    _hide_claude_enabled,
    _hide_codex_enabled,
    _hide_deepseek_enabled,
    _hide_duoyuanx_enabled,
    _hide_footer_enabled,
    _hide_grok_enabled,
    _hide_manus_enabled,
    _hide_projects_enabled,
    _menubar_provider_visible,
    _quota_notifications_enabled,
    _window_keeper_enabled,
)


class _SwitchMenuApp(Protocol):
    language: str
    active_panel: Any
    _switch_menu_action_taken: bool

    def _resync_popover_after_menu(self) -> None: ...


def build_menu_item(
    language: str,
    title_key: str,
    selector: str,
    *,
    target: Any,
    represented: Any | None = None,
    state: bool | None = None,
    tooltip_key: str | None = None,
) -> Any:
    item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        _t(language, title_key), selector, ""
    )
    item.setTarget_(target)
    if represented is not None:
        item.setRepresentedObject_(represented)
    if state is not None:
        item.setState_(1 if state else 0)
    if tooltip_key is not None:
        item.setToolTip_(_t(language, tooltip_key))
    return item


def build_switch_menu(app: _SwitchMenuApp, sender: Any) -> None:
    import panels
    from menubar.app import _session_resume_enabled, _terse_mode_enabled

    menu = NSMenu.alloc().initWithTitle_(_t(app.language, "switch_panel"))
    menu.addItem_(
        build_menu_item(app.language, "panel_ai_daily", "toggleAiDaily:", target=app)
    )
    menu.addItem_(
        build_menu_item(app.language, "reset_panel_position", "resetPanelPosition:", target=app)
    )
    menu.addItem_(NSMenuItem.separatorItem())
    # Panel themes live in a submenu so the menu stays short — one "面板主題 ▸"
    # row that expands on demand instead of fourteen inline rows.
    panel_submenu = NSMenu.alloc().initWithTitle_(_t(app.language, "switch_panel"))
    for panel in panels.all_panels():
        panel_submenu.addItem_(
            build_menu_item(
                app.language, panel.i18n_key, "selectPanel:", target=app,
                represented=panel.id,
                state=panel.id == app.active_panel.id,
            )
        )
    panel_parent = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        _t(app.language, "switch_panel"), "", ""
    )
    panel_parent.setSubmenu_(panel_submenu)
    menu.addItem_(panel_parent)
    # Provider visibility lives in one "Hide Sections ▸" submenu row, grouped
    # with the panel-themes submenu: both are drill-in rows that shape what
    # the popover shows.
    hide_submenu = NSMenu.alloc().initWithTitle_(_t(app.language, "hide_sections_menu"))
    hide_submenu.addItem_(
        build_menu_item(
            app.language, "claude_name", "toggleHideClaude:", target=app,
            state=_hide_claude_enabled(),
        )
    )
    hide_submenu.addItem_(
        build_menu_item(
            app.language, "codex_name", "toggleHideCodex:", target=app,
            state=_hide_codex_enabled(),
        )
    )
    hide_submenu.addItem_(
        build_menu_item(
            app.language, "agy_name", "toggleHideAgy:", target=app,
            state=_hide_agy_enabled(),
        )
    )
    hide_submenu.addItem_(
        build_menu_item(
            app.language, "grok_name", "toggleHideGrok:", target=app,
            state=_hide_grok_enabled(),
        )
    )
    hide_submenu.addItem_(
        build_menu_item(
            app.language, "deepseek_name", "toggleHideDeepSeek:", target=app,
            state=_hide_deepseek_enabled(),
        )
    )
    hide_submenu.addItem_(
        build_menu_item(
            app.language, "manus_name", "toggleHideManus:", target=app,
            state=_hide_manus_enabled(),
        )
    )
    hide_submenu.addItem_(
        build_menu_item(
            app.language, "duoyuanx_name", "toggleHideDuoyuanX:", target=app,
            state=_hide_duoyuanx_enabled(),
        )
    )
    hide_submenu.addItem_(NSMenuItem.separatorItem())
    hide_submenu.addItem_(
        build_menu_item(
            app.language, "hide_projects", "toggleHideProjects:", target=app,
            state=_hide_projects_enabled(),
        )
    )
    hide_submenu.addItem_(
        build_menu_item(
            app.language, "hide_footer", "toggleHideFooter:", target=app,
            state=_hide_footer_enabled(),
        )
    )
    hide_parent = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        _t(app.language, "hide_sections_menu"), "", ""
    )
    hide_parent.setSubmenu_(hide_submenu)
    menu.addItem_(hide_parent)

    # Menubar Visibility Submenu ("hide menubas"): allows toggling any AI tool in the top menubar independently
    menubar_submenu = NSMenu.alloc().initWithTitle_(_t(app.language, "menubar_visibility_menu"))
    menubar_submenu.addItem_(
        build_menu_item(
            app.language, "claude_name", "toggleMenubarProvider:", target=app,
            represented="claude",
            state=_menubar_provider_visible("claude"),
        )
    )
    menubar_submenu.addItem_(
        build_menu_item(
            app.language, "codex_name", "toggleMenubarProvider:", target=app,
            represented="codex",
            state=_menubar_provider_visible("codex"),
        )
    )
    menubar_submenu.addItem_(
        build_menu_item(
            app.language, "agy_name", "toggleMenubarProvider:", target=app,
            represented="agy",
            state=_menubar_provider_visible("agy"),
        )
    )
    menubar_submenu.addItem_(
        build_menu_item(
            app.language, "grok_name", "toggleMenubarProvider:", target=app,
            represented="grok",
            state=_menubar_provider_visible("grok"),
        )
    )
    menubar_submenu.addItem_(
        build_menu_item(
            app.language, "deepseek_name", "toggleMenubarProvider:", target=app,
            represented="deepseek",
            state=_menubar_provider_visible("deepseek"),
        )
    )
    menubar_submenu.addItem_(
        build_menu_item(
            app.language, "manus_name", "toggleMenubarProvider:", target=app,
            represented="manus",
            state=_menubar_provider_visible("manus"),
        )
    )
    menubar_submenu.addItem_(
        build_menu_item(
            app.language, "duoyuanx_name", "toggleMenubarProvider:", target=app,
            represented="duoyuanx",
            state=_menubar_provider_visible("duoyuanx"),
        )
    )
    menubar_parent = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        _t(app.language, "menubar_visibility_menu"), "", ""
    )
    menubar_parent.setSubmenu_(menubar_submenu)
    menu.addItem_(menubar_parent)

    menu.addItem_(
        build_menu_item(
            app.language, "configure_deepseek", "configureDeepSeek:", target=app,
        )
    )
    menu.addItem_(
        build_menu_item(
            app.language, "configure_manus", "configureManus:", target=app,
        )
    )
    menu.addItem_(
        build_menu_item(
            app.language, "configure_duoyuanx", "configureDuoyuanX:", target=app,
        )
    )
    # Plain on/off switches sit together in the second group.
    menu.addItem_(NSMenuItem.separatorItem())
    menu.addItem_(
        build_menu_item(
            app.language, "launch_at_login", "toggleLaunchAtLogin:", target=app,
            state=login_item.is_enabled(),
        )
    )
    menu.addItem_(
        build_menu_item(
            app.language, "quota_notifications_menu", "toggleQuotaNotifications:", target=app,
            state=_quota_notifications_enabled(),
        )
    )
    menu.addItem_(
        build_menu_item(
            app.language, "window_keeper_menu", "toggleWindowKeeper:", target=app,
            state=_window_keeper_enabled(),
            tooltip_key="window_keeper_tooltip",
        )
    )
    # Project Butler: one toggle that hands last session's progress to the next
    # one. Tooltip carries the full explanation so the menu line stays short.
    # Grouped with the plain switches above it — a separate section here just
    # added a divider with no real category difference.
    menu.addItem_(
        build_menu_item(
            app.language, "project_butler", "toggleSessionResume:", target=app,
            state=_session_resume_enabled(),
            tooltip_key="project_butler_tooltip",
        )
    )
    menu.addItem_(
        build_menu_item(
            app.language, "terse_mode_menu", "toggleTerseMode:", target=app,
            state=_terse_mode_enabled(),
            tooltip_key="terse_mode_tooltip",
        )
    )
    app._switch_menu_action_taken = False
    menu.popUpMenuPositioningItem_atLocation_inView_(None, NSMakePoint(0, 0), sender)
    # Dismissing the menu without picking anything used to close the panel:
    # a transient popover was already gone by then, so closing it was just
    # cleanup. The floating window survives the menu, so the same call would
    # read as "cancelling the menu threw my panel away".
    app._resync_popover_after_menu()
