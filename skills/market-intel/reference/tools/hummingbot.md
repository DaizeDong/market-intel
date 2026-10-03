# Tool: Hummingbot (+ MCP)

- **Domain(s):** crypto-defi (also: none)
- **Barrier route:** ① (execution layer) · **Source tier:** L1 · **Ready MCP:** yes, `hummingbot/mcp` (stdio/docker, talks to a running Hummingbot API)
- **Cost:** free, open-source (Apache-2.0). You pay only for a VPS + exchange trading fees.
- **Repo / Provider:** github.com/hummingbot/hummingbot, `hummingbot/hummingbot (18.8k★, gh-api 2026-06)`, Apache-2.0, active (pushed 2026-06-09). MCP: `hummingbot/mcp (56★, gh-api 2026-06)`, active (pushed 2026-03). ⚠ tool-master.json lists the MCP path as `hummingbot/hummingbot-mcp` which **404s**, the real repo is `hummingbot/mcp`.
- **Top pick for its domain:** no

## What it does / when to pick it
Open-source bot framework that **executes** market-making and CEX/DEX + AMM arbitrage strategies across many exchanges. Pick it only when you've moved past analysis and actually want to *place orders* / run a live arb or MM strategy. For measuring spreads or funding (the usual research output) you do NOT need Hummingbot, that's ccxt + funding-rates-mcp. Hummingbot is the execution endpoint, and it needs a VPS to run continuously.

## Install
The MCP is a thin client over a running **Hummingbot API** (historical default
`http://localhost:8000`). Before starting either component, check the installed core/API and MCP
versions for their supported configuration and persistence options. From an importable full
Market checkout, resolve an existing private runtime directory:

```python
from tools.private_inventory import resolve_directory

runtime = resolve_directory("runtime/hummingbot")
```

Initialize that directory in the configured PRIVATE versioned companion and provide a fresh
visibility receipt first. The shared proof checks all configured fetch/push destinations from
local Git configuration and receipts; it does not query GitHub live or require a remote named
`origin`. Missing, stale or unknown visibility fails setup.

Use supported absolute bind mounts beneath `runtime.path` for the core databases, encrypted
keystore, MCP sessions, logs, strategy configuration and exports. A Docker named volume alone
does not establish Git versioning or backup. Supply API configuration and credentials through a
supported external private env-file or secret configuration, never a `.env` in the public clone.
Verify every enabled writer, revalidate its destination before launch, and keep setup-only if
the installed version cannot redirect any writer.

For source installation, `git clone https://github.com/hummingbot/mcp`, then `cd mcp`, then
`uv sync` installs code and dependencies only. Start the configured services only after private
persistence is established. Windows stdio behavior is version-dependent; test the selected host
and transport. See `reference/volatile/pricing-install.md` → crypto-defi for dated install details.

## Auth / keys
Exchange API keys belong in **Hummingbot's own encrypted keystore** in the private runtime. The
MCP authenticates to the Hummingbot API through its supported private configuration, historically
`HUMMINGBOT_USERNAME` and `HUMMINGBOT_PASSWORD`; verify the installed version's variable names.
Use a small isolated test wallet and disable withdrawal permission. Never expose credentials in
transcripts or public repositories; designated PRIVATE versioned credential backups are allowed.
See `reference/install-guide.md` → Secret-handling hygiene.

## Usage, call examples
Once the configured API and MCP are running, discover the actual callable operations in the
active host. Verify an authorized read-only status or balance operation, including authentication
and usable response content. Return only value-free status diagnostics; never dump raw MCP
configuration or secret-bearing listings. Installation checks never place orders or start a
trading strategy. Strategy execution requires separate explicit authorization and paper/dry-run
validation first.

## General experience & gotchas (踩坑)
- **Reality check (shard):** public arbitrage bots/scripts basically don't profit. Real edge is latency, order flow, gas/capital mgmt, not running a stock strategy. Set expectations before deploying live.
- **It needs a VPS.** It's a long-running process; laptop/intermittent runs miss fills and desync state. Budget a cheap always-on box.
- **Two moving parts** (Hummingbot core API + the MCP). If the MCP fails, check the core's status and configured API address through value-free diagnostics before investigating the client.
- **Disable withdrawals** on the exchange key and use a small isolated test wallet. A leaked trade-only key can still lose capital through unauthorized trades, adverse prices and fees.
- Docker networking depends on the host: `localhost` inside a container refers to that container. Docker Desktop commonly provides `host.docker.internal`; verify the supported address on the actual platform.

## Failure signals & fallback
Failure = MCP `✗ Failed` / connection refused (Hummingbot API down or wrong URL), auth errors
(private API credentials rejected), or strategy never fills (spread gone after fees, or wrong
market symbol). Fallback for *research* (no execution): measure the opportunity with **ccxt**
(spreads) + **funding-rates-mcp** (perp funding divergence) and report whether an edge exists before
standing up a bot.

## Last verified: 2026-06
