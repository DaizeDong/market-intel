# Tool: saseq-discord-mcp

- **Domain(s):** discord-community
- **Barrier route:** 1 official API (bot token) - **Source tier:** free - **Ready MCP:** yes (self-host, Docker)
- **Top pick for its domain:** yes (only ToS-compliant Discord MCP route)

## What it does / when to pick it
Bot-token Discord MCP for own or admin servers - ToS-compliant alternative to user-session scrapers. Built on JDA (Java Discord API), shipped as a Docker container exposing `/mcp` on port 8085.

**Decision rule:** pick when you need Discord-server intel from servers **you own or admin** (bot-token model: invite the bot, scope its permissions, read what it can see). For unowned servers, scraping a user session violates Discord ToS and risks account termination - there is no legitimate route 2 or 3 here, so the honest answer for unowned servers is "you cannot, ask the server owner to invite a bot."

## Install
```bash
git clone https://github.com/SaseQ/discord-mcp
cd discord-mcp
docker compose up -d   # exposes MCP at http://localhost:8085/mcp
```
<TODO: confirm exact docker-compose env wiring> - see https://github.com/SaseQ/discord-mcp for the current `DISCORD_TOKEN` env-var name and compose file.

Then register with Claude Code as an HTTP MCP pointing at `http://localhost:8085/mcp`.

## Auth / keys
Free, but **requires your own Discord bot token**. Create an application at https://discord.com/developers/applications, add a bot, copy the token into `secrets/discord-mcp.env` as `DISCORD_TOKEN=...`, and invite the bot to your target server with the read scopes you need (Read Messages, Read Message History, View Channels, plus Message Content Intent toggled on in the dev portal). No paid API key, no marketplace key.

## Usage - call examples
Once registered, the MCP exposes tools like `list_guilds`, `list_channels`, `read_messages`. Minimal flow:
1. `list_guilds` -> confirm the bot sees your server
2. `list_channels guild_id=...` -> pick channel
3. `read_messages channel_id=... limit=100` -> pull recent messages for analysis

## General experience & gotchas (踩坑)
- **ToS wall is real:** this tool only works for servers you own or admin. For competitor/community servers you have not been invited to, there is no route here - do not try to repurpose a user-session scraper, Discord bans accounts for it.
- **Message Content Intent is gated:** in the dev portal, the "Message Content" privileged intent must be toggled on or `read_messages` returns empty content even with correct permissions. Easy to miss on first setup.
- **Java + Docker only:** JDA-based, so no `npx`/`uvx` one-liner. If you don't run Docker, expect to install a JDK and build from source - heavier footprint than a typical Node/Python MCP.
- **Self-hosted, no managed endpoint:** the container runs on your machine at `:8085`. If you tear down the host or change ports, the MCP registration in Claude Code breaks silently - re-verify after reboots.
- **Modest project, single maintainer:** 356 stars / 81 forks / MIT, last commit 2026-04-25. Active enough to trust for research workflows, but don't expect rapid issue turnaround - read the source before depending on it in production.

## Last verified: 2026-06
