---
name: freight-onboard
description: "Onboard a freight-forwarding company onto this skill plugin — either set up a fresh new company (Mode A: create 7 canonical WeCom sub-sheets across two operator-provided empty smartsheet docs) or adopt an existing manually-maintained WeCom workspace (Mode B: inspect existing sub-sheets, diff against canonical schema, reconcile via add_fields / update_fields with operator approval). Conducts a short conversational intake, writes workspace/wecom/links.md, renders the daily cron config, and hands off with a clear punch-list of operator follow-up. Use when the user says 'set up freight skills for a new company', 'first install for <X 公司>', 'onboard a new freight forwarder', 'adopt existing 企微 workbench for freight skills', 'wire freight-skills to our existing 运价表/客户线索表', '我要给新货代公司装一遍', '把 freight skills 接到我们已有的企微表上'. Do NOT run after onboarding is complete — re-running won't corrupt anything but the entry point for adding incremental fields is `wecom-cli doc smartsheet_add_fields` directly."
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

# Freight onboarding — fresh-install AND adopt-existing flows

Mirrors the [cold-start-interview](https://github.com/anthropics/claude-for-legal/tree/main/ai-governance-legal/skills/cold-start-interview) pattern from `claude-for-legal`: short conversational intake → auto-provision external state → hand off with explicit unfinished items.

**Upstream wecom-cli skill reference** — for the actual `wecom-cli doc smartsheet_*` API surface (field types, cell-value formats, error codes), defer to [`WecomTeam/wecom-cli/skills/wecomcli-smartsheet/SKILL.md`](https://github.com/WecomTeam/wecom-cli/blob/main/skills/wecomcli-smartsheet/SKILL.md). That doc is canonical; this skill does NOT re-document the API.

After onboarding completes, the two operational skills (`freight-lead-profiling`, `freight-rate-daily-promotion`) read from the workspace this skill creates. They do not need re-installation.

## Detection — fresh vs configured

Run all three checks at start:

```bash
LINKS="$HOME/.openclaw/workspace/shipping-rate-automation/wecom/links.md"

# A. Workspace links.md missing or template-state
test -f "$LINKS" && ! grep -q '<填入' "$LINKS" 2>/dev/null && echo "EXISTS: $LINKS"

# B. Cron job already registered?
openclaw cron list 2>/dev/null | grep -q "freight-rate-daily" && echo "CRON: registered"

# C. Skill symlinks resolved?
test -e "$HOME/.agents/skills/freight-rate-daily-promotion" && echo "SKILL: linked"
```

- **All three indicate configured** → STOP. Tell operator "freight already configured for <company>. To add fields to an existing sheet use `wecom-cli doc smartsheet_add_fields` directly. To re-onboard with different DocIDs, delete `$LINKS` first."
- **All three indicate fresh** → proceed.
- **Partial state** → STOP. Refuse to proceed; ask operator to either complete or fully reset. A half-configured workspace is worse than no workspace.

## Mode selection

After detection, the very first intake question splits the flow:

> 您现在是 (A) **全新公司**，企微里还没建任何 freight 表？还是 (B) **公司已经在企微里手工维护着运价表/客户线索表**，希望 agent 接到现有表上？

- **Mode A (fresh new company)** → §"Mode A: Provision 7 canonical sub-sheets"
- **Mode B (adopt existing)** → §"Mode B: Adopt existing workbench"

Both modes share the conversational intake (skip the 2 docid questions in Mode A since the agent collects them differently below) — see `references/intake-questions.md`.

## Conversational intake (both modes)

8 slots, ask one at a time, validate as you go. Translate engineering terms to freight-ops Chinese ("DocID" → "企微文档 ID"; "sub-sheet" → "子表"; "field" → "列"). Full wording: `references/intake-questions.md`.

| Slot | Example | Notes |
|---|---|---|
| `company_slug` | `orientlinkage` | lowercase, hyphens OK, no spaces |
| `company_full_name` | `东方联动国际货运代理有限公司` | non-empty |
| `scenario_1_docid` | `REDACTED-DOCID...` | Mode A: operator pre-creates 1 empty smartsheet doc in 企微 UI and gives DocID. Mode B: operator's existing 拓客 workbench DocID. |
| `scenario_2_docid` | `REDACTED-DOCID...` | Mode A: same — pre-creates 1 empty doc. Mode B: existing 运价 workbench DocID. |
| `chat_channel` | `telegram` / `feishu` / `wecom` / `dingtalk` | One of the supported set |
| `chat_channel_id` | chat ID or webhook URL | Format depends on channel |
| `reviewer_handle` | operator's WeCom/email for 待审核 notifications | non-empty |
| `cron_time` | `08:00` (Asia/Shanghai) | `HH:MM`; default 08:00 |

> Why operator-provided DocIDs (not auto-create): **`wecom-cli` has no API to create a top-level smartsheet doc.** It can only add sub-sheets and fields *inside* an existing doc. So the operator clicks "新建智能表格" in 企微 UI twice (once per scenario), gives us the resulting DocIDs, and the agent fills the docs in.

## Mode A: Provision 7 canonical sub-sheets

Driver: `scripts/create-wecom-sheets.sh` reads `scripts/sheet-definitions.json` and provisions both docs in one call.

```bash
ONBOARD="$(dirname "$0")"
OUT=$(mktemp -t freight-onboard-XXXXXX.json)
bash "$ONBOARD/scripts/create-wecom-sheets.sh" \
  "$scenario_1_docid" \
  "$scenario_2_docid" \
  "$OUT"
```

What the script does for each scenario:

1. For each canonical sub-sheet (7 total — 2 in scenario 1, 5 in scenario 2):
   - `wecom-cli doc smartsheet_add_sheet '{"docid":"...","properties":{"title":"<canonical name>"}}'` → returns new `sheet_id`
   - `wecom-cli doc smartsheet_add_fields '{"docid":"...","sheet_id":"...","fields":[...]}'` → adds the canonical column list (see `scripts/sheet-definitions.json`)
2. Errors per sheet are non-fatal — script continues; failures listed in output JSON's `errors` array.

Note: each newly-created smartsheet doc starts with **one default sub-sheet** (empty, default name). The script does NOT touch it. After the script succeeds, the punch-list includes "delete the default empty sub-sheet" as an optional cleanup step.

Parse the output JSON to extract DocIDs and sheet_ids and feed them into the links.md writer (next section).

## Mode B: Adopt existing workbench

For companies already running workflows in 企微 with their own sheet layouts. The agent inspects, reports diffs, and reconciles per the operator's choice — does NOT silently mutate.

For each scenario (1 and 2), run:

```bash
# 1. List sub-sheets in the operator's existing doc
wecom-cli doc smartsheet_get_sheet '{"docid":"<scenario_N_docid>"}'
# returns: [{"sheet_id":"...", "title":"运价表 2026", ...}, ...]

# 2. For each sub-sheet, fetch its column structure
for SHEET_ID in $(...) ; do
  wecom-cli doc smartsheet_get_fields '{"docid":"<scenario_N_docid>","sheet_id":"'"$SHEET_ID"'"}'
done
```

Then for each canonical sub-sheet defined in `scripts/sheet-definitions.json`, **semantic-match** against the operator's existing sub-sheets by title + column overlap (allow rough matches: "船公司" ≈ "承运人" / "carrier", "POL" ≈ "起运港", etc.).

Build a **reconcile report** in freight-ops language and present to the operator as a checklist:

```
对照我司标准 7 张表 + 您现有的工作台 — 以下是 diff，逐项让您拍板：

[运价表]
  → 我找到您的 sub-sheet 「运价表 2026 红海版」(sheet_id sx12abc)，列结构 7/9 匹配:
    缺：「有效期」「超重费标准和其他费用」
    多：「联系业务员」「优先级」
    名字不同：「船公司」(您的) vs 「船公司」(标准) — 已对齐
  → 您要：
    (a) 用现有的 + 我帮您补 2 个缺列 (smartsheet_add_fields)
    (b) 用现有的 + 我把 2 个多列删掉 (smartsheet_delete_fields, 不可逆)
    (c) 重命名某些列对齐标准 (smartsheet_update_fields, 只改名不改类型)
    (d) 新建一张标准的 sub-sheet — 现有的留着不动

[运价信息] ...
[每日简报]
  → 没找到对应 sub-sheet。建议: 新建一张 5 列的 "每日简报 (AI)"
[推广审核] ...
[发送记录] ...
[客户线索表] ...
[待审核开发信] ...
```

Operator responds per row. Then the agent executes:

| Operator chose | Agent runs |
|---|---|
| (a) add missing columns to existing | `smartsheet_add_fields` for the missing fields |
| (b) delete extra columns | `smartsheet_delete_fields` — confirm with operator each field_id first (irreversible) |
| (c) rename a column | `smartsheet_update_fields` (can rename, cannot retype) |
| (d) create new canonical | `smartsheet_add_sheet` + `smartsheet_add_fields` |
| (e) (special) keep operator's schema, agent adapts | write column-name mapping into `wecom/links.md` so the operational skills translate at read time — see `references/column-mapping-fallback.md` |

After all 7 canonical sheets are reconciled, agent records the final (existing or newly-created) sheet_id for each into the result JSON, then proceeds to write `wecom/links.md`.

**Adopt safety rules:**
- Never call `smartsheet_delete_*` without explicit per-item operator confirmation in chat
- Never `smartsheet_update_fields` to change `field_type` (the API only renames; trying to change type silently keeps the old type)
- If a column has data already and the operator wants to remove it — STOP and ask "this column has N rows of data, delete will lose it; confirm again?" before delete

## Write workspace/wecom/links.md (both modes)

After provision/adopt produces all 7 (docid, sheet_id) pairs:

```bash
WS="$HOME/.openclaw/workspace/shipping-rate-automation"
mkdir -p "$WS/wecom" "$WS/raw/source-files" "$WS/knowledge-base" \
         "$WS/scenarios/scenario-1-lead-profiling" \
         "$WS/scenarios/scenario-2-daily-rate-promotion/runs"

cat > "$WS/wecom/links.md" <<EOF
# WeCom workspace truth source — $company_full_name
# Generated by freight-onboard skill on $(date -Iseconds)
# Mode: $mode  (A=fresh, B=adopt-existing)

## Scenario 1 workbench (拓客)
DocID: $scenario_1_docid
- 客户线索表 sheet_id: $leads_sheet_id
- 待审核开发信 sheet_id: $review_sheet_id

## Scenario 2 workbench (运价推广)
DocID: $scenario_2_docid
- 运价表（人） sheet_id: $rate_table_sheet_id
- 运价信息（人） sheet_id: $rate_info_sheet_id
- 每日简报（AI） sheet_id: $daily_brief_sheet_id
- 推广审核（AI+人） sheet_id: $promotion_review_sheet_id
- 发送记录（AI） sheet_id: $send_record_sheet_id
EOF
```

If Mode B included any column-name mapping (operator kept their schema), append a `## Column mapping` section that the operational skills translate through — see `references/column-mapping-fallback.md` for format.

The operational skills read this file before any `wecom-cli doc smartsheet_*` call.

## Render the cron config

```bash
python3 "$(dirname "$0")/scripts/render-cron-config.py" \
  --company-slug "$company_slug" \
  --chat-channel "$chat_channel" \
  --chat-id "$chat_channel_id" \
  --cron-time "$cron_time" \
  --out "$WS/../../cron/freight-rate-daily.json"

openclaw cron add --from-json "$WS/../../cron/freight-rate-daily.json"
```

## Hand-off punch list

Print to operator in freight-ops Chinese at the end:

1. **客户运价文件**：把您最新的 `运价表*.xlsx` + `运价信息*.docx` 放进 `$HOME/.openclaw/workspace/shipping-rate-automation/raw/source-files/`。这些不进 git，不上传到企微。
2. **客户线索**：在企微 `客户线索表` 子表（DocID `$scenario_1_docid` / sheet_id `$leads_sheet_id`）里手工填客户线索。**只填事实**：公司名 / 官网 / 联系人 / 来源渠道——AI 不会写这张表。
3. **聊天频道 bot token**：在 OpenClaw 配置 (`~/.openclaw/openclaw.json`) 里设好 `$chat_channel` 的 token / webhook secret。具体配法见 `freight-skills/docs/prerequisites.md` § "{chat_channel}"。
4. **(可选) Firecrawl API key**：`export FIRECRAWL_API_KEY=fc-...`（freight-lead-profiling 的网页抓取走 firecrawl CLI，没 key 会退到 web_fetch fallback）。
5. **Mode A only — 删除默认空 sub-sheet**（可选清理）：每个 doc 创建时默认带一个空子表，agent 没动它。您可以在企微 UI 里手动删掉，让 doc 只含 7 张规范子表。或者留着不影响功能。
6. **Mode B only — 数据迁移**：如果 reconcile 时操作员选择"新建标准子表"，旧子表里的数据不会自动迁移。需要手工 export + 重新 import，或 sql-style 转换。agent 不做这一步。
7. **触发一次 cron 验证**：`openclaw cron run <new cron id>`。预期：聊天频道收到完整简报正文 (plain text, 不带附件)。

## Gotchas

- **Detection must be all-or-nothing.** Partial state → STOP, ask operator to reset. Half-configured is worse than zero.
- **`wecom-cli` does NOT have `smartsheet_create` for top-level docs.** Top-level docs are operator-created in 企微 UI. The CLI only manages sub-sheets and fields **within** an existing doc. Do not try to invent a `smartsheet_create` API call — it'll fail with "unknown subcommand".
- **`smartsheet_update_fields` cannot change `field_type`.** Per [upstream skill doc](https://github.com/WecomTeam/wecom-cli/blob/main/skills/wecomcli-smartsheet/SKILL.md): "只能改名，不能改类型 (field_type 必须传原始类型)". If Mode B reconcile detects a type mismatch, the only options are: create a new column of the right type + (optionally) delete the old one, or accept the mismatch and let operational skills coerce at read time.
- **`smartsheet_delete_sheet` / `smartsheet_delete_fields` / `smartsheet_delete_records` are irreversible.** Mode B's reconcile MUST get per-item operator confirmation before any delete. Never bulk-delete on the assumption that "the operator probably wants this cleaned up."
- **Each new doc has 1 default sub-sheet** (created when operator clicks "新建智能表格" in 企微 UI). `create-wecom-sheets.sh` ignores it — adds 2 (scenario 1) / 5 (scenario 2) canonical sub-sheets alongside. Operator can delete the default later.
- **`field_title` cannot be updated to its current value** (per upstream — passing the same title to `smartsheet_update_fields` errors). Skip the rename if the current title already matches the canonical.
- **DocID resolution**: `wecom-cli` accepts either `docid` or `url` to identify a doc. URLs look like `https://doc.weixin.qq.com/smartsheet/s3_<base64>?scode=<token>` — the actual DocID is internal and revealed only via `wecom-cli doc info --url <url>` (or similar). When operator provides a URL, resolve to DocID first; never persist URLs in links.md (they contain `scode` tokens which expire).
- **`+smartsheet_add_records_auto_file`** — the `+` prefix is a wecom-cli local helper convention. Use these helpers for any record that includes image/file local paths; non-`+` `smartsheet_add_records` doesn't auto-upload local files.
- **Idempotency**: this skill does NOT clean up on operator abort. To retry from scratch, operator deletes `workspace/wecom/links.md` first. To retry Mode B reconcile after a partial run, operator marks already-done sheets in the next iteration's intake.

## What this skill does NOT do

- Does NOT install `wecom-cli`, `firecrawl-cli`, `freightindex-pp-cli`, `schedule-pp-cli`, OpenClaw, or any chat-channel bot — those are prereqs per `docs/prerequisites.md`.
- Does NOT seed real customer data into 客户线索表 — operator's job (privacy boundary).
- Does NOT send any customer-facing communication. The first time customer email goes out, it's gated by `推广审核 → 通过` AND explicit operator instruction.
- Does NOT migrate data between old and new sub-sheets in Mode B. Operator handles data migration manually if they choose "new canonical" over "reuse existing".
- Does NOT modify the canonical schema in `scripts/sheet-definitions.json` based on what existing companies have. To extend the canonical, open a PR on the freight-skills repo.
