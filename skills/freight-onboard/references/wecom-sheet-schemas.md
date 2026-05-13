# WeCom smartsheet schemas — canonical column structures

The 7 canonical sub-sheets `freight-onboard` creates (Mode A) or reconciles against (Mode B). Schemas mirror two production reference workbenches:

- **Scenario 2** (运价推广 — 5 sheets): https://doc.weixin.qq.com/smartsheet/s3_REDACTED-WORKBENCH
- **Scenario 1** (拓客 — 2 sheets): https://doc.weixin.qq.com/smartsheet/s3_REDACTED-WORKBENCH

All 7 sub-sheets live **inside** 2 operator-pre-created smartsheet docs (one per scenario). `wecom-cli` has no API for top-level doc creation — operator does that in 企微 UI; the agent then provisions sub-sheets and fields via `smartsheet_add_sheet` + `smartsheet_add_fields`.

Machine-readable version (used by `scripts/create-wecom-sheets.sh`): `scripts/sheet-definitions.json`.

## Column types — wecom-cli `FIELD_TYPE_*` enums

Per [upstream `wecomcli-smartsheet` SKILL.md](https://github.com/WecomTeam/wecom-cli/blob/main/skills/wecomcli-smartsheet/SKILL.md) and its [`smartsheet-field-types.md`](https://github.com/WecomTeam/wecom-cli/blob/main/skills/wecomcli-smartsheet/references/smartsheet-field-types.md) (canonical), the 7 sheets use only:

- `FIELD_TYPE_TEXT` — free-text (most columns)
- `FIELD_TYPE_CHECKBOX` — boolean (1 column: `成本价检查` in `推广审核（AI+人）`)

For values written to text fields, see the cell-value format reference upstream — `text` cells take `[{"type":"text","text":"..."}]` shape. Multi-line content goes in the same single text value (newlines preserved).

## Scenario 2 workbench: 5 sheets

### Sheet 1 · 运价表（人） — maintained by 业务

Structured rate table. Human-maintained — AI reads, never writes.

| Column | `field_type` | Notes |
|---|---|---|
| 区域 | TEXT | e.g. 红海 / 印巴 / 美线 / 欧地 / 非洲 / 中东 |
| POD | TEXT | 目的港 short code or city (e.g. JEDDAH / KARACHI) |
| 船公司 | TEXT | e.g. PIL / CMA / MSC / TSL / SJJ |
| 20GP | TEXT | USD price for 20GP — text allows "实单单询" / "暂无" |
| 40GP | TEXT | USD price for 40GP |
| 40HQ | TEXT | USD price for 40HQ |
| 有效期 | TEXT | multi-line — e.g. "2026-03-17" or "至 03-20 截关" |
| POL | TEXT | 起运港 short code (SK / NS / DCB / YT) |
| 超重费标准和其他费用 | TEXT | multi-line free text |

### Sheet 2 · 运价信息（人） — maintained by 业务

Unstructured rate paragraphs extracted from 运价信息.docx.

| Column | `field_type` | Notes |
|---|---|---|
| 入库日期 | TEXT | YYYY-MM-DD |
| 区域 | TEXT | as above |
| 段落标题 | TEXT | e.g. "PIL 红海卖价大票" |
| 原文 | TEXT | multi-line full paragraph |
| 来源 | TEXT | source file reference |
| 解析状态 | TEXT | "已解析" / "需补充" / "拒绝外发" |
| 备注 | TEXT | free text |

### Sheet 3 · 每日简报（AI） — written by AI

5-column index sheet. AI appends one row per cron run. Brief body does NOT go here — it goes to the chat channel.

| Column | `field_type` | Notes |
|---|---|---|
| 日期 | TEXT | YYYY-MM-DD |
| 简报标题 | TEXT | "场景2 每日运价简报 YYYY-MM-DD HH:mm" |
| 推广审核状态 | TEXT | "待审核" / "需补充信息" / "通过" / "拒绝" / "无可推" |
| 备注 | TEXT | short stat line |
| 更新时间 | TEXT | YYYY-MM-DD HH:mm ISO |

### Sheet 4 · 推广审核（AI+人） — AI writes, human reviews

Customer-safe promotion drafts awaiting review.

| Column | `field_type` | Notes |
|---|---|---|
| 推广标题 | TEXT | e.g. "红海方向近期优势参考" |
| 推广信息草稿 | TEXT | multi-line plain-text promotion (NO cost prices) |
| 内部依据摘要 | TEXT | summary of source rate rows used |
| **成本价检查** | **CHECKBOX** | true if AI verified no 成本/底价/拿价 leaked |
| 审核状态 | TEXT | "待审核" / "通过" / "拒绝" / "需补充信息" |
| 目标客户/分组 | TEXT | customer segment hint |
| 人工指定发送渠道 | TEXT | "邮件" / "企微" / "LinkedIn" / etc. |
| 更新时间 | TEXT | YYYY-MM-DD HH:mm |

> The CHECKBOX in this sheet is the only non-TEXT column across all 7. CHECKBOX values are written as raw `true` / `false` (not wrapped in `{"type":"checkbox",...}`). See upstream cell-value format reference.

### Sheet 5 · 发送记录（AI） — written by AI

Audit log of approved external sends.

| Column | `field_type` | Notes |
|---|---|---|
| 发送时间 | TEXT | ISO timestamp |
| 客户名 | TEXT | |
| 联系人 | TEXT | |
| 邮箱 | TEXT | |
| 航线/区域 | TEXT | |
| 邮件主题 | TEXT | |
| 发送状态 | TEXT | "成功" / "失败" / "退信" |
| 错误原因 | TEXT | non-empty on failure |
| 回复状态 | TEXT | "无回复" / "已回复" / "已成单" — updated later by 业务员 |

## Scenario 1 workbench: 2 sheets

### Sheet 6 · 客户线索表 — facts-only, human-maintained

**Critical**: AI NEVER writes to this sheet. Only the operator adds rows.

| Column | `field_type` | Notes |
|---|---|---|
| 公司名 | TEXT | required |
| 官网 | TEXT | URL — may be blank |
| 联系人 | TEXT | may be blank |
| 来源渠道 | TEXT | e.g. "展会名单" / "目标客户调研" |

### Sheet 7 · 待审核开发信 — AI writes, human reviews

| Column | `field_type` | Notes |
|---|---|---|
| 客户名 | TEXT | mirrors 客户线索表.公司名 |
| 官网 | TEXT | |
| 联系人 | TEXT | |
| 来源渠道 | TEXT | |
| 信息获取状态 | TEXT | "已获取" / "信息不足" / "搜索失败" |
| 主营业务摘要 | TEXT | evidence-backed, freight-ops language |
| 市场定位 | TEXT | e.g. "B2C 跨境电商" / "工程承包" |
| 潜在需求分析 | TEXT | logistics inferences with cautious wording |
| 与我司业务匹配度 | TEXT | "高" / "中" / "低" + reasoning |
| 画像摘要 | TEXT | 1-2 sentence customer profile |
| 开发信草稿 | TEXT | 90-140 word draft |
| 审核状态 | TEXT | "待审核" / "通过" / "需补充信息" / "拒绝" / "归档" |
| 人工指定发送渠道 | TEXT | "邮件" / "LinkedIn" / "企微外联" |
| 异常原因 | TEXT | non-empty if 信息获取状态 != "已获取" or 审核状态 = "需补充信息" |
| 更新时间 | TEXT | YYYY-MM-DD HH:mm |

## Why all-TEXT plus one CHECKBOX

Choosing TEXT for almost everything is deliberate:
- Allows empty / placeholder values like `实单单询`, `暂无`, `需人工确认` without API errors
- Allows multi-line content in single cells (e.g. `有效期` with multiple lines)
- Avoids per-WeCom-tenant option-set drift (single-select / multi-select fields require pre-defining options, which adds onboarding friction)

The one CHECKBOX (`成本价检查`) is a hard quality gate — AI sets it true only after explicitly verifying no internal price terms leaked into the customer-facing draft. TEXT would let the AI write "是" / "false" / "yes" / "通过" / any string the model improvises that day, which would break downstream filtering.

## Schema evolution

To add or change a canonical column, follow this order:

1. Update `scripts/sheet-definitions.json` (the machine-readable source of truth that `create-wecom-sheets.sh` uses)
2. Update this file to match (the human-readable contract)
3. Update the corresponding operational skill (`freight-lead-profiling` or `freight-rate-daily-promotion`) to consume the new column
4. Tag a new freight-skills release
5. Each company that already onboarded runs `wecom-cli doc smartsheet_add_fields` on their existing sub-sheet to backfill the new column

Don't add columns silently — every column the agent writes must be visible in this doc.
