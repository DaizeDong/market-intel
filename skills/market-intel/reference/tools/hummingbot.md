# Tool: Hummingbot (+ MCP)

- **Domain(s):** crypto-defi (also: none)
- **Barrier route:** ① (execution layer) · **Source tier:** L1 · **Ready MCP:** yes — `hummingbot/mcp` (stdio/docker, talks to a running Hummingbot API)
- **Cost:** free, open-source (Apache-2.0). You pay only for a VPS + exchange trading fees.
- **Repo / Provider:** github.com/hummingbot/hummingbot — `hummingbot/hummingbot (18.8k★, gh-api 2026-06)`, Apache-2.0, active (pushed 2026-06-09). MCP: `hummingbot/mcp (56★, gh-api 2026-06)`, active (pushed 2026-03). ⚠ tool-master.json lists the MCP path as `hummingbot/hummingbot-mcp` which **404s** — the real repo is `hummingbot/mcp`.
- **Top pick for its domain:** no

## What it does / when to pick it
Open-source bot framework that **executes** market-making and CEX/DEX + AMM arbitrage strategies across many exchanges. Pick it only when you've moved past analysis and actually want to *place orders* / run a live arb or MM strategy. For measuring spreads or funding (the usual research output) you do NOT need Hummingbot — that's ccxt + funding-rates-mcp. Hummingbot is the execution endpoint, and it needs a VPS to run continuously.

## Install
The MCP is a thin client over a running **Hummingbot API** (default `http://localhost:8000`), so you run Hummingbot first, then point the MCP at it. Docker (from the shard, verified 2026-06):
```
claude mcp add --transport stdio hummingbot -- docker run --rm -i \
  -e HUMMINGBOT_API_URL=http://host.docker.internal:8000 \
  -v hummingbot_mcp:/root/.hummingbot_mcp hummingbot/hummingbot-mcp:latest
```
Dev alt (`hummingbot/mcp`): `git clone https://github.com/hummingbot/mcp && cd mcp && uv sync`, set `.env` (`HUMMINGBOT_API_URL/USERNAME/PASSWORD`), run via `uv run main.py`. stdio is flaky on Windows — prefer running the bot + API on a Linux VPS. Exact line: `reference/volatile/pricing-install.md` → crypto-defi.

## Auth / keys
Exchange API keys live in **Hummingbot's own encrypted keystore**, not in the MCP config. The MCP authenticates to the Hummingbot API via `HUMMINGBOT_USERNAME/PASSWORD` in `.env`. Anything with private keys → small test wallet, **never enable withdrawal permission** on the key (shard hard rule). Keep `.env` out of the transcript and out of git — see `reference/install-guide.md` → Secret-handling hygiene.

## Usage — call examples
After the Hummingbot API is up and the MCP connected, the MCP exposes tools to list/start/stop strategies, query bot status, and read balances/orders. Typical flow: configure a strategy in Hummingbot → `claude mcp get hummingbot` to see the tool names → start the strategy and monitor fills through the MCP. Always dry-run / paper first.

## General experience & gotchas (踩坑)
- **Reality check (shard):** public arbitrage bots/scripts basically don't profit. Real edge is latency, order flow, gas/capital mgmt — not running a stock strategy. Set expectations before deploying live.
- **It needs a VPS.** It's a long-running process; laptop/intermittent runs miss fills and desync state. Budget a cheap always-on box.
- **Two moving parts** (Hummingbot core API + the MCP). If the MCP shows `✗ Failed`, 90% of the time the underlying Hummingbot API isn't running or `HUMMINGBOT_API_URL` is wrong — check the core first.
- **Never enable withdrawals** on the exchange key; scope keys to trade-only, use a small isolated test wallet. A leaked trade-only key can't drain funds; a withdrawal-enabled one can.
- Docker networking on the host: `host.docker.internal` is required so the container reaches the API on the host — plain `localhost` inside the container fails.

## Failure signals & fallback
Failure = MCP `✗ Failed` / connection refused (Hummingbot API down or wrong URL), auth errors (bad `.env` user/pass), or strategy never fills (spread gone after fees, or wrong market symbol). Fallback for *research* (no execution): measure the opportunity with **ccxt** (spreads) + **funding-rates-mcp** (perp funding divergence) and report whether an edge even exists before standing up a bot.

## Last verified: 2026-06
