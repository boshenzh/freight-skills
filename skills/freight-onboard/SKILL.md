---
name: freight-onboard
description: "Onboard a fresh freight-forwarding company onto this skill plugin — detect a clean install (no workspace/wecom/links.md or template-state file), conduct a short conversational intake (company name, WeCom workspace, preferred chat channel + chat ID, customer raw-rate file location), automatically create the 7 required WeCom smartsheets (scenario-2 dual-source 运价表/运价信息 + AI 每日简报 + 推广审核 + 发送记录; scenario-1 客户线索表 + 待审核开发信) per the canonical column schemas, write the resulting DocIDs into workspace/wecom/links.md, render a cron config from the user-provided chat channel binding, and hand off with a clear punch-list of what the operator still needs to do manually. Use when the user says 'set up freight skills for a new company / onboard new freight company / first install of freight automation / fresh install / install freight for <X 公司> / 我要给新货代公司装一遍 / 第一次配置 freight skills'. Do NOT use after the company is already configured — re-running will not corrupt anything but it's not the right entry point for adding new sheets to an existing company."
author: "boshenzh"
license: "Apache-2.0"
argument-hint: "<company-slug>"
allowed-tools: "Read Write Edit Bash"
metadata:
  openclaw:
    requires:
      bins:
        - wecom-cli
---

# Freight onboarding — fresh company setup

