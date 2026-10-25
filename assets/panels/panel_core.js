    const defaultPanelHooks = {
      accentFallback(cardEl, computedAccent) {
        return computedAccent;
      },
      applyFillVisual(fillEl, { available, percent, color }) {
        fillEl.style.width = available ? `${Math.max(0, Math.min(100, percent))}%` : "0%";
        fillEl.style.setProperty("--fill-color", color);
      },
      projectRankLabels: ["1", "2", "3"],
      renderProjectRow(p, index, ranks) {
        const row = document.createElement("div");
        row.className = "proj-row";
        const rank = document.createElement("span");
        rank.className = "proj-rank";
        rank.textContent = ranks[index];
        const name = document.createElement("span");
        name.className = "proj-name";
        name.textContent = p.name || "";
        const tok = document.createElement("span");
        tok.className = "proj-tokens";
        tok.textContent = p.tokensText || "";
        const cost = document.createElement("span");
        cost.className = "proj-cost";
        cost.textContent = p.costText || "";
        const bar = document.createElement("div");
        bar.className = "proj-bar";
        const fill = document.createElement("div");
        fill.className = "proj-bar-fill";
        fill.style.width = `${p.sharePercent}%`;
        bar.append(fill);
        row.append(rank, name, tok, cost, bar);
        return row;
      },
      switchButtonStrategy(state) {
        const buttons = document.querySelectorAll('[data-action="switch"]');
        for (let i = 1; i < buttons.length; i++) {
          buttons[i].remove();
        }
        const button = buttons[0];
        if (!button) return;

        function findCardHeader(cardId) {
          const card = document.querySelector(`[data-card="${cardId}"]`);
          return card ? card.querySelector(".brand, .header, header") : null;
        }
        function isHidden(cardId) {
          if (!state) return false;
          if (cardId === "claude") return !!state.hideClaude;
          if (cardId === "codex") return !!state.hideCodex;
          if (cardId === "agy") return !!state.hideAgy;
          if (cardId === "grok") return !!state.hideGrok;
          if (cardId === "deepseek") return !!state.hideDeepseek || (!state.deepseek || !state.deepseek.configured);
          if (cardId === "projects") return !!state.hideProjects;
          return false;
        }

        const order = Array.isArray(state?.cardOrder) && state.cardOrder.length
          ? state.cardOrder
          : ["claude", "codex", "agy", "grok", "deepseek"];

        let host = null;
        let className = "switch";

        for (const id of order) {
          if (!isHidden(id)) {
            host = findCardHeader(id);
            if (host) break;
          }
        }
        if (!host) {
          for (const id of ["claude", "codex", "agy", "grok", "deepseek"]) {
            if (!isHidden(id)) {
              host = findCardHeader(id);
              if (host) break;
            }
          }
        }
        if (!host && !isHidden("projects")) {
          host = findCardHeader("projects");
        }
        if (!host && !state?.hideFooter) {
          host = document.querySelector(".footer .actions, .footer");
          className = "action";
        }
        if (!host) {
          host = document.querySelector("main.wrap") || document.body;
          className = "switch floating-switch";
        }

        if (!host) return;
        button.className = className;
        button.style.display = "";
        if (button.parentElement !== host) host.appendChild(button);
      },
      pointerdownExcludeSelector: "button, a, .codex-stale-info",
    };

    if (!window.PanelHooks || typeof window.PanelHooks !== "object") {
      window.PanelHooks = {};
    }
    Object.entries(defaultPanelHooks).forEach(([name, defaultValue]) => {
      if (window.PanelHooks[name] === undefined) {
        window.PanelHooks[name] = defaultValue;
      }
    });

    const I18N = {{I18N_BUNDLE}};
    const FALLBACK_LANGUAGE = "en";
    const root = document.documentElement;
    const switchHostStyle = document.createElement("style");
    switchHostStyle.textContent = `
      [data-card="codex"] .usage-switch-host > h1,
      [data-card="codex"] .usage-switch-host > .header-copy {
        flex: 0 0 auto !important;
        min-width: max-content !important;
        overflow: visible !important;
      }
      [data-card="codex"] .usage-switch-host > [data-codex-stale] {
        flex: 1 1 0 !important;
        min-width: 0 !important;
        overflow: hidden !important;
      }
      [data-card="codex"] .usage-switch-host [data-codex-stale-age] {
        display: block;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      [data-card="agy"] .usage-switch-host > h1,
      [data-card="agy"] .usage-switch-host > .header-copy {
        flex: 0 0 auto !important;
        min-width: max-content !important;
        overflow: visible !important;
      }
      [data-card="agy"] .usage-switch-host > [data-agy-stale] {
        flex: 1 1 0 !important;
        min-width: 0 !important;
        overflow: hidden !important;
      }
      [data-card="agy"] .usage-switch-host [data-agy-stale-age] {
        display: block;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      [data-card="grok"] .usage-switch-host > h1,
      [data-card="grok"] .usage-switch-host > .header-copy {
        flex: 0 0 auto !important;
        min-width: max-content !important;
        overflow: visible !important;
      }
      [data-card="grok"] .usage-switch-host > [data-grok-stale] {
        flex: 1 1 0 !important;
        min-width: 0 !important;
        overflow: hidden !important;
      }
      [data-card="grok"] .usage-switch-host [data-grok-stale-age] {
        display: block;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .usage-switch-host [data-action="switch"] {
        margin-left: auto !important;
        flex: 0 0 auto !important;
      }
      button.floating-switch[data-action="switch"] {
        position: fixed !important;
        top: 8px !important;
        right: 8px !important;
        z-index: 99999 !important;
      }
      [data-card="grok"] { cursor: grab; }
      [data-card="deepseek"] .usage-switch-host > h1,
      [data-card="deepseek"] .usage-switch-host > .header-copy {
        flex: 0 0 auto !important;
        min-width: max-content !important;
        overflow: visible !important;
      }
      [data-card="deepseek"] { cursor: grab; }
      .hide-deepseek [data-card="deepseek"] { display: none !important; }
    `;
    document.head.appendChild(switchHostStyle);
    let currentLanguage = "en";
    let projectRange = "1d";
    let latestState = null;

    function languageTable(language) {
      return I18N[language] || I18N[FALLBACK_LANGUAGE] || {};
    }

    function t(key, params = {}) {
      const template = languageTable(currentLanguage)[key] || languageTable(FALLBACK_LANGUAGE)[key] || key;
      return template.replace(/\{(\w+)\}/g, (_, name) => `${params[name] ?? ""}`);
    }

    function labels() {
      return {
        session: t("session_label"),
        weekly: t("weekly_label"),
      };
    }

    function projectRangeLabel(range) {
      if (range === "yesterday") return t("project_range_yesterday");
      if (range === "7d") return t("project_range_7d");
      if (range === "30d") return t("project_range_30d");
      if (range === "all") return t("project_range_all");
      return t("project_range_1d");
    }

    function applyStaticText() {
      document.documentElement.lang = currentLanguage === "zh-TW" ? "zh-Hant" : currentLanguage;
      document.querySelectorAll("[data-i18n]").forEach((node) => {
        const key = node.dataset.i18n;
        if (key) node.textContent = t(key);
      });
      const rangeButton = document.querySelector('[data-action="toggle-project-range"]');
      if (rangeButton) rangeButton.textContent = projectRangeLabel(projectRange);
    }

    window.usageSetLanguage = function usageSetLanguage(language) {
      currentLanguage = I18N[language] ? language : FALLBACK_LANGUAGE;
      applyStaticText();
      if (latestState) {
        window.usageApplyState({ ...latestState, language: currentLanguage });
      }
    };

    function cssVar(name) {
      return getComputedStyle(root).getPropertyValue(name).trim();
    }

    // Panels may draw a critical halo past this; colorFor's 80% only turns text red.
    const CRITICAL_PERCENT = 90;

    function colorFor(percent, fallback) {
      if (typeof percent !== "number") return fallback;
      if (percent >= 80) return cssVar("--danger");
      if (percent >= 50) return cssVar("--warn");
      return fallback;
    }

    function renderRow(card, key, row) {
      const el = document.querySelector(`[data-card="${card}"] [data-row="${key}"]`);
      if (!el) return;
      el.hidden = card === "codex" && !row;
      if (el.hidden) return;
      const cardEl = el.closest(".card");
      if (!cardEl) return;
      const data = row || {
        percent: null,
        percentText: "--",
        resetText: t("reset_placeholder"),
        warning: false,
        available: false,
      };
      const available = data.available === true && typeof data.percent === "number";
      const accent = window.PanelHooks.accentFallback(
        cardEl,
        getComputedStyle(cardEl).getPropertyValue("--accent").trim()
      );
      const color = colorFor(data.percent, accent);
      el.dataset.available = available ? "true" : "false";
      if (el.dataset.rowReady !== "true") {
        el.innerHTML = `
          <div class="row-head">
            <div class="row-title"></div>
            <div class="percent"></div>
          </div>
          <div class="track"><div class="fill"></div></div>
          <div class="reset"></div>
        `;
        el.dataset.rowReady = "true";
      }
      const title = el.querySelector(".row-title");
      const percent = el.querySelector(".percent");
      const reset = el.querySelector(".reset");
      const fill = el.querySelector(".fill");
      if (!title || !percent || !reset || !fill) return;
      title.textContent = data.title != null ? data.title : labels()[key];
      if (available && typeof data.percent === "number") {
        const remaining = Math.max(0, 100 - data.percent);
        const remFormatted = Number.isInteger(remaining) ? remaining : remaining.toFixed(1);
        percent.textContent = `剩余 ${remFormatted}%`;
      } else {
        percent.textContent = data.percentText || "--";
      }
      reset.textContent = data.resetText || t("reset_placeholder");
      reset.dataset.warning = data.warning === true ? "true" : "false";
      percent.style.color = available ? color : "";
      window.PanelHooks.applyFillVisual(fill, { available, percent: data.percent, color });
    }

    function isCriticalRow(row) {
      return Boolean(row)
        && row.available === true
        && typeof row.percent === "number"
        && row.percent >= CRITICAL_PERCENT;
    }

    function applyCard(name, rows) {
      renderRow(name, "session", rows && rows.session);
      renderRow(name, "weekly", rows && rows.weekly);
      const cardEl = document.querySelector(`.card[data-card="${name}"]`);
      if (!cardEl) return;
      const critical = isCriticalRow(rows && rows.session)
        || isCriticalRow(rows && rows.weekly);
      cardEl.dataset.critical = critical ? "true" : "false";
    }

    function renderCodexStale(stale) {
      const staleEl = document.querySelector("[data-codex-stale]");
      const ageEl = document.querySelector("[data-codex-stale-age]");
      const tooltipEl = document.querySelector("[data-codex-stale-tooltip]");
      if (!staleEl || !ageEl || !tooltipEl) return;
      if (stale && stale.ageText) {
        ageEl.textContent = stale.ageText;
        tooltipEl.textContent = t("codex_stale_tooltip");
        staleEl.hidden = false;
        return;
      }
      ageEl.textContent = "";
      tooltipEl.textContent = "";
      staleEl.hidden = true;
    }

    function renderCodexCredits(credits) {
      const card = document.querySelector('[data-card="codex"]');
      if (!card) return;
      const existing = card.querySelector('[data-codex-credits]');
      if (!credits) {
        if (existing) existing.remove();
        return;
      }
      const el = existing || document.createElement("div");
      if (!existing) {
        el.className = "codex-credits";
        el.dataset.codexCredits = "";
        card.appendChild(el);
      }
      el.textContent = credits.unlimited
        ? t("codex_credits_unlimited")
        : t("codex_credits", { balance: credits.balance || "--" });
    }

    function renderAgy(agy) {
      applyCard("agy", agy);
      const staleEl = document.querySelector("[data-agy-stale]");
      const ageEl = document.querySelector("[data-agy-stale-age]");
      const tooltipEl = document.querySelector("[data-agy-stale-tooltip]");
      if (!staleEl || !ageEl || !tooltipEl) return;
      if (agy && agy.stale && agy.stale.ageText) {
        ageEl.textContent = agy.stale.ageText;
        tooltipEl.textContent = t("agy_stale_tooltip");
        staleEl.hidden = false;
        return;
      }
      ageEl.textContent = "";
      tooltipEl.textContent = "";
      staleEl.hidden = true;
    }

    function renderGrok(grok) {
      applyCard("grok", grok);
      const staleEl = document.querySelector("[data-grok-stale]");
      const ageEl = document.querySelector("[data-grok-stale-age]");
      const tooltipEl = document.querySelector("[data-grok-stale-tooltip]");
      if (!staleEl || !ageEl || !tooltipEl) return;
      if (grok && grok.stale && grok.stale.ageText) {
        ageEl.textContent = grok.stale.ageText;
        tooltipEl.textContent = t("grok_stale_tooltip");
        staleEl.hidden = false;
        return;
      }
      ageEl.textContent = "";
      tooltipEl.textContent = "";
      staleEl.hidden = true;
    }

    function ensureDeepSeekCard() {
      let card = document.querySelector('[data-card="deepseek"]');
      if (card) return card;
      const wrap = document.querySelector("main.wrap");
      if (!wrap) return null;
      card = document.createElement("section");
      card.className = "card";
      card.dataset.card = "deepseek";
      card.style.setProperty("--accent", "#4D6BFE");
      card.innerHTML = `
        <header class="header brand" style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
          <div class="brand-icon deepseek-icon" aria-hidden="true" style="display:flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:50%;background:rgba(77,107,254,0.15);color:#4D6BFE;flex:none;">
            <svg fill="currentColor" viewBox="0 0 24 24" width="18" height="18" xmlns="http://www.w3.org/2000/svg">
              <path d="M23.748 4.482c-.254-.124-.364.113-.512.234-.051.039-.094.09-.137.136-.372.397-.806.657-1.373.626-.829-.046-1.537.214-2.163.848-.133-.782-.575-1.248-1.247-1.548-.352-.156-.708-.311-.955-.65-.172-.241-.219-.51-.305-.774-.055-.16-.11-.323-.293-.35-.2-.031-.278.136-.356.276-.313.572-.434 1.202-.422 1.84.027 1.436.633 2.58 1.838 3.393.137.093.172.187.129.323-.082.28-.18.552-.266.833-.055.179-.137.217-.329.14a5.526 5.526 0 0 1-1.736-1.18c-.857-.828-1.631-1.742-2.597-2.458a11.365 11.365 0 0 0-.689-.471c-.985-.957.13-1.743.388-1.836.27-.098.093-.432-.779-.428-.872.004-1.67.295-2.687.684a3.055 3.055 0 0 1-.465.137 9.597 9.597 0 0 0-2.883-.102c-1.885.21-3.39 1.102-4.497 2.623C.082 8.606-.231 10.684.152 12.85c.403 2.284 1.569 4.175 3.36 5.653 1.858 1.533 3.997 2.284 6.438 2.14 1.482-.085 3.133-.284 4.994-1.86.47.234.962.327 1.78.397.63.059 1.236-.03 1.705-.128.735-.156.684-.837.419-.961-2.155-1.004-1.682-.595-2.113-.926 1.096-1.296 2.746-2.642 3.392-7.003.05-.347.007-.565 0-.845-.004-.17.035-.237.23-.256a4.173 4.173 0 0 0 1.545-.475c1.396-.763 1.96-2.015 2.093-3.517.02-.23-.004-.467-.247-.588zM11.581 18c-2.089-1.642-3.102-2.183-3.52-2.16-.392.024-.321.471-.235.763.09.288.207.486.371.739.114.167.192.416-.113.603-.673.416-1.842-.14-1.897-.167-1.361-.802-2.5-1.86-3.301-3.307-.774-1.393-1.224-2.887-1.298-4.482-.02-.386.093-.522.477-.592a4.696 4.696 0 0 1 1.529-.039c2.132.312 3.946 1.265 5.468 2.774.868.86 1.525 1.887 2.202 2.891.72 1.066 1.494 2.082 2.48 2.914.348.292.625.514.891.677-.802.09-2.14.11-3.054-.614zm1-6.44a.306.306 0 0 1 .415-.287.302.302 0 0 1 .2.288.302.302 0 0 1-.31.307.303.303 0 0 1-.304-.308zm3.11 1.596c-.2.081-.399.151-.59.16a1.245 1.245 0 0 1-.598-.052z"/>
            </svg>
          </div>
          <div class="header-copy" style="min-width:0;flex:1;">
            <h1 data-i18n="deepseek_name" style="margin:0;font-size:16px;font-weight:600;">DeepSeek</h1>
          </div>
          <div class="deepseek-badge" data-deepseek-balance style="font-weight:700;font-size:14px;color:#4D6BFE;margin-left:auto;white-space:nowrap;">--</div>
        </header>
        <div class="row" data-row="deepseek-details" style="display:flex;justify-content:space-between;gap:8px;padding:4px 0;font-size:12px;opacity:0.85;">
          <span data-deepseek-topped-up></span>
          <span data-deepseek-granted></span>
        </div>
      `;
      const projects = document.querySelector('[data-card="projects"]');
      if (projects) {
        wrap.insertBefore(card, projects);
      } else {
        wrap.appendChild(card);
      }
      return card;
    }

    function renderDeepSeek(deepseek) {
      if (!deepseek || !deepseek.configured) {
        const card = document.querySelector('[data-card="deepseek"]');
        if (card) card.style.display = "none";
        return;
      }
      const card = ensureDeepSeekCard();
      if (!card) return;
      card.style.display = "";

      const balEl = card.querySelector('[data-deepseek-balance]');
      if (balEl) {
        balEl.textContent = deepseek.formattedBalance || "--";
      }

      const toppedEl = card.querySelector('[data-deepseek-topped-up]');
      if (toppedEl) {
        if (deepseek.toppedUp) {
          toppedEl.textContent = `${t("deepseek_topped_up")}: ${deepseek.toppedUp}`;
          toppedEl.style.display = "";
        } else {
          toppedEl.style.display = "none";
        }
      }

      const grantedEl = card.querySelector('[data-deepseek-granted]');
      if (grantedEl) {
        if (deepseek.granted) {
          grantedEl.textContent = `${t("deepseek_granted")}: ${deepseek.granted}`;
          grantedEl.style.display = "";
        } else {
          grantedEl.style.display = "none";
        }
      }

      const detailsRow = card.querySelector('[data-row="deepseek-details"]');
      if (detailsRow) {
        if (!deepseek.toppedUp && !deepseek.granted) {
          if (deepseek.errorMessage) {
            detailsRow.innerHTML = `<span style="color:#f87171;font-size:11px;">${deepseek.errorMessage}</span>`;
            detailsRow.style.display = "";
          } else {
            detailsRow.style.display = "none";
          }
        } else {
          detailsRow.style.display = "flex";
        }
      }
    }

    function ensureManusCard() {
      let card = document.querySelector('[data-card="manus"]');
      if (card) return card;
      const wrap = document.querySelector("main.wrap");
      if (!wrap) return null;
      card = document.createElement("section");
      card.className = "card";
      card.dataset.card = "manus";
      card.style.setProperty("--accent", "#E87A40");
      card.innerHTML = `
        <header class="header brand" style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
          <div class="brand-icon manus-icon" aria-hidden="true" style="display:flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:8px;background:rgba(232,122,64,0.15);color:#E87A40;flex:none;overflow:hidden;">
            <img src="../manus_color_menubar.png" width="22" height="22" style="border-radius:5px;object-fit:cover;" alt="Manus" />
          </div>
          <div class="header-copy" style="min-width:0;flex:1;">
            <div style="display:flex;align-items:center;gap:6px;">
              <h1 data-i18n="manus_name" style="margin:0;font-size:16px;font-weight:600;">Manus</h1>
              <span class="manus-plan-badge" data-manus-plan style="font-size:11px;font-weight:600;padding:1px 6px;border-radius:4px;background:rgba(232,122,64,0.18);color:#E87A40;">PRO</span>
            </div>
          </div>
          <div class="manus-badge" data-manus-credits style="font-weight:700;font-size:15px;color:#E87A40;margin-left:auto;white-space:nowrap;">--</div>
        </header>
        <div class="reset" data-manus-reset></div>
      `;
      const projects = document.querySelector('[data-card="projects"]');
      if (projects) {
        wrap.insertBefore(card, projects);
      } else {
        wrap.appendChild(card);
      }
      return card;
    }

    function renderManus(manus) {
      if (!manus || (!manus.configured && !manus.available)) {
        const card = document.querySelector('[data-card="manus"]');
        if (card) card.style.display = "none";
        return;
      }
      const card = ensureManusCard();
      if (!card) return;
      card.style.display = "";

      // Remove points breakdown if previously present
      const oldDetails = card.querySelector('[data-row="manus-details"]');
      if (oldDetails) oldDetails.remove();

      const creditsEl = card.querySelector('[data-manus-credits]');
      if (creditsEl) {
        if (manus.secondaryFormattedCredits) {
          const p = manus.primaryCredits != null ? Number(manus.primaryCredits).toLocaleString() : (manus.formattedCredits || "--");
          creditsEl.textContent = `${p} / ${manus.secondaryFormattedCredits} ${t("credits_unit") || "点"}`;
        } else {
          creditsEl.textContent = (manus.formattedCredits || "--") + " " + (t("credits_unit") || "点");
        }
      }

      const planEl = card.querySelector('[data-manus-plan]');
      if (planEl) {
        planEl.textContent = (manus.membershipVersion ? manus.membershipVersion.toUpperCase() : "PRO");
      }

      let resetEl = card.querySelector('[data-manus-reset]');
      if (!resetEl) {
        resetEl = document.createElement("div");
        resetEl.className = "reset";
        resetEl.dataset.manusReset = "";
        card.appendChild(resetEl);
      }

      if (manus.errorMessage) {
        resetEl.textContent = manus.errorMessage;
        resetEl.style.color = "#f87171";
        resetEl.style.display = "";
      } else if (manus.secondaryFormattedCredits) {
        const p = manus.primaryCredits != null ? Number(manus.primaryCredits).toLocaleString() : "--";
        const n1 = manus.userName || "manus-nick";
        const n2 = manus.secondaryUserName || "manus-zzn";
        let multiInfo = `${n1}: ${p} 点 · ${n2}: ${manus.secondaryFormattedCredits} 点`;
        if (manus.resetText) multiInfo += ` · ${manus.resetText}`;
        resetEl.textContent = multiInfo;
        resetEl.style.color = "";
        resetEl.style.display = "";
      } else if (manus.resetText) {
        resetEl.textContent = manus.resetText;
        resetEl.style.color = "";
        resetEl.style.display = "";
      } else {
        resetEl.textContent = "";
        resetEl.style.display = "none";
      }
    }

    function ensureDuoyuanxCard() {
      let card = document.querySelector('[data-card="duoyuanx"]');
      if (card) return card;
      const wrap = document.querySelector("main.wrap");
      if (!wrap) return null;
      card = document.createElement("section");
      card.className = "card";
      card.dataset.card = "duoyuanx";
      card.style.setProperty("--accent", "#2563EB");
      card.innerHTML = `
        <header class="header brand" style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
          <div class="brand-icon duoyuanx-icon" aria-hidden="true" style="display:flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:8px;background:rgba(37,99,235,0.15);color:#2563EB;flex:none;overflow:hidden;">
            <svg fill="currentColor" viewBox="0 0 26 17" width="20" height="14" xmlns="http://www.w3.org/2000/svg">
              <path d="M0.407 0L5.25 0L13.17 12.255L8.389 12.255L0.407 0Z"/>
              <path d="M6.612 0L11.515 0L12.68 1.97C12.53 2.799 12.136 3.569 11.514 4.225L10.966 4.805L11.745 4.633C12.756 4.411 13.739 4.521 14.614 4.94L19.376 12.255L14.594 12.255L6.612 0Z"/>
              <path d="M0 6.866L3.974 6.866L3.974 12.255L0 12.255L0 6.866Z"/>
            </svg>
          </div>
          <div class="header-copy" style="min-width:0;flex:1;">
            <div style="display:flex;align-items:center;gap:6px;">
              <h1 data-i18n="duoyuanx_name" style="margin:0;font-size:16px;font-weight:600;">多元X</h1>
              <span style="font-size:11px;font-weight:600;padding:1px 6px;border-radius:4px;background:rgba(37,99,235,0.18);color:#2563EB;">API</span>
            </div>
          </div>
          <div class="duoyuanx-badge" data-duoyuanx-balance style="font-weight:700;font-size:14px;color:#2563EB;margin-left:auto;white-space:nowrap;">--</div>
        </header>
        <div class="row" data-row="duoyuanx-details" style="display:flex;justify-content:space-between;gap:8px;padding:4px 0;font-size:12px;opacity:0.85;">
          <span data-duoyuanx-sub></span>
          <span data-duoyuanx-used></span>
        </div>
      `;
      const projects = document.querySelector('[data-card="projects"]');
      if (projects) {
        wrap.insertBefore(card, projects);
      } else {
        wrap.appendChild(card);
      }
      return card;
    }

    function renderDuoyuanx(duoyuanx) {
      if (!duoyuanx || !duoyuanx.configured) {
        const card = document.querySelector('[data-card="duoyuanx"]');
        if (card) card.style.display = "none";
        return;
      }
      const card = ensureDuoyuanxCard();
      if (!card) return;
      card.style.display = "";

      const balEl = card.querySelector('[data-duoyuanx-balance]');
      if (balEl) {
        balEl.textContent = duoyuanx.formattedBalance || "--";
      }

      const subEl = card.querySelector('[data-duoyuanx-sub]');
      if (subEl) {
        const quotaFmt = duoyuanx.totalAvailableQuota ? Number(duoyuanx.totalAvailableQuota).toLocaleString() : "0";
        subEl.textContent = `${duoyuanx.name ? duoyuanx.name + " · " : ""}${quotaFmt} 配额`;
      }

      const usedEl = card.querySelector('[data-duoyuanx-used]');
      if (usedEl) {
        usedEl.textContent = `${t("duoyuanx_used") || "已用"}: ${duoyuanx.formattedUsed || "$0.00"}`;
      }
    }

    function renderHistoryLoadError(err) {
      const el = document.querySelector("[data-history-error]");
      const textEl = document.querySelector("[data-history-error-text]");
      const tooltipEl = document.querySelector("[data-history-error-tooltip]");
      if (!el || !textEl || !tooltipEl) return;
      if (err && err.reasonText) {
        textEl.textContent = err.reasonText;
        tooltipEl.textContent = t("history_load_error_tooltip");
        el.hidden = false;
        return;
      }
      textEl.textContent = "";
      tooltipEl.textContent = "";
      el.hidden = true;
    }

    function renderProjects(projects) {
      const list = document.querySelector('[data-project-list]');
      if (!list) return;
      const ranks = window.PanelHooks.projectRankLabels;
      const rows = (projects || []).slice(0, 3);
      const totalTokens = rows.reduce((s, p) => s + Math.max(0, Number(p.tokens) || 0), 0);
      list.replaceChildren();
      if (rows.length === 0) {
        const empty = document.createElement("div");
        empty.style.cssText = "color:var(--muted);font-size:13px;padding:8px 0";
        empty.textContent = t("projects_empty");
        list.append(empty);
        return;
      }
      rows.forEach((p, i) => {
        const tokens = Math.max(0, Number(p.tokens) || 0);
        const width = totalTokens > 0 ? Math.max(0, Math.min(100, (tokens / totalTokens) * 100)) : 0;
        const row = window.PanelHooks.renderProjectRow({ ...p, sharePercent: width }, i, ranks);
        if (row) list.append(row);
      });
    }

    function renderPeriodTotal(state) {
      const total = document.querySelector('[data-footer="today"]');
      if (!total) return;
      total.textContent = projectRange === "yesterday"
        ? (state.footer.yesterday || t("yesterday_text", { cost: "0.00", tokens: "0" }))
        : (state.footer.today || t("today_text", { cost: "0.00", tokens: "0" }));
    }





    function renderStatusline(statusline) {
      const data = statusline || {};
      const button = document.querySelector('[data-action="toggle-statusline"]');
      if (button) {
        const enabled = data.enabled === true;
        button.dataset.active = enabled ? "true" : "false";
        button.textContent = enabled ? t("cli_enabled") : t("cli_disabled");
      }
    }

    function relocateSwitchButton(state) {
      document.querySelectorAll(".usage-switch-host").forEach((host) => {
        host.classList.remove("usage-switch-host");
      });
      window.PanelHooks.switchButtonStrategy(state);
      const button = document.querySelector('[data-action="switch"]');
      const host = button && button.parentElement;
      if (host) {
        host.classList.add("usage-switch-host");
      }
    }

    const QUOTA_CARD_IDS = ["claude", "codex", "agy", "grok", "deepseek", "manus"];

    function applyCardOrder(order) {
      if (cardDrag && cardDrag.dragging) return;
      if (!Array.isArray(order) || order.length !== QUOTA_CARD_IDS.length || new Set(order).size !== QUOTA_CARD_IDS.length || !order.every((id) => QUOTA_CARD_IDS.includes(id))) return;
      const wrap = document.querySelector("main.wrap");
      const projects = document.querySelector('[data-card="projects"]');
      if (!wrap || !projects) return;
      const currentOrder = [...wrap.querySelectorAll(':scope > [data-card]')]
        .filter((card) => QUOTA_CARD_IDS.includes(card.dataset.card))
        .map((card) => card.dataset.card);
      if (order.every((id, index) => currentOrder[index] === id)) return;
      order.forEach((id) => {
        const card = document.querySelector(`[data-card="${id}"]`);
        if (card) wrap.insertBefore(card, projects);
      });
    }

    const hideSectionsStyle = document.createElement("style");
    hideSectionsStyle.textContent = `
      html.hide-deepseek [data-card="deepseek"],
      .hide-deepseek [data-card="deepseek"] {
        display: none !important;
      }
      html.hide-manus [data-card="manus"],
      .hide-manus [data-card="manus"] {
        display: none !important;
      }
      html.hide-duoyuanx [data-card="duoyuanx"],
      .hide-duoyuanx [data-card="duoyuanx"] {
        display: none !important;
      }
      html.hide-projects [data-card="projects"],
      .hide-projects [data-card="projects"] {
        display: none !important;
      }
      html.hide-footer .footer,
      .hide-footer .footer {
        display: none !important;
      }
    `;
    (document.head || document.documentElement).appendChild(hideSectionsStyle);

    window.usageApplyState = function usageApplyState(state) {
      if (typeof state.system_accent_color === "string" && state.system_accent_color) {
        root.style.setProperty("--usage-system-accent", state.system_accent_color);
      } else {
        root.style.removeProperty("--usage-system-accent");
      }
      document.documentElement.classList.toggle('hide-codex', !!state.hideCodex);
      document.documentElement.classList.toggle('hide-claude', !!state.hideClaude);
      document.documentElement.classList.toggle('hide-agy', !!state.hideAgy);
      document.documentElement.classList.toggle('hide-grok', !!state.hideGrok);
      document.documentElement.classList.toggle('hide-deepseek', !!state.hideDeepseek);
      document.documentElement.classList.toggle('hide-manus', !!state.hideManus);
      document.documentElement.classList.toggle('hide-duoyuanx', !!state.hideDuoyuanx);
      document.documentElement.classList.toggle('hide-projects', !!state.hideProjects);
      document.documentElement.classList.toggle('hide-footer', !!state.hideFooter);
      applyCardOrder(state.cardOrder);
      relocateSwitchButton(state);
      currentLanguage = I18N[state.language] ? state.language : currentLanguage;
      applyStaticText();
      applyCard("claude", state.claude);
      applyCard("codex", state.codex);
      renderCodexStale(state.codex && state.codex.stale);
      renderCodexCredits(state.codex && state.codex.credits);
      renderAgy(state.agy);
      renderGrok(state.grok);
      renderDeepSeek(state.deepseek);
      renderManus(state.manus);
      renderDuoyuanx(state.duoyuanx);
      renderHistoryLoadError(state.historyError);
      latestState = state;
      renderProjects(
        projectRange === "1d" ? state.projects
        : projectRange === "yesterday" ? state.projectsYesterday
        : projectRange === "7d" ? state.projects7d
        : projectRange === "30d" ? state.projects30d
        : projectRange === "all" ? state.projectsAll
        : state.projects
      );
      renderStatusline(state.statusline || {});
      const rate = document.querySelector('[data-footer="rate"]');
      const status = document.querySelector('[data-footer="status"]');
      const serviceAlerts = document.querySelector('[data-footer="service-alerts"]');
      const install = document.querySelector('[data-action="install"]');
      if (rate) rate.textContent = state.footer.rate || t("rate_text", { value: "--" });
      if (status) status.textContent = state.footer.status || t("status_text", { value: "--" });
      renderPeriodTotal(state);
      if (install) install.dataset.visible = state.footer.showInstall === true ? "true" : "false";
      if (serviceAlerts) {
        const alerts = state.footer.serviceAlerts || [];
        serviceAlerts.replaceChildren(...alerts.slice(0, 2).map((alert) => {
          const item = document.createElement("div");
          item.className = "service-alert";
          item.textContent = alert;
          return item;
        }));
        serviceAlerts.hidden = alerts.length === 0;
      }
    };

    document.addEventListener("click", (event) => {
      const button = event.target.closest("[data-action]");
      if (!button) return;
      if (button.dataset.action === "toggle-project-range") {
        projectRange = projectRange === "1d" ? "yesterday" : projectRange === "yesterday" ? "7d" : projectRange === "7d" ? "30d" : projectRange === "30d" ? "all" : "1d";
        button.textContent = projectRangeLabel(projectRange);
        if (latestState) {
          renderProjects(
            projectRange === "1d" ? latestState.projects
            : projectRange === "yesterday" ? latestState.projectsYesterday
            : projectRange === "7d" ? latestState.projects7d
            : projectRange === "30d" ? latestState.projects30d
            : projectRange === "all" ? latestState.projectsAll
            : latestState.projects
          );
          renderPeriodTotal(latestState);
          if (typeof window.usageRequestContentHeight === "function") {
            window.usageRequestContentHeight();
          }
        }
        return;
      }
      const bridge = window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.usage;
      if (bridge && typeof bridge.postMessage === "function") {
        bridge.postMessage(button.dataset.action);
      }
    });

    let mouseLeaveTimer = null;
    document.addEventListener("mouseenter", () => {
      if (mouseLeaveTimer) {
        clearTimeout(mouseLeaveTimer);
        mouseLeaveTimer = null;
      }
    });
    document.addEventListener("mouseleave", () => {
      if (cardDrag && cardDrag.dragging) return;
      if (mouseLeaveTimer) clearTimeout(mouseLeaveTimer);
      mouseLeaveTimer = setTimeout(() => {
        const bridge = window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.usage;
        if (bridge && typeof bridge.postMessage === "function") {
          bridge.postMessage("close");
        }
      }, 250);
    });

    let cardDrag = null;

    document.addEventListener("pointerdown", (event) => {
      const card = event.target.closest('[data-card="claude"], [data-card="codex"], [data-card="agy"], [data-card="grok"], [data-card="deepseek"], [data-card="manus"]');
      if (!card || event.button !== 0 || event.target.closest(window.PanelHooks.pointerdownExcludeSelector)) return;
      cardDrag = { card, pointerId: event.pointerId, startY: event.clientY, dragging: false };
      card.setPointerCapture(event.pointerId);
    });

    document.addEventListener("pointermove", (event) => {
      if (!cardDrag || event.pointerId !== cardDrag.pointerId) return;
      if (!cardDrag.dragging) {
        if (Math.abs(event.clientY - cardDrag.startY) <= 4) return;
        cardDrag.dragging = true;
        cardDrag.card.classList.add("is-dragging");
        document.documentElement.classList.add("is-card-dragging");
      }
      event.preventDefault();
      const cards = [...document.querySelectorAll('[data-card="claude"], [data-card="codex"], [data-card="agy"], [data-card="grok"], [data-card="deepseek"], [data-card="manus"]')]
        .filter((card) => card.offsetParent !== null);
      const target = cards.find((card) => card !== cardDrag.card && event.clientY < card.getBoundingClientRect().top + card.getBoundingClientRect().height / 2);
      if (target) target.parentElement.insertBefore(cardDrag.card, target);
      else {
        const projects = document.querySelector('[data-card="projects"]');
        if (projects) projects.parentElement.insertBefore(cardDrag.card, projects);
      }
    });

    function finishCardDrag(event) {
      if (!cardDrag || event.pointerId !== cardDrag.pointerId) return;
      const { card, dragging } = cardDrag;
      if (card.hasPointerCapture(event.pointerId)) card.releasePointerCapture(event.pointerId);
      card.classList.remove("is-dragging");
      document.documentElement.classList.remove("is-card-dragging");
      cardDrag = null;
      if (!dragging) return;
      const order = [...document.querySelectorAll('main.wrap > [data-card]')]
        .filter((item) => QUOTA_CARD_IDS.includes(item.dataset.card))
        .map((item) => item.dataset.card);
      const bridge = window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.usage;
      if (bridge && typeof bridge.postMessage === "function") {
        bridge.postMessage(JSON.stringify({ action: "set_card_order", order }));
      }
    }

    document.addEventListener("pointerup", finishCardDrag);
    document.addEventListener("pointercancel", finishCardDrag);

    window.usageApplyState({
      language: "en",
      claude: { session: {}, weekly: {} },
      codex: { session: {}, weekly: {} },
      agy: { session: {}, weekly: {}, groupName: "" },
      grok: { weekly: {} },
      deepseek: { available: false },
      manus: { available: false },
      cardOrder: ["claude", "codex", "agy", "grok", "deepseek", "manus"],
      hideAgy: true,
      hideGrok: true,
      hideDeepseek: false,
      hideManus: false,
      projects: [],
      projectsYesterday: [],
      projects7d: [],
      projects30d: [],
      projectsAll: [],
      statusline: {},
      footer: { rate: "Rate: --", status: "Status: Loading", today: "Today: $0.00 (0 tokens)", yesterday: "Yesterday: $0.00 (0 tokens)", serviceAlerts: [], showInstall: false }
    });
