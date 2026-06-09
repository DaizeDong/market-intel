# Domain: finance-markets

**Triage signals:** stocks, options, fundamentals, earnings, SEC filings, macro/economic data,
unusual options flow, 股票/期权/基本面. (Tools only — not investment advice.)

| source | route | capability | detect | note |
|---|---|---|---|---|
| **SEC EDGAR MCP** (stefanoamorelli) | ① free | 13M+ filings, 10-K/Q, XBRL, insider | connected, no key (User-Agent only) | zero cost, institutional-grade |
| **FRED MCP** | ① free | 800k+ macro series (GDP/CPI/rates) | connected + free FRED key | zero cost |
| Polygon.io (now **Massive**) | ① | realtime + 20yr history + WebSocket | connected + key | **REBRAND** → massive.com (301); still the live Pro pick — same API/keys; free 5/min, $29/$79/$199 tiers |
| **Alex2Yang97/yahoo-finance-mcp** (306★) | ④ | free no-key price/fundamentals/options/news | `uvx` self-host | the only **free, no-key** route here; ⚠ yfinance scrapes Yahoo — not for prod/algo, IP-ban prone |
| Finnhub / Twelve Data | ① | fundamentals + alt-data / multi-asset realtime | connected + key | best free tiers (60/min, 800/day) |
| Financial Modeling Prep | ① | financials/valuation | key | free 250/day |
| Unusual Whales MCP | ① | options flow, dark pool, congress trades | connected + paid token | differentiated arb signals |
| Alpaca / Tradier MCP | ① official | trade execution (paper first!) | connected | put risk guardrails in front |

**Default pick:** Free start → SEC EDGAR + FRED + Finnhub free tier. Pro → Polygon.io. Execution →
Alpaca (paper trading first, MCP holds key + enforces risk policy).

**Dead/avoid:** IEX Cloud (shut down 2024-08). Alpha Vantage free = 25/day (worst). "Free realtime"
is usually 15-min delayed. Auto-trading MUST have guardrails + small test sizing.

**Install guidance:** `reference/volatile/pricing-install.md` → finance-markets.