This skill runs when a brand-new freight forwarder is setting up `freight-skills` on their VPS for the first time. It mirrors the [cold-start-interview](https://github.com/anthropics/claude-for-legal/tree/main/ai-governance-legal/skills/cold-start-interview) pattern from `claude-for-legal`: short conversational intake → auto-provision the required external state → hand off with explicit unfinished items.

After onboarding, the two operational skills (`freight-lead-profiling`, `freight-rate-daily-promotion`) read from the workspace this skill creates. They do not need re-installation.

## Detection — is this a fresh install?

Run these three checks at the start; only proceed if ALL THREE indicate fresh:

```bash
# 1. No workspace/wecom/links.md, or it contains only template/placeholder DocIDs
test -f "$HOME/.openclaw/workspace/shipping-rate-automation/wecom/links.md" || echo "FRESH: no links.md"
grep -q '{{DOCID' "$HOME/.openclaw/workspace/shipping-rate-automation/wecom/links.md" 2>/dev/null && echo "FRESH: template placeholders"

# 2. No registered cron job for this skill family
openclaw cron list 2>/dev/null | grep -q "freight-rate-daily" || echo "FRESH: no cron"

# 3. ~/.agents/skills/freight-* symlinks point at this freight-skills plugin (not a private Layer 3 fork)
readlink "$HOME/.agents/skills/freight-rate-daily-promotion" 2>/dev/null | grep -q "freight-skills" || echo "FRESH or non-standard"
```

If ANY check indicates the company is already configured, **stop** and tell the operator: "freight already configured for <company> — to add or update sheets use `wecom-cli` directly, not this skill."

## Conversational intake

Run through the 8-question intake from `references/intake-questions.md`. Don't batch all 8 in one block — ask one at a time, build on prior answers, validate as you go. The exact wording is up to you; the slots to fill are:

| Slot | Example | Validation |
|---|---|---|
| `company_slug` | `orientlinkage` | lowercase, hyphens OK, no spaces |
| `company_full_name` | `东方联动国际货运代理有限公司` | non-empty |
| `wecom_workspace_url` | `https://doc.weixin.qq.com/...` | parses to a WeCom space the operator can access |
| `chat_channel` | `telegram` / `feishu` / `wecom` / `dingtalk` | one of the supported set |
| `chat_channel_id` | (Telegram chat ID like `123456789`, 飞书 webhook URL, etc.) | format depends on channel |
| `raw_rate_dir` | `~/.openclaw/workspace/shipping-rate-automation/raw/source-files/` | absolute path that exists OR can be created |
| `reviewer_handle` | operator's WeCom/email for `待审核` notifications | non-empty |
| `cron_time` | `08:00` (Asia/Shanghai) | `HH:MM` format; default 08:00 |

Use freight-ops language, not engineering jargon — the operator may be a 业务员 not a developer. Translate "DocID" → "企微文档 ID"; "smartsheet" → "企微表格".

## Create the 7 WeCom smartsheets

Read the canonical column structures from `references/wecom-sheet-schemas.md`. Then create each sheet via `wecom-cli`:

```bash
# Try the supported create command — exact flag set varies by wecom-cli version.
wecom-cli doc smartsheet_create --json '{
  "title": "运价表（人）",
  "columns": [
    {"name":"区域","type":"text"},
    {"name":"POD","type":"text"},
    {"name":"船公司","type":"text"},
    {"name":"20GP","type":"text"},
    {"name":"40GP","type":"text"},
    {"name":"40HQ","type":"text"},
    {"name":"有效期","type":"text"},
    {"name":"POL","type":"text"},
    {"name":"超重费标准和其他费用","type":"text"}
  ]
}' > /tmp/sheet-rate-table.json
```

Parse the resulting docid + sheet_id from the response. Repeat for all 7 sheets — see `references/wecom-sheet-schemas.md` for each table's columns.

**Fallback if `wecom-cli` doesn't expose `smartsheet_create`**: load `references/manual-fallback.md` and follow it. You'll print precise manual instructions for the operator to create each sheet in the WeCom UI, then prompt them to paste each DocID back to you. Then continue.

## Write workspace/wecom/links.md

After all 7 sheets exist (auto-created or manual), write the binding file:

```bash
WS="$HOME/.openclaw/workspace/shipping-rate-automation"
mkdir -p "$WS/wecom" "$WS/raw/source-files" "$WS/knowledge-base" \
         "$WS/scenarios/scenario-1-lead-profiling" \
         "$WS/scenarios/scenario-2-daily-rate-promotion/runs"

cat > "$WS/wecom/links.md" <<EOF
# WeCom workspace truth source — {company_full_name}
# Generated by freight-onboard skill on $(date -Iseconds)

## Scenario 1 workbench (拓客)
DocID: <填入 scenario-1 docid>
- 客户线索表 sheet_id: <填入>
- 待审核开发信 sheet_id: <填入>

## Scenario 2 workbench (运价推广)
DocID: <填入 scenario-2 docid>
- 运价表（人） sheet_id: <填入>
- 运价信息（人） sheet_id: <填入>
- 每日简报（AI） sheet_id: <填入>
- 推广审核（AI+人） sheet_id: <填入>
- 发送记录（AI） sheet_id: <填入>
EOF
```

The operational skills read this file before any `wecom-cli doc smartsheet_*` call — never hardcode DocIDs in skill files.

## Render the cron config

Use `scripts/render-cron-config.py` to produce a `cron/freight-rate-daily.json` from the intake answers:

```bash
python3 "$(dirname "$0")/scripts/render-cron-config.py" \
  --company-slug "$company_slug" \
  --chat-channel "$chat_channel" \
  --chat-id "$chat_channel_id" \
  --cron-time "$cron_time" \
  --out "$WS/../../cron/freight-rate-daily.json"
```

Then register the cron:

```bash
openclaw cron add --from-json "$WS/../../cron/freight-rate-daily.json"
```

## Hand-off punch list

Print this to the operator in freight-ops language at the very end, **so they know what's still on them**:

1. Put your latest 运价表 (xlsx) + 运价信息 (docx) into:
   `$HOME/.openclaw/workspace/shipping-rate-automation/raw/source-files/`
2. Fill the new 客户线索表 (sheet `{leads_sheet_id}`) with your current customer lead pipeline — keep it facts-only (公司名 / 官网 / 联系人 / 来源渠道).
3. Configure the chat channel bot token in OpenClaw config (`~/.openclaw/openclaw.json`) — see `freight-skills/docs/prerequisites.md` for the per-channel setup.
4. (Optional) Configure `FIRECRAWL_API_KEY` env if you want firecrawl-based website scraping for lead profiling (recommended). See `freight-skills/docs/prerequisites.md`.
5. Manually trigger one cron run to verify end-to-end:
   `openclaw cron run <new cron id>`
   You should receive the daily 简报 as plain text in your configured chat channel.

## Gotchas

- **Detection must be all-or-nothing.** If you partially-detect a fresh install (some signals fresh, some configured) — refuse to proceed and ask the operator to clean up first. A half-configured workspace is worse than no workspace.
- **wecom-cli `smartsheet_create` may not exist.** If the command returns "unknown subcommand", switch to the manual-fallback flow — do not try to invent a different API. Manual fallback is documented in `references/manual-fallback.md`.
- **DocIDs from `smartsheet_create` response shape** varies — read one returned record carefully before assuming where `docid` and `sheet_id` live in the JSON.
- **Idempotency**: this skill does NOT clean up after itself if the operator aborts mid-flow. If the operator wants to retry, they delete `workspace/wecom/links.md` first.
- **Cron config schema**: see `freight-skills/docs/workspace-spec.md` § cron — must include `delivery.channel`, `delivery.to`, `payload.message`, etc. Do not invent fields.

## What this skill does NOT do

- It does NOT install `wecom-cli`, `firecrawl-cli`, `freightindex-pp-cli`, `schedule-pp-cli`, OpenClaw, or any chat-channel bot — those are prereqs per `docs/prerequisites.md`.
- It does NOT seed any real customer data into the new 客户线索表 — that's the operator's job (and a privacy boundary).
- It does NOT send any customer-facing communication. The first time customer email goes out, it's gated by `推广审核 → 通过` AND explicit operator instruction.
