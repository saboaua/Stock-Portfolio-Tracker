/**
 * Portfolio Tracker Card — native Lovelace card for the integration.
 *
 * Resource URL (after install + restart):
 *   /portfolio_tracker_static/portfolio-tracker-card.js
 *
 * Lovelace:
 *   type: custom:portfolio-tracker-card
 *   title: Portfolio
 */
class PortfolioTrackerCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    this._title = this._config.title || "Portfolio Tracker";
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 4;
  }

  _state(id) {
    return this._hass?.states?.[id];
  }

  _num(id, fallback = 0) {
    const s = this._state(id);
    const v = parseFloat(s?.state);
    return Number.isFinite(v) ? v : fallback;
  }

  _attr(id, key, fallback = null) {
    const s = this._state(id);
    return s?.attributes?.[key] ?? fallback;
  }

  _money(n, ccy = "USD") {
    try {
      return new Intl.NumberFormat(undefined, {
        style: "currency",
        currency: ccy,
        maximumFractionDigits: 2,
      }).format(n);
    } catch {
      return `${ccy} ${n.toFixed(2)}`;
    }
  }

  _render() {
    if (!this._hass) return;
    if (!this._root) {
      this._root = document.createElement("ha-card");
      this.appendChild(this._root);
    }

    // Support both clean and portfolio_tracker_ prefixed entity IDs
    const pick = (...ids) => ids.find((id) => this._state(id)) || ids[0];
    const totalId = pick("sensor.portfolio_total_value", "sensor.portfolio_tracker_portfolio_total_value");
    const gainId = pick("sensor.portfolio_total_gain", "sensor.portfolio_tracker_portfolio_total_gain");
    const dayId = pick("sensor.portfolio_day_change", "sensor.portfolio_tracker_portfolio_day_change");
    const invId = pick("sensor.portfolio_total_invested", "sensor.portfolio_tracker_portfolio_total_invested");
    const realId = pick("sensor.portfolio_realized_gain", "sensor.portfolio_tracker_portfolio_realized_gain");
    const countId = pick("sensor.portfolio_holdings_count", "sensor.portfolio_tracker_portfolio_holdings_count");
    const usId = pick("sensor.us_market_session", "sensor.portfolio_tracker_us_market_session");
    const euId = pick("sensor.eu_market_session", "sensor.portfolio_tracker_eu_market_session");

    const ccy = this._attr(totalId, "base_currency", "USD");
    const total = this._num(totalId);
    const gain = this._num(gainId);
    const gainPct = this._attr(gainId, "gain_pct", 0);
    const day = this._num(dayId);
    const dayPct = this._attr(dayId, "gain_pct", 0);
    const invested = this._num(invId);
    const realized = this._num(realId);
    const count = this._num(countId);
    const us = (this._state(usId)?.state || "closed").toLowerCase();
    const eu = (this._state(euId)?.state || "closed").toLowerCase();

    const gainColor = gain >= 0 ? "#22c55e" : "#ef4444";
    const dayColor = day >= 0 ? "#22c55e" : "#ef4444";
    const pill = (label, open) =>
      `<span style="display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:700;background:${open ? "rgba(5,150,105,.12)" : "rgba(220,38,38,.12)"};color:${open ? "#059669" : "#dc2626"}">
        <span style="width:8px;height:8px;border-radius:50%;background:currentColor"></span>${label} ${open ? "OPEN" : "CLOSED"}
      </span>`;

    this._root.innerHTML = `
      <div style="padding:16px 18px 20px;">
        <div style="font-size:18px;font-weight:800;margin-bottom:12px;">${this._title}</div>
        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px;">
          ${pill("🇺🇸 US", us === "open")}
          ${pill("🇪🇺 EU", eu === "open")}
        </div>
        <div style="background:linear-gradient(135deg,#312e81,#1e1b4b);border-radius:18px;padding:18px;color:#fff;">
          <div style="font-size:11px;letter-spacing:1px;opacity:.7;text-transform:uppercase;margin-bottom:6px;">Holdings summary</div>
          <div style="font-size:32px;font-weight:800;letter-spacing:-1px;margin-bottom:12px;">${this._money(total, ccy)}</div>
          <div style="display:flex;flex-wrap:wrap;gap:10px;">
            <div style="background:rgba(255,255,255,.1);border-radius:12px;padding:8px 12px;min-width:120px;">
              <div style="font-size:10px;opacity:.8;text-transform:uppercase;">Unrealized</div>
              <div style="font-weight:700;color:${gainColor}">${gain >= 0 ? "▲" : "▼"} ${this._money(Math.abs(gain), ccy)} (${Number(gainPct).toFixed(2)}%)</div>
            </div>
            <div style="background:rgba(255,255,255,.1);border-radius:12px;padding:8px 12px;min-width:120px;">
              <div style="font-size:10px;opacity:.8;text-transform:uppercase;">Day change</div>
              <div style="font-weight:700;color:${dayColor}">${day >= 0 ? "▲" : "▼"} ${this._money(Math.abs(day), ccy)} (${Number(dayPct).toFixed(2)}%)</div>
            </div>
          </div>
          <div style="margin-top:12px;font-size:12px;opacity:.75;">
            Cost ${this._money(invested, ccy)} · Realized ${this._money(realized, ccy)} · ${count} holdings
          </div>
        </div>
      </div>
    `;
  }

  static getStubConfig() {
    return { title: "Portfolio Tracker" };
  }
}

customElements.define("portfolio-tracker-card", PortfolioTrackerCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "portfolio-tracker-card",
  name: "Portfolio Tracker Card",
  description: "Summary card for the Portfolio Tracker integration",
  preview: true,
});
