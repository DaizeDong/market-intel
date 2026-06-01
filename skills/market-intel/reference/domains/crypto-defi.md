# Domain: crypto-defi

**Triage signals:** crypto price, on-chain data, DEX, funding rate, MEV, cross-exchange spread,
new token monitoring, 加密/链上/套利.

| source | route | capability | detect | note |
|---|---|---|---|---|
| **CoinGecko MCP** | ① official | 15k+ coins price + GeckoTerminal on-chain DEX | connected (public no key) | best read-only price source |
| CoinMarketCap MCP | ① official | quotes, TA, derivatives, narratives | connected + key | free 30/min; x402 pay-per-call |
| **Etherscan MCP** | ① official | balances, tx, ABI, gas, 60+ chains | connected + free key | on-chain first pick |
| Moralis / Covalent (GoldRush) | ① | multi-chain wallet/portfolio normalized | connected + key | 100+ chains normalized |
| Nansen | ① | smart-money labels, token god mode | connected + key | unique labels, pricey |
| GeckoTerminal API | ① | DEX OHLCV history to 1s, liquidity | via CoinGecko MCP | beats DexScreener (which has no history) |
| **ccxt** (lib) | — | unified 100+ exchanges, spread monitor | python lib | base for cross-exchange logic |
| **Hummingbot** (+ MCP) | execution | CEX/DEX arb, AMM arbitrage strategy | docker MCP | run actual arbitrage; needs VPS |
| funding-rates-mcp (Kukapay) | ① | cross-exchange funding-rate divergence table | connected | perp funding arb signal |

**Default pick:** Monitor spreads → CoinGecko MCP + ccxt + funding-rates-mcp. On-chain analysis →
Etherscan MCP + GeckoTerminal. Run arbitrage → Hummingbot + ccxt.

**Reality check:** public arbitrage bots/scripts basically don't profit; real edge = latency, order
flow, gas/capital mgmt. Anything with private keys → small test wallet, never enable withdrawals.

**Install guidance:** `reference/volatile/pricing-install.md` → crypto-defi.
