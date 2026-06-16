# Domain: crypto-defi

**Triage signals:** crypto price, on-chain data, DEX, funding rate, MEV, cross-exchange spread,
new token monitoring, 加密/链上/套利.

| source | route | capability | detect | note |
|---|---|---|---|---|
| **CoinGecko MCP** | ① official | 15k+ coins price + GeckoTerminal on-chain DEX | connected (public no key) | best read-only price source |
| CoinMarketCap MCP | ① official | quotes, TA, derivatives, narratives | connected + key | free Basic now **50/min + 15k credits/mo** (was 30/min); x402 pay-per-call |
| **Etherscan MCP** | ① official | balances, tx, ABI, gas, 60+ chains | connected + free key | on-chain first pick; free-tier chain coverage cut ~10% 2026-05 (verified-contract + ABI endpoints stay free — info.etherscan.com) |
| **Blockscout MCP** (blockscout/mcp-server 40★) | ① official | on-chain data across 3000+ chains: addresses, tx, blocks, contracts/ABI, view calls | connected (public endpoint, no key for dev) | free read-only; **backstops the Etherscan free-tier cut** on dropped chains |
| **DefiLlama API** | ① free | **TVL, yields/APY, stablecoins, DEX/perp volume, fees/revenue** — protocol analytics the shard lacked | REST `api.llama.fi` / `yields.llama.fi`, no key | free no-key; 3rd-party MCPs only (frame as REST). DeFi ground-truth dataset |
| **Barker** (barker.money) | ① L2 | **stablecoin yields across 515 DeFi protocols + 20 CEX** (DefiLlama is DeFi-only — Binance/OKX/Bybit Earn rates only show here) | REST + `llms.txt` index at docs.barker.money, no MCP, no key claimed for read | specialist: stable-only + CEX-included; CEX rates are campaign-driven so **timestamp every quoted APY** |
| Moralis / Covalent (GoldRush) | ① | multi-chain wallet/portfolio normalized | connected + key | 100+ chains normalized |
| Nansen | ① | smart-money labels, token god mode | connected + key | unique labels; now affordable ~$49/mo annual (collapsed from up to ~$999/mo) |
| GeckoTerminal API | ① | DEX OHLCV history to 1s, liquidity | via CoinGecko MCP | beats DexScreener (which has no history) |
| **ccxt** (lib) | — | unified 100+ exchanges, spread monitor | python lib | base for cross-exchange logic |
| **Hummingbot** (+ MCP) | execution | CEX/DEX arb, AMM arbitrage strategy | docker MCP | run actual arbitrage; needs VPS |
| funding-rates-mcp (Kukapay) | ① | cross-exchange funding-rate divergence table | connected | perp funding arb signal; ⚠ **D-STALE** (7★, last push 2025-04) — watch vooi-app/mcp as live alt |

**Default pick:** Monitor spreads → CoinGecko MCP + ccxt + funding-rates-mcp. On-chain analysis →
Etherscan MCP + GeckoTerminal (+ **Blockscout MCP** free for chains Etherscan dropped from free tier).
Run arbitrage → Hummingbot + ccxt. **Stablecoin yield discovery → Barker (CEX + DeFi unified) +
DefiLlama yields (DeFi-only ground truth) — cross-check the two.**

**Reality check:** public arbitrage bots/scripts basically don't profit; real edge = latency, order
flow, gas/capital mgmt. Anything with private keys → small test wallet, never enable withdrawals.

**Install guidance:** `reference/volatile/pricing-install.md` → crypto-defi.
