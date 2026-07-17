# Companion config repo, hardening runbook

When setting up a companion config repo from scratch (see
[`companion-config-spec.md`](companion-config-spec.md) for the structural contract), the
default GitHub configuration is **dangerously permissive** for a repo that may hold API
keys, ops state, or per-tool registration metadata. This runbook walks every setting that
matters, with the rationale and the exact path / `gh` CLI command to flip each.

Apply this checklist **before** committing the first secret.

> 💡 Time budget: ~15 minutes the first time, ~5 minutes per subsequent personal repo once
> you know the flow. Most settings are one-time.

---

## Threat model (what this runbook defends against)

| Threat | Mitigation |
|---|---|
| Repo accidentally made public | Visibility checked + verified at creation |
| AI tool (ChatGPT Codex, Devin, etc.) silently scans this repo because it has "all repos" access | GitHub Apps audit + restrict scope or uninstall |
| GitHub uses your code to train Copilot / future AI models | Account-level Copilot data sharing **disabled** |
| Compromised GitHub Action exfiltrates secrets via outbound HTTP | Actions **disabled** (no CI on this repo) |
| Dependabot opens PRs that touch secrets | Dependabot **disabled** |
| Webhook → external service hands credentials to an attacker | Webhooks **empty** |
| Deploy key compromise enables clone outside your control | Deploy keys **empty** |
| Inadvertent collaborator added during a help session | Collaborators **empty** + verified after each support interaction |
| Public-facing surface (Wikis / Issues / Pages / Discussions) leaks via search-engine index | All four **disabled** |

---

## Step 1, Create the repo as PRIVATE

```bash
gh repo create <your-user>/market-intel-config \
  --private \
  --description "Private companion config repo for market-intel — ops state + (optionally) secrets" \
  --confirm
```

Or via web UI: <https://github.com/new> → **Private** radio selected before pressing Create.

**Verification**: visit `https://github.com/<your-user>/<repo>` while signed-out (in an
incognito window). You should see a "Page not found", that confirms private. If you see the
repo contents, **stop immediately and flip to private**.

---

## Step 2, Decide your secret-storage mode

See [`companion-config-spec.md`](companion-config-spec.md) §5.3 for the formal trade-off
between Mode A (secrets committed) and Mode B (secrets gitignored + out-of-band backup).
The hardening steps below are **identical for both modes**, Mode A just has a stricter
"any single compromise = all keys exposed" residual risk that you accept consciously.

---

## Step 3, Lock down repo-level Features

Path: `Settings → General → Features`.

Disable everything you don't actively use. For a personal ops-state repo this is usually
ALL of them:

| Feature | Default | Recommended for config repo |
|---|---|---|
| Wikis | ✓ on | ✗ **off**, no docs surface to leak |
| Issues | ✓ on | ✗ **off**, no need; you're the only user |
| Sponsorships | ✗ off | leave off |
| Discussions | ✗ off | leave off |
| Projects | ✓ on | ✗ **off**, no need |
| Preserve this repository | varies | leave default |

These are auto-saved on click; no Save button.

---

## Step 4, Disable Dependabot + all Code Security

Path: `Settings → Code security`.

For free personal accounts, the only available controls on private repos are Dependabot
features. **Leave them all disabled**:

- Dependency graph: Disabled
- Dependabot alerts: Disabled
- Dependabot security updates: Disabled
- Grouped security updates: Disabled
- Dependabot version updates: Disabled
- Dependabot on self-hosted runners: Disabled

Rationale: this repo has no application dependencies in the conventional sense, the
"dependencies" are MCP server packages that are pulled live at apply time, not pinned
manifest files. Dependabot scanning adds zero value and surface area only.

If you're on a paid plan that exposes "Secret Scanning" / "Push protection" / "Code
scanning" panels here, **also disable** them for your private companion repo. The point of
Mode A is that you've consciously accepted holding secrets here; provider auto-revoke from
those scans (especially Push Protection) would block legitimate commits.

---

## Step 5, Disable Actions entirely

Path: `Settings → Actions → General → Actions permissions`.

Set the radio to **"Disable actions"** and click Save.

Rationale: this repo has no CI to run. Leaving Actions enabled with the default "Allow all
actions" means a compromised marketplace action could exfiltrate `secrets/*.env` files via
an outbound HTTP request the moment someone tricks you into running it. With Actions
disabled, that whole attack surface is closed.

If you previously shipped a `no-secret-leak.yml` style gate, **delete the workflow file**
before disabling Actions (it would just silently stop running otherwise):

```bash
rm .github/workflows/*.yml
git add . && git commit -m "remove all workflows (Actions disabled at repo level)"
```

---

## Step 6, Disable Pages

Path: `Settings → Pages`.

Source: **None**.

A personal config repo has no reason to serve a public site. Leaving Pages with a default
branch source could in extreme edge cases publish README content to the open web.

---

## Step 7, Verify Webhooks / Deploy keys / Actions secrets are empty

Paths to check (each should show "no items" or equivalent):

- `Settings → Webhooks`, no webhooks. (Some integrations auto-add these; audit periodically.)
- `Settings → Deploy keys`, no deploy keys. (SSH keys here grant non-revocable git access.)
- `Settings → Secrets and variables → Actions`, no Actions secrets. (Real secrets live in
  `secrets/<slug>.env` per the spec, not in Actions secret storage which is meant for CI.)
