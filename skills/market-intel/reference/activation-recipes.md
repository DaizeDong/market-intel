# Source activation recipes

Choose a source and operation from the public catalog, then verify that operation
in the active Claude or Codex session. This guide describes setup steps; it does
not record which accounts or tools a particular operator has configured.

1. Read the selected source's tool document for installation, authentication and
   capability requirements. Check volatile pricing and access terms at the provider.
2. Use the active host's supported MCP or app configuration. Reconnect when required
   and inspect the tools exposed in that same session.
3. Make a bounded read-only request for the selected capability. Distinguish transport,
   authentication, quota and content failures from a successful empty response.
4. Record current host, session, source, operation, timestamp and verification method
   using the [host capability contract](host-capabilities.md).
5. Report `available-now`, `setup` with the missing prerequisite, or an evidenced
   `hard-gap`. Installed packages and saved configuration alone do not grant readiness.

Use [install-guide.md](install-guide.md) for host setup and secret handling. Provider
credentials and real readiness observations belong in the PRIVATE companion. Use
[the synthetic setup example](remaining-tools.md.example) only to understand the
report shape; its entries do not establish any operator's current setup state.

A real setup checklist can be stored as `reports/setup-state.md` below the verified
PRIVATE DATA directory. Resolve and validate the destination with the existing
`tools/private_inventory.py` writer before creating it. Never recreate the retired
public `remaining-tools.md` runtime report or use a repository-local fallback.
