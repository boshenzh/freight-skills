# Prerequisites for freight-skills

These tools must be installed on the VPS before the skills can function. The `freight-onboard` skill checks for each one and warns if missing.

## Core (required)

### OpenClaw

Agent runtime. Skill discovery, cron scheduling, plugin install. Install per OpenClaw docs.

### wecom-cli

WeCom 企业微信 smartsheet read/write. The `freight-onboard` skill calls `wecom-cli doc smartsheet_create` (if supported) or falls back to manual create instructions. The two operational skills call `wecom-cli doc smartsheet_get_records` / `smartsheet_add_records` / `smartsheet_update_records` / `smartsheet_get_fields`.

Install via your internal channel (private binary).

### Chat channel bot

One of: Telegram bot, 飞书 webhook bot, 企微 group bot, 钉钉 custom bot.

- **Telegram**: create a bot via @BotFather, get the bot token + your chat ID. Configure both in OpenClaw's delivery layer (`~/.openclaw/openclaw.json` or env).
- **飞书 / 企微 / 钉钉**: create a group custom bot, copy the webhook URL.

The `freight-onboard` skill asks you which channel and prompts for the right kind of ID/URL.

## Industry data CLIs (required for scenario 2)

Install from `ocean-pp-cli`:

```bash
go install github.com/boshenzh/ocean-pp-cli/freightindex-pp-cli/cmd/freightindex-pp-cli@latest
go install github.com/boshenzh/ocean-pp-cli/schedule-pp-cli/cmd/schedule-pp-cli@latest
go install github.com/boshenzh/ocean-pp-cli/webprofile-pp-cli/cmd/webprofile-pp-cli@latest
```

Or via `npx printing-press install <name>`. Resulting binaries land in `~/go/bin/`. **Important**: cron-spawned sessions don't have `~/go/bin` on PATH — the skills always invoke with the full path `$HOME/go/bin/<binary>`.

Used for:
- `freightindex-pp-cli pull --json && digest` — SCFI market context (every cron run)
- `schedule-pp-cli pull && next-cls --json` — sailing/CLS sanity check (every cron run)
- `webprofile-pp-cli country / hs-search / fit-score` — Comtrade trade-flow data (freight-lead-profiling step 3a)

All three are fail-soft: skill never blocks on their failure.

## Web scraping for scenario 1

### firecrawl-cli (recommended)

Primary website scraper for `freight-lead-profiling`. Handles JS-rendered SPAs (modern marketing sites) — much better signal than `web_fetch`.

```bash
npm install -g firecrawl-cli         # global install
# OR run on demand:
npx -y firecrawl-cli@1.16.2 init -y --browser
```

Authentication — one of:
- `export FIRECRAWL_API_KEY=fc-xxxxx` in shell rc
- `firecrawl login` (browser flow)
- `firecrawl login --api-key fc-xxxxx`

Get a key at https://firecrawl.dev.

Verify: `firecrawl --version` (should print `v1.16+`).

### web_fetch / web_search (fallback)

Built into most agent runtimes. Used when `firecrawl` is unavailable. Lower signal quality on SPA sites — note the fallback in the run log so the operator knows to install firecrawl.

## Optional (scenario 3 — future)

### mirador (IMAP IDLE watcher)

For the planned scenario 3 (IMAP inquiry → auto-quote). Install from [pimalaya/mirador](https://github.com/pimalaya/mirador):

```bash
cargo install --git https://github.com/pimalaya/mirador.git --features imap,keyring --locked
```

### himalaya (IMAP/SMTP CLI)

Companion to mirador for read/write. `brew install himalaya` or cargo from [pimalaya/himalaya](https://github.com/pimalaya/himalaya).

## Verify everything

After install, the `freight-onboard` skill's first-step prereq check probes each binary. Or manually:

```bash
openclaw --version
wecom-cli --version
$HOME/go/bin/freightindex-pp-cli --version
$HOME/go/bin/schedule-pp-cli --version
$HOME/go/bin/webprofile-pp-cli --version
firecrawl --version
mirador --version      # only needed for scenario 3
himalaya --version     # only needed for scenario 3
```
