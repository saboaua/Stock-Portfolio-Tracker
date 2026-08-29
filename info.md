<p align="center">
  <img src="https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/ha-portfolio-tracker/main/icon.png" alt="Portfolio Tracker" width="96">
</p>

## Portfolio Tracker

Track stocks, ETFs, and crypto in Home Assistant — no day-to-day YAML.

- **Configure** UI: add / buy / sell / edit / remove holdings  
- Live **Yahoo Finance** prices (no API key)  
- Portfolio totals, day change, **realized P/L**, allocation %  
- US & EU market open sensors + session clocks  
- Ready-made Lovelace cards in `dashboards/`

**Version:** 1.3.0

{% if not installed %}
### Installation
1. Download from HACS  
2. Restart Home Assistant  
3. Settings → Devices & Services → Add Integration → Portfolio Tracker  
{% endif %}

### Lovelace frontend cards (for the designed dashboard)

Install from **HACS → Frontend**:

- button-card  
- auto-entities  
- flex-table-card  
- card-mod  
- layout-card *(optional)*  
- vertical-stack-in-card *(optional)*  
- Mushroom  
- mini-graph-card *(optional)*