- `Settings → Secrets and variables → Codespaces`, same: empty.
- `Settings → Secrets and variables → Dependabot`, same: empty.

---

## Step 8, Verify Collaborators is empty

Path: `Settings → Collaborators`.

There should be **zero** collaborators on a personal config repo. Every collaborator you
add gets access to **all historical commits**, including any secrets you committed in the
past (rotated or not).

If you ever need to share help with this repo with someone, prefer:
1. A temporary read-only branch + `gh repo create` a stripped-down public fork manually,
   OR
2. A one-off invite that you revoke immediately after the help session,
   AND
3. Rotate every secret in the repo before re-pushing, because the helper saw them.

---

## Step 9, Account-level Copilot data sharing opt-out

Path: <https://github.com/settings/copilot/features>

Find **"Allow GitHub to use my data for AI model training"** and set it to **Disabled**.

This is the canonical "do not train on my code" opt-out. It applies account-wide (covers
all your repos, public + private) regardless of whether you have a Copilot subscription.

> ⚠️ This setting is **account-wide**, not repo-level. There's currently no per-repo
> opt-out for AI training on personal accounts. The repo-level Code security panel covers
> Copilot Workspace / Copilot Code Indexing for paid org plans; personal-free repos rely on
> this account-level toggle.

`gh` CLI does not currently have a documented command for this; use the web UI.

---

## Step 10, Audit your installed GitHub Apps

Path: `https://github.com/<your-user>/<repo>/settings/installations`

This is **the most overlooked step** and often the most consequential. GitHub Apps you've
installed at the account level may have access to **all your repositories** by default,
including this private one with all your secrets.

For every installed app, click `Configure` and check:

1. **Repository access**: is it "All repositories" or "Only select repositories"?
2. **Permissions**: how broad? (Read code? Write code? Webhooks? PRs?)

For each AI / automation app, decide:

| App | Action |
|---|---|
| Claude (Anthropic) | Keep if you use Claude Code (it needs repo access for some features). |
| ChatGPT Codex Connector (OpenAI) | **Uninstall**, or restrict to "Only select repositories" excluding your config repo. Codex has Read+Write code access. |
| Devin.ai Integration | **Uninstall** or restrict. Devin is an autonomous AI agent that browses + edits repo content. |
| Cursor / Continue / other AI coding assistants | Restrict access scope; do NOT grant access to config repo. |
| Linear, Slack, Notion, etc. | Usually fine; verify they don't have code read permission. |
| Dependabot Preview / Renovate | Disabled by default for your repo if Dependabot is off (Step 4). |

The "Uninstall" button at the bottom of each Configure page is **reversible**, just
re-install if you change your mind. "Suspend" is a softer version that pauses access
without removing the app.

**Important**: changing an app from "All repositories" to "Only select repositories"
requires you to **explicitly list** which repos the app keeps access to. Use this to KEEP
the app for repos where you want it, and SILENTLY remove it from your config repo.

---

## Step 11, (Optional) Branch protection

If you ever bring in a collaborator: `Settings → Branches → Add classic branch protection
rule` → require PR review before merge to main.

For solo use, skip.

---

## Step 12, Periodic re-audit (every 30 to 90 days)

Schedule a recurring reminder to redo Steps 7 to 10. New GitHub Apps may auto-install if you
authorize an integration somewhere else (e.g., GitHub's marketplace, third-party tool
prompts). New webhooks may appear if you connect this repo to anything. Periodic re-audit
catches drift.

```bash
# Quick audit script
gh api /user/installations --jq '.installations[] | {app_slug, app_id, account: .account.login, repository_selection}'
gh repo view <your-user>/<repo> --json visibility,hasIssuesEnabled,hasWikiEnabled,hasProjectsEnabled,hasDiscussionsEnabled
gh api /repos/<your-user>/<repo>/hooks --jq 'length'
gh api /repos/<your-user>/<repo>/keys --jq 'length'
gh api /repos/<your-user>/<repo>/collaborators --jq 'length'
```

---

## Quick-reference checklist

Copy this to a sticky note when bootstrapping a fresh companion config repo:

```
□ Repo created PRIVATE (verify in incognito)
□ Features: Wikis OFF / Issues OFF / Projects OFF / Discussions OFF
□ Code security: all Dependabot OFF
□ Actions: Disabled (radio: Disable actions; Save)
□ Pages: Source None
□ Webhooks: empty
□ Deploy keys: empty
□ Actions / Codespaces / Dependabot secrets: empty
□ Collaborators: empty
□ Copilot data sharing: Disabled (account-level)
□ GitHub Apps: each audited, AI tools uninstalled or restricted
```

Total time investment ≈ 15 min the first time. Future repos using the same convention can
reuse most of these settings as defaults.

---

## Why this doc lives in market-intel, not in the companion config repo itself

The companion config repo is **generated from scratch by each user**. The doc you're reading
now is the runbook that tells them *how* to do that generation safely. Putting the runbook
inside the companion repo would create a chicken-and-egg problem (you can't read it until
you've created the thing it's instructing you to create).

This is also why `companion-config-spec.md` (the structural contract) and
`companion-config-repo.md` (the overview + tutorial) live here too. Together with this
hardening runbook they form the complete "how to set up a companion config repo" L3 reading
package referenced from `install-guide.md`.
