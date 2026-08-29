/**
 * Portfolio Tracker Card
 *
 * Resource: /portfolio_tracker_static/portfolio-tracker-card.js  (JavaScript Module)
 *
 * Modes:
 *   type: custom:portfolio-tracker-card
 *   view: summary | charts | holdings   (default: summary)
 *   title: My Portfolio
 *   range: 1W | 1M                       (sparkline window for charts view)
 */
class PortfolioTrackerCard extends HTMLElement {
  static getStubConfig() {
    return { title: "My Portfolio", view: "charts", range: "1W" };
  }

  static getConfigElement() {
    return document.createElement("portfolio-tracker-card-editor");
  }

  setConfig(config) {
    if (!config) throw new Error("Invalid configuration");
    this._config = {
      title: "My Portfolio",
      view: "charts",
      range: "1W",
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    const view = this._config?.view || "summary";
    if (view === "charts") return 5;
    if (view === "holdings") return 6;
    return 3;
  }

  _st(id) {
    return this._hass?.states?.[id];
  }

  _pick(...ids) {
    return ids.find((id) => this._st(id)) || ids[0];
  }

  _num(id, fb = 0) {
    const v = parseFloat(this._st(id)?.state);
    return Number.isFinite(v) ? v : fb;
  }

  _attr(id, key, fb = null) {
    return this._st(id)?.attributes?.[key] ?? fb;
  }

  _money(n, ccy = "USD") {
    try {
      return new Intl.NumberFormat(undefined, {
        style: "currency",
        currency: ccy,
        maximumFractionDigits: 2,
      }).format(n ?? 0);
    } catch {
      return `${ccy} ${Number(n || 0).toFixed(2)}`;
    }
  }

  _rows() {
    const tableId = this._pick(
      "sensor.portfolio_holdings_table",
      "sensor.portfolio_tracker_portfolio_holdings_table"
    );
    const rows = this._attr(tableId, "rows", []) || [];
    return Array.isArray(rows) ? rows : [];
  }

  _sparkSvg(points, color, width = 160, height = 48) {
    if (!points || points.length < 2) {
      return `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"></svg>`;
    }
    const range = this._config.range || "1W";
    let pts = points.slice();
    if (range === "1W") pts = pts.slice(-7);
    else if (range === "1M") pts = pts.slice(-22);
    if (pts.length < 2) pts = points.slice(-2);

    const min = Math.min(...pts);
    const max = Math.max(...pts);
    const span = max - min || 1;
    const step = width / (pts.length - 1);
    const coords = pts
      .map((v, i) => {
        const x = i * step;
        const y = height - ((v - min) / span) * (height - 6) - 3;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");
    return `
      <svg width="100%" height="${height}" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none"
           style="display:block;margin-top:8px;">
        <polyline fill="none" stroke="${color}" stroke-width="2.2"
                  stroke-linecap="round" stroke-linejoin="round" points="${coords}" />
      </svg>`;
  }

  _rangeTabs() {
    const ranges = ["1W", "1M"];
    const cur = this._config.range || "1W";
    return `
      <div style="display:flex;gap:4px;flex-wrap:wrap;">
        ${ranges
          .map(
            (r) => `
          <button data-range="${r}" style="
            border:none;cursor:pointer;padding:4px 10px;border-radius:8px;font-size:12px;font-weight:700;
            background:${r === cur ? "var(--primary-color, #3b82f6)" : "transparent"};
            color:${r === cur ? "#fff" : "var(--secondary-text-color, #94a3b8)"};
          ">${r}</button>`
          )
          .join("")}
      </div>`;
  }

  _viewTabs() {
    const views = [
      { id: "summary", label: "Summary" },
      { id: "charts", label: "Charts" },
      { id: "holdings", label: "Holdings" },
    ];
    const cur = this._config.view || "charts";
    return `
      <div style="display:flex;gap:6px;flex-wrap:wrap;">
        ${views
          .map(
            (v) => `
          <button data-view="${v.id}" style="
            border:1px solid var(--divider-color, rgba(0,0,0,.08));cursor:pointer;
            padding:4px 12px;border-radius:999px;font-size:12px;font-weight:700;
            background:${v.id === cur ? "var(--primary-color, #3b82f6)" : "var(--card-background-color, #fff)"};
            color:${v.id === cur ? "#fff" : "var(--primary-text-color, #0f172a)"};
          ">${v.label}</button>`
          )
          .join("")}
      </div>`;
  }

  _bindTabs() {
    this._root.querySelectorAll("button[data-view]").forEach((btn) => {
      btn.onclick = (e) => {
        e.preventDefault();
        this._config = { ...this._config, view: btn.dataset.view };
        this._render();
      };
    });
    this._root.querySelectorAll("button[data-range]").forEach((btn) => {
      btn.onclick = (e) => {
        e.preventDefault();
        this._config = { ...this._config, range: btn.dataset.range };
        this._render();
      };
    });
  }

  _renderSummary() {
    const totalId = this._pick(
      "sensor.portfolio_total_value",
      "sensor.portfolio_tracker_portfolio_total_value"
    );
    const gainId = this._pick(
      "sensor.portfolio_total_gain",
      "sensor.portfolio_tracker_portfolio_total_gain"
    );
    const dayId = this._pick(
      "sensor.portfolio_day_change",
      "sensor.portfolio_tracker_portfolio_day_change"
    );
    const invId = this._pick(
      "sensor.portfolio_total_invested",
      "sensor.portfolio_tracker_portfolio_total_invested"
    );
    const realId = this._pick(
      "sensor.portfolio_realized_gain",
      "sensor.portfolio_tracker_portfolio_realized_gain"
    );
    const countId = this._pick(
      "sensor.portfolio_holdings_count",
      "sensor.portfolio_tracker_portfolio_holdings_count"
    );
    const usId = this._pick(
      "sensor.us_market_session",
      "sensor.portfolio_tracker_us_market_session"
    );
    const euId = this._pick(
      "sensor.eu_market_session",
      "sensor.portfolio_tracker_eu_market_session"
    );

    const ccy = this._attr(totalId, "base_currency", "USD");
    const total = this._num(totalId);
    const gain = this._num(gainId);
    const gainPct = this._attr(gainId, "gain_pct", 0);
    const day = this._num(dayId);
    const dayPct = this._attr(dayId, "gain_pct", 0);
    const invested = this._num(invId);
    const realized = this._num(realId);
    const count = this._num(countId);
    const us = (this._st(usId)?.state || "closed").toLowerCase();
    const eu = (this._st(euId)?.state || "closed").toLowerCase();
    const gainColor = gain >= 0 ? "#22c55e" : "#ef4444";
    const dayColor = day >= 0 ? "#22c55e" : "#ef4444";
    const pill = (label, open) =>
      `<span style="display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:700;background:${
        open ? "rgba(5,150,105,.12)" : "rgba(220,38,38,.12)"
      };color:${open ? "#059669" : "#dc2626"}">
        <span style="width:8px;height:8px;border-radius:50%;background:currentColor"></span>${label} ${
        open ? "OPEN" : "CLOSED"
      }</span>`;

    return `
      <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px;">
        ${pill("🇺🇸 US", us === "open")}
        ${pill("🇪🇺 EU", eu === "open")}
      </div>
      <div style="background:linear-gradient(135deg,#312e81,#1e1b4b);border-radius:18px;padding:18px;color:#fff;">
        <div style="font-size:11px;letter-spacing:1px;opacity:.7;text-transform:uppercase;margin-bottom:6px;">Holdings summary</div>
        <div style="font-size:32px;font-weight:800;letter-spacing:-1px;margin-bottom:12px;">${this._money(
          total,
          ccy
        )}</div>
        <div style="display:flex;flex-wrap:wrap;gap:10px;">
          <div style="background:rgba(255,255,255,.1);border-radius:12px;padding:8px 12px;min-width:120px;">
            <div style="font-size:10px;opacity:.8;text-transform:uppercase;">Unrealized</div>
            <div style="font-weight:700;color:${gainColor}">${
      gain >= 0 ? "▲" : "▼"
    } ${this._money(Math.abs(gain), ccy)} (${Number(gainPct).toFixed(2)}%)</div>
          </div>
          <div style="background:rgba(255,255,255,.1);border-radius:12px;padding:8px 12px;min-width:120px;">
            <div style="font-size:10px;opacity:.8;text-transform:uppercase;">Day change</div>
            <div style="font-weight:700;color:${dayColor}">${
      day >= 0 ? "▲" : "▼"
    } ${this._money(Math.abs(day), ccy)} (${Number(dayPct).toFixed(2)}%)</div>
          </div>
        </div>
        <div style="margin-top:12px;font-size:12px;opacity:.75;">
          Cost ${this._money(invested, ccy)} · Realized ${this._money(
      realized,
      ccy
    )} · ${count} holdings
        </div>
      </div>`;
  }

  _renderCharts() {
    const rows = this._rows();
    if (!rows.length) {
      return `<div style="opacity:.7;padding:12px 0;">No holdings yet. Add stocks or crypto via Configure (e.g. NVDA, VUAA.L, BTC-USD).</div>`;
    }
    const tiles = rows
      .map((r) => {
        const pct = Number(r.day_gain_pct || 0);
        const up = pct >= 0;
        const color = up ? "#22c55e" : "#ef4444";
        const name = r.long_name || r.name || r.symbol;
        const ccy = r.currency || "USD";
        const spark = this._sparkSvg(r.sparkline || [], color);
        return `
          <div style="
            background:var(--secondary-background-color, #f1f5f9);
            border-radius:14px;padding:14px 14px 10px;min-width:0;
            border:1px solid var(--divider-color, rgba(0,0,0,.06));
          ">
            <div style="display:flex;justify-content:space-between;gap:8px;align-items:flex-start;">
              <div style="font-size:13px;font-weight:700;color:var(--primary-text-color,#0f172a);
                          white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:70%;">
                ${name}
              </div>
              <div style="font-size:11px;font-weight:700;color:var(--secondary-text-color,#94a3b8);">${
                r.symbol
              }</div>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:6px;">
              <div style="font-size:22px;font-weight:800;letter-spacing:-0.5px;">${this._money(
                r.last_price,
                ccy
              )}</div>
              <div style="font-size:13px;font-weight:700;color:${color};">
                ${up ? "▲" : "▼"} ${Math.abs(pct).toFixed(2)}%
              </div>
            </div>
            <div style="font-size:12px;color:var(--secondary-text-color,#94a3b8);">
              ${r.previous_close != null ? this._money(r.previous_close, ccy) : ""}
            </div>
            ${spark}
          </div>`;
      })
      .join("");

    return `
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;">
        ${tiles}
      </div>`;
  }

  _renderHoldings() {
    const rows = this._rows();
    if (!rows.length) {
      return `<div style="opacity:.7;padding:12px 0;">No holdings yet.</div>`;
    }
    const body = rows
      .map((r) => {
        const gain = Number(r.tot_gain_dollar || 0);
        const gainPct = Number(r.tot_gain_pct || 0);
        const up = gain >= 0;
        const color = up ? "#22c55e" : "#ef4444";
        const ccy = r.currency || "USD";
        return `
          <div style="
            display:grid;grid-template-columns:1.2fr 0.8fr 0.8fr 1fr 1fr;
            gap:8px;padding:12px 4px;border-bottom:1px solid var(--divider-color, rgba(0,0,0,.06));
            align-items:center;font-size:13px;
          ">
            <div>
              <div style="font-weight:800;">${r.symbol}</div>
              <div style="font-size:11px;color:var(--secondary-text-color,#94a3b8);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                ${r.long_name || r.name || ""}
              </div>
            </div>
            <div style="text-align:right;">
              <div style="font-size:11px;color:var(--secondary-text-color);">Shares</div>
              <div style="font-weight:700;">${r.shares}</div>
            </div>
            <div style="text-align:right;">
              <div style="font-size:11px;color:var(--secondary-text-color);">Avg cost</div>
              <div style="font-weight:700;">${this._money(r.ac_share, ccy)}</div>
            </div>
            <div style="text-align:right;">
              <div style="font-size:11px;color:var(--secondary-text-color);">Invested</div>
              <div style="font-weight:700;">${this._money(r.total_cost, ccy)}</div>
            </div>
            <div style="text-align:right;">
              <div style="font-size:11px;color:var(--secondary-text-color);">Value</div>
              <div style="font-weight:800;">${this._money(r.market_value, ccy)}</div>
              <div style="font-size:12px;font-weight:700;color:${color};">
                ${up ? "▲" : "▼"} ${this._money(Math.abs(gain), ccy)} (${gainPct.toFixed(2)}%)
              </div>
            </div>
          </div>`;
      })
      .join("");

    return `
      <div style="overflow-x:auto;">
        <div style="
          display:grid;grid-template-columns:1.2fr 0.8fr 0.8fr 1fr 1fr;gap:8px;
          padding:0 4px 8px;font-size:11px;font-weight:700;color:var(--secondary-text-color,#94a3b8);
          text-transform:uppercase;letter-spacing:.4px;border-bottom:1px solid var(--divider-color, rgba(0,0,0,.08));
        ">
          <div>Symbol</div>
          <div style="text-align:right;">Shares</div>
          <div style="text-align:right;">Avg cost</div>
          <div style="text-align:right;">Invested</div>
          <div style="text-align:right;">Market value</div>
        </div>
        ${body}
      </div>`;
  }

  _render() {
    if (!this._hass || !this._config) return;
    if (!this._root) {
      this._root = document.createElement("ha-card");
      this.appendChild(this._root);
    }
    const view = this._config.view || "charts";
    let body = "";
    if (view === "holdings") body = this._renderHoldings();
    else if (view === "charts") body = this._renderCharts();
    else body = this._renderSummary();

    this._root.innerHTML = `
      <div style="padding:16px 18px 18px;">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:14px;">
          <div style="font-size:18px;font-weight:800;">${this._config.title || "My Portfolio"}</div>
          <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
            ${this._viewTabs()}
            ${view === "charts" ? this._rangeTabs() : ""}
          </div>
        </div>
        ${body}
      </div>`;
    this._bindTabs();
  }
}

customElements.define("portfolio-tracker-card", PortfolioTrackerCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "portfolio-tracker-card",
  name: "Portfolio Tracker Card",
  description:
    "Summary, chart grid (sparklines), or holdings table for Portfolio Tracker",
  preview: true,
});
