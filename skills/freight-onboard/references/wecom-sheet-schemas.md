# WeCom smartsheet schemas — canonical column structures

These are the **exact** column structures `freight-onboard` creates for a new company, mirrored from two production reference workbenches:

- **Scenario 2** (运价推广 — 5 sheets): https://doc.weixin.qq.com/smartsheet/s3_AWMACQa7AM0CNOKw7IXI9RXq0wtTl
- **Scenario 1** (拓客 — 2 sheets): https://doc.weixin.qq.com/smartsheet/s3_AWMACQa7AM0CNSEDiTxi4QKa5bWkK

All 7 sheets are created in the new company's WeCom workspace as **empty tables with these exact columns and types**. No data is copied across companies.

## Scenario 2 workbench: 5 sheets

### Sheet 1 · 运价表（人） — maintained by 业务

Structured rate table. Human-maintained — AI reads, never writes.

| Column | Type | Notes |
|---|---|---|
| 区域 | text | e.g. 红海 / 印巴 / 美线 / 欧地 / 非洲 / 中东 |
| POD | text | 目的港 short code or city (e.g. JEDDAH / KARACHI) |
| 船公司 | text | e.g. PIL / CMA / MSC / TSL / SJJ |
| 20GP | text | USD price for 20GP — text type allows "实单单询" / "暂无" |
| 40GP | text | USD price for 40GP |
| 40HQ | text | USD price for 40HQ |
| 有效期 | text | multi-line allowed — e.g. "2026-03-17" or "至 03-20 截关" |
| POL | text | 起运港 short code (SK / NS / DCB / YT) |
| 超重费标准和其他费用 | text | multi-line free text — e.g. "AQJ 已含 EIS USD100/200" |

### Sheet 2 · 运价信息（人） — maintained by 业务

Unstructured rate paragraphs extracted from 运价信息.docx — human-maintained.

| Column | Type | Notes |
|---|---|---|
| 入库日期 | text | YYYY-MM-DD |
| 区域 | text | as above |
| 段落标题 | text | e.g. "PIL 红海卖价大票" |
| 原文 | text | multi-line full paragraph text |
| 来源 | text | source file reference |
| 解析状态 | text | "已解析" / "需补充" / "拒绝外发" |
| 备注 | text | free text |

### Sheet 3 · 每日简报（AI） — written by AI

5-column index sheet. AI appends one row per cron run. Brief body does NOT go here — it goes to the chat channel.

| Column | Type | Notes |
|---|---|---|
| 日期 | text | YYYY-MM-DD |
| 简报标题 | text | "场景2 每日运价简报 YYYY-MM-DD HH:mm" |
| 推广审核状态 | text | "待审核" / "需补充信息" / "通过" / "拒绝" / "无可推" |
| 备注 | text | short stat line (e.g. "77 表行 / 9 docx 段 / 0 拦截 / 红海占 100%") |
| 更新时间 | text | YYYY-MM-DD HH:mm ISO |

### Sheet 4 · 推广审核（AI+人） — AI writes, human reviews

Customer-safe promotion drafts awaiting review.

| Column | Type | Notes |
|---|---|---|
| 推广标题 | text | e.g. "红海方向近期优势参考" |
| 推广信息草稿 | text | multi-line plain-text promotion (NO cost prices) |
| 内部依据摘要 | text | summary of source rate rows used |
| 成本价检查 | checkbox | true if AI verified no 成本/底价/拿价 leaked |
| 审核状态 | text | "待审核" / "通过" / "拒绝" / "需补充信息" |
| 目标客户/分组 | text | customer segment hint |
| 人工指定发送渠道 | text | "邮件" / "企微" / "LinkedIn" / etc. |
| 更新时间 | text | YYYY-MM-DD HH:mm |

### Sheet 5 · 发送记录（AI） — written by AI

Audit log of approved external sends.

| Column | Type | Notes |
|---|---|---|
| 发送时间 | text | ISO timestamp |
| 客户名 | text | |
| 联系人 | text | |
| 邮箱 | text | |
| 航线/区域 | text | |
| 邮件主题 | text | |
| 发送状态 | text | "成功" / "失败" / "退信" |
| 错误原因 | text | non-empty on failure |
| 回复状态 | text | "无回复" / "已回复" / "已成单" — updated later by 业务员 |

## Scenario 1 workbench: 2 sheets

### Sheet 6 · 客户线索表 — facts-only, human-maintained

**Critical**: AI NEVER writes to this sheet. Only the operator adds rows.

| Column | Type | Notes |
|---|---|---|
| 公司名 | text | required |
| 官网 | text | URL — may be blank if unknown |
| 联系人 | text | name + role if known; may be blank |
| 来源渠道 | text | e.g. "展会名单" / "目标客户调研" / "客户推荐" |

### Sheet 7 · 待审核开发信 — AI writes, human reviews

| Column | Type | Notes |
|---|---|---|
| 客户名 | text | mirrors 客户线索表.公司名 |
| 官网 | text | |
| 联系人 | text | |
| 来源渠道 | text | |
| 信息获取状态 | text | "已获取" / "信息不足" / "搜索失败" |
| 主营业务摘要 | text | evidence-backed, freight-ops language |
| 市场定位 | text | e.g. "B2C 跨境电商" / "工程承包" / "传统贸易" |
| 潜在需求分析 | text | logistics inferences with cautious wording |
| 与我司业务匹配度 | text | "高" / "中" / "低" + reasoning |
| 画像摘要 | text | 1-2 sentence customer profile |
| 开发信草稿 | text | 90-140 word draft, freight-ops voice |
| 审核状态 | text | "待审核" / "通过" / "需补充信息" / "拒绝" / "归档" |
| 人工指定发送渠道 | text | "邮件" / "LinkedIn" / "企微外联" / etc. |
| 异常原因 | text | non-empty if 信息获取状态 != "已获取" or 审核状态 = "需补充信息" |
| 更新时间 | text | YYYY-MM-DD HH:mm |
