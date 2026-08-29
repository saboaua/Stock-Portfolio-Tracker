<p align="center">
  <img src="https://raw.githubusercontent.com/saboaua/Stock-Portfolio-Tracker/main/logo.png" alt="Portfolio Tracker" width="420">
</p>

## Portfolio Tracker

Track stocks, ETFs, and crypto in Home Assistant.

- Configure UI with icons (add / buy / sell / edit / remove)
- Yahoo Finance prices · multi-currency FX · dividend calendar
- Native card views: **summary** · **charts** (sparklines) · **holdings**
- Crypto: Yahoo symbols such as `BTC-USD`, `ETH-USD` via Configure → Add

**Docs:** [github.com/saboaua/Stock-Portfolio-Tracker](https://github.com/saboaua/Stock-Portfolio-Tracker)

**Version:** 1.4.3

{% if not installed %}
### Installation
1. Download from HACS  
2. Restart Home Assistant  
3. Settings → Devices & Services → Add Integration → Portfolio Tracker  
{% endif %}

### Lovelace card resource

| Field | Value |
|-------|--------|
| URL | `/portfolio_tracker_static/portfolio-tracker-card.js` |
| Type | JavaScript Module |

```yaml
type: custom:portfolio-tracker-card
title: My Portfolio
view: charts    # summary | charts | holdings
range: 1W
```
