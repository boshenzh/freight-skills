# Prerequisites for freight-skills

These tools must be installed on the VPS before the skills can function. The `freight-onboard` skill checks for each one and warns if missing.

## Core (required)

### OpenClaw

Agent runtime. Skill discovery, cron scheduling, plugin install. Install per OpenClaw docs.

**The Gateway must be running.** Every `openclaw cron` command — registration *and* the scheduled trigger itself — talks to the OpenClaw Gateway. If it's down, `openclaw cron list/add` fails with "gateway closed" and scheduled jobs never fire. Start it with `openclaw gateway start`. On a VPS, run the Gateway under a process supervisor (a systemd unit on Linux, a launchd plist on macOS) so it restarts after a crash or reboot — otherwise a Gateway that quietly dies takes the daily brief down with it. Writing that supervisor unit is per-VPS ops, out of scope for this repo.

### wecom-cli

WeCom 企业微信 smartsheet read/write. `freight-onboard` (Mode A) calls `wecom-cli doc create_doc` to create the 2 workbench docs, then `smartsheet_add_sheet` / `smartsheet_add_fields` to provision the sub-sheets. The two operational skills call `smartsheet_get_records` / `smartsheet_add_records` / `smartsheet_update_records` / `smartsheet_get_fields`.

Install via your internal channel (private binary).

**Auth — `wecom-cli init`.** wecom-cli must be logged in to the WeCom account that owns the workspace before it can read/write real DocIDs. Run its interactive auth flow (`wecom-cli init`) **as the same OS user OpenClaw runs as** — an isolated cron session inherits that user's `$HOME`, so the token/session it picks up must belong to that user. If a cron run reports an auth error (errcode `40001` / `40014` / `41001` etc.), re-run `wecom-cli init`.

### Chat channel

The daily 简报 is delivered to one chat channel: Telegram / 飞书 / 企微 group bot / 钉钉. The channel is registered with OpenClaw via `openclaw channels add`; the cron job's `--channel` + `--to` then point at it.

- **Telegram**: create a bot via @BotFather, get the bot token. Register it:
  ```bash
  openclaw channels add --channel telegram --token <bot-token>
  # or: --token-file <path>   or: --use-env  (read the token from an env var)
  ```
  The cron's `--to` is your numeric chat ID.
- **飞书 / 企微 / 钉钉**: create a group custom bot, copy its webhook URL. Register the channel per OpenClaw's docs for that channel type; the cron's `--to` is the webhook URL.

`freight-onboard` asks which channel and prompts for the right kind of ID/URL, then registers the cron with `--channel` + `--to`. It does **not** create the bot or run `openclaw channels add` for you — that's a one-time manual step.

### Model provider

The daily cron runs an agent turn on a specific model — `openclaw cron add --model <alias>` (the binding repo pins this in `cron/cron-params.json`; `freight-onboard` omits it and uses OpenClaw's default). Whatever alias you use, OpenClaw must be able to route it: the provider and its API key live in OpenClaw's own config (`~/.openclaw/openclaw.json` or env), **not** in this repo. Verify with `openclaw models list` — the alias the cron uses must appear. A cron pinned to a model OpenClaw can't route fails every morning.

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
