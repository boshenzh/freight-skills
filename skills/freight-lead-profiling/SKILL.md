---
name: freight-lead-profiling
description: Process freight-forwarding sales leads — extract evidence from customer websites/public sources, infer cargo & logistics needs cautiously, score against our 航线/货类/出货规模 portfolio, and draft personalized 开发信 into the WeCom 待审核开发信 queue for human review. Use when the user mentions 客户线索, 拓客, 开发信, 客户画像, lead qualification, customer profiling, or asks to "look at this company / see if they're a fit / draft a first-touch email" — even when freight context is implicit. Do NOT use this skill for outbound mass mail, customer-facing replies without human review, or daily rate promotion drafts (those belong to `freight-rate-daily-promotion`).
---

# Freight Lead Profiling / 分析画像 + 拓客

## Audience and tone

This workflow is run **for the freight desk** — business users, not engineers. When you (the AI) **talk back** to the user (in chat-channel messages, run summaries, 画像摘要, 开发信草稿, 异常原因 fields, error reports), use **freight/operations language**, not engineering jargon.

**Translate when reporting:**
- "skill / workflow file" → 流程文档 / 工作方法
- "CLI / binary" → 数据源 / 数据查询工具
- "webprofile-pp-cli" → 贸易流数据源（UN Comtrade）
- "schedule-pp-cli" → 船期/航线数据源
- "API / endpoint" → 数据查询
- "schema" → 字段格式
- "smartsheet_add_records" → 写入企微表格
- "model" → AI 引擎
- "fail-soft" → 失败后自动降级，不影响整体流程

**Freight terms stay as-is** — these are the user's native vocabulary:
POL、POD、CLS、截关、船期、航线、船司、直航、中转、卖价、底价、成本价、开发信、画像、客户线索、目标市场、HS Code、贸易流、进口量、20GP/40GP/40HQ、LCL、起运港、目的港、转运、电放、订舱。

**When engineering specificity is unavoidable**, wrap it in a business framing. Example: instead of "fit-score returned 70 with route_covered=false", say "客户匹配度评分 70（满分 100，因为我司还没配置该国对应的航线覆盖；补全航线后可上探）" — keep the meaning, lose the field-name noise.

**Skill files and cron task descriptions stay technical** (the AI reads them); only **user-facing messages, 画像摘要 written to 待审核开发信, chat-channel notifications, and error reports** need the translation.

## Core rule

客户线索表 is facts-only. Never write assumptions into it.

Allowed input fields only:
- 公司名
- 官网
- 联系人
- 来源渠道

AI analysis belongs only in 待审核开发信 or notes, with evidence and cautious wording.

## Gotchas

Concrete corrections to mistakes the agent will make without being told:

- **客户线索表 fields are facts-only.** Never write a推测 into 公司名 / 官网 / 联系人 / 来源渠道. Reason: 业务员 expects these cells to be source-of-truth for outreach addressing; AI noise corrupts the desk's primary input.
- **Never invent customer logistics specifics.** Destination ports, monthly volume, container count, contact names, shipment frequency, target price, cargo readiness — all 待确认. Asking the customer in the 开发信 draft is fine; fabricating them in 画像 is not.
- **Workspace path is `~/.openclaw/workspace/shipping-rate-automation/`** (historical name). Repo folder is `freight-orientlinkage` but every file reference in this skill assumes the workspace dir is `shipping-rate-automation` — they are decoupled on purpose.
- **Cron-spawned PATH excludes `~/go/bin/`.** Always invoke ocean-pp-cli binaries with full path: `$HOME/go/bin/webprofile-pp-cli ...`, `$HOME/go/bin/schedule-pp-cli ...`. Skipping this causes silent CLI skip → unbacked profile.
- **Step 3a/3b CLI calls are fail-soft, not required.** `webprofile-pp-cli` (Comtrade) and `schedule-pp-cli` (lane coverage) are *enhancements*. If they fail (network, rate-limit, missing binary), fall back to evidence-only profile — never block a lead on a CLI error.
- **Cite at most ONE concrete stat per draft.** When step 3a returns Comtrade data, you may cite one signal ("Egypt imported \$1.35B HS 8517 from China in 2025, +69% YoY") to ground the pitch. Stacking multiple stats reads as a data-dump; one clear hook beats five lukewarm ones.
- **First-touch length cap.** ~90–140 English words or concise Chinese equivalent. No first-touch attachments. No fake `Re:`. No spammy words. No unsupported savings claims. The high-reply playbook (`references/high-reply-development-letter-playbook.md`) is the rubric — score the draft against it before writing to 待审核.
- **`审核状态` defaults are NOT auto-pass.** Useful draft → `待审核`. Insufficient info → `需补充信息`. Clearly not a fit → `归档` or `拒绝`. Never default to `通过` — that's the 业务员's call, not the AI's.
- **Translation rule when reporting to operator.** Engineering terms (skill / CLI / API / schema / model / fail-soft / smartsheet_add_records) get translated to freight-ops vocabulary (流程文档 / 数据源 / 数据查询 / 字段格式 / AI 引擎 / 失败自动降级 / 写入企微表格). **Freight terms stay native** (POL / POD / CLS / 截关 / 船期 / 直航 / 中转 / 卖价 / 底价 / 开发信 / 画像 / HS Code / 20GP/40GP/40HQ / 起运港 / 目的港).
- **Firecrawl CLI requires `FIRECRAWL_API_KEY`.** Install via `npm install -g firecrawl-cli` (CLI v1.16+); first-time setup also accepts `firecrawl login` (browser flow) or `firecrawl login --api-key fc-...`. Key on VPS lives in env (`export FIRECRAWL_API_KEY=fc-...` in shell rc) or `~/.firecrawl/config`. **Without it the CLI returns 401 silently** — the step-2 instructions above explicitly fall back to `web_fetch` and log the fallback, do not crash. Reference: https://github.com/firecrawl/cli

## WeCom workspace

**DocIDs are NOT in this skill file** — they are per-company and live in:
`$HOME/.openclaw/workspace/shipping-rate-automation/wecom/links.md`

That file is created by the `freight-onboard` skill on first install. Read it before every WeCom write to get the company-specific DocID + sheet IDs for the two sheets this skill uses:

- **客户线索表** — facts-only customer leads (operator-maintained; AI never writes)
- **待审核开发信** — AI-drafted profile + outreach awaiting review

Validate the schema with `wecom-cli doc smartsheet_get_fields` before writing — the schema may evolve. See [`wecom-sheet-schemas.md`](../freight-onboard/references/wecom-sheet-schemas.md) for the canonical 4-column / 15-column structures.

## Required workflow

### 1. Read leads

Use WeCom CLI to read 客户线索表 records.

Only process rows with at least 公司名 and/or 官网. If 官网 is blank, use company-name web search; if no reliable public page is found, mark 信息不足.

### 2. Get public information

**Primary**: drive the [firecrawl CLI](https://github.com/firecrawl/cli). It handles JS-rendered SPAs reliably and returns clean markdown — much better signal than raw `web_fetch` on modern marketing sites.

```bash
# Scrape the customer site (default subcommand is scrape).
firecrawl https://customer-example.com --json --pretty > /tmp/lead-<id>.json

# Find a customer when the website is missing/broken — search by company name.
firecrawl search "Customer Company Name Ltd export" --json

# Map all URLs on the customer domain when the homepage is sparse (find about/products pages).
firecrawl map https://customer-example.com --json
```

Read the JSON output's `markdown` / `links` / `metadata` fields. The `metadata.description` / `metadata.ogDescription` often summarize the customer's business better than the first H1 on the page.

**Fallback**: if `firecrawl` CLI is not on PATH (no `FIRECRAWL_API_KEY`, CLI not installed), fall back to the agent's built-in `web_fetch` / `web_search`. Results will be lower quality on SPA-heavy sites but better than nothing — note the fallback in the run log so the operator knows to install firecrawl on this VPS.

Extract only evidence-backed facts:
- 主营业务 / products
- 市场定位 / customer type
- export/global signals
- target market signals (Middle East, India, Pakistan, US, Europe, Africa, etc.)
- product/cargo characteristics visible from the site

Do not bypass login, CAPTCHA, paywalls, or private systems. Do not invoke `firecrawl interact` / `firecrawl agent` (interactive features — clicks, form fills, multi-step flows) for first-touch lead profiling — those require explicit operator approval and a sandbox session. First-touch lead research stays on public surfaces only.

### 3. Analyze profile and matching

Use the rubric in `references/matching-rubric.md` when deciding:
- 潜在需求
- 航线匹配
- 货类匹配
- 出货规模匹配
- 综合匹配度

Always separate:
- 已确认：directly visible in source
- 合理推测：inferred from product/category, with cautious wording
- 待确认：destination port, volume, container type, shipment frequency, target price, cargo readiness

Never invent exact destination ports, monthly volume, container count, contact names, or shipment frequency.

#### 3a. Trade-flow data (webprofile-pp-cli) — optional, fail-soft

When the customer has a clear country and product (HS) signal, use `webprofile-pp-cli` to back the profile with UN Comtrade trade flows. Call when reasonable; **never block the lead on CLI failure** — fall back to evidence-only profile.

> ⚠️ Path note: ocean-pp-cli binaries (`webprofile-pp-cli`, `schedule-pp-cli`) live in `~/go/bin/`, not on default cron PATH. Always invoke with `$HOME/go/bin/...` to avoid silent skips.

```bash
# Resolve country / HS first if needed
$HOME/go/bin/webprofile-pp-cli country "Egypt" --json
$HOME/go/bin/webprofile-pp-cli hs-search "telecom equipment" --json

# Score fit
$HOME/go/bin/webprofile-pp-cli fit-score Egypt 8517 --json
```

Capture in 画像 / 综合匹配度:
- `import_from_cn` and `import_from_world` (year, USD)
- `yoy_growth_pct` (latest vs prior year)
- `fit_score` (0-100; 70 max if no covered routes configured — note that explicitly when reporting)
- `route_covered` flag

Mark this data as `webprofile/Comtrade YYYY` in evidence; it is public trade-flow signal, not customer-specific facts.

#### 3b. Lane coverage (schedule-pp-cli) — optional, fail-soft

When you can credibly identify a likely POL (e.g. our company's main 出运港 from raw files) and the customer's destination country/region, verify carrier/service coverage:

```bash
$HOME/go/bin/schedule-pp-cli carriers --start-port-code CNNSA --json
$HOME/go/bin/schedule-pp-cli fleet-routes --start-port-code CNNSA --carrier CMA --json
```

Use this only to confirm or contradict 航线匹配; never invent a specific sailing/CLS for the lead.

### 4. Reference our business/raw files as needed

For our business strengths and wording, use distilled templates first, then raw files only when needed. Each reference loads on demand — only when the trigger condition fires, not up-front.

| File | Load when |
|---|---|
| `references/high-reply-development-letter-playbook.md` | About to draft 任意 outreach text — score the draft against this playbook's rubric before writing to 待审核 |
| `references/matching-rubric.md` | Scoring 综合匹配度 / 航线 / 货类 / 出货规模 in step 3 |
| `references/raw-file-map.md` | Need to cite a specific raw运价 file or 推广模板 — don't load every run |
| `references/templates/outreach-templates.md` | Need first-touch wording structure |
| `references/templates/follow-up-templates.md` | Drafting a follow-up (not first-touch) message |
| `references/templates/promotion-template.md` | Piggy-backing on a current promotion in the outreach — rare; usually scenario 2 owns this |

Use templates for reusable phrasing and structure. Use 运价表 / 运价信息 only for actual route/price/service facts. Use raw 推广模板 / 跟进话术 only to refine the templates, not during every run.

### 5. Draft outreach

Before drafting, apply `references/high-reply-development-letter-playbook.md`.

Draft a personalized development email/企微 message for human review. It should include:
- 客户业务呼应 based on evidence
- one possible logistics pain point, phrased cautiously
- one relevant advantage only: route / price / service / response / comparison ability
- concrete low-friction next action: ask target market, shipment plan, cargo ready date, container type, or whether they want a short reference rate/sailing comparison

High-reply constraints:
- keep first-touch drafts short: about 90–140 English words or concise Chinese equivalent
- use one clear subject line and one CTA
- avoid first-touch attachments, fake `Re:`, spammy words, unsupported savings claims, or full company-brochure style
- score the draft with the playbook rubric; only useful drafts should enter `待审核`
- when 3a / 3b returned data, you may cite **one** concrete signal (e.g. "Egypt imported $1.35B of HS 8517 from China in 2025, +69% YoY") to ground the pitch — do not stack multiple stats; one clear hook beats a data dump

No external sending. Write to 待审核开发信 only.

### 6. Write 待审核开发信

Use WeCom CLI to append a row to 待审核开发信 with fields:
- 客户名
- 官网
- 联系人
- 来源渠道
- 信息获取状态
- 主营业务摘要
- 市场定位
- 潜在需求分析
- 与我司业务匹配度
- 画像摘要
- 开发信草稿
- 审核状态
- 人工指定发送渠道
- 异常原因
- 更新时间

If you used webprofile/schedule data in step 3, append a short evidence line to 画像摘要 like:
`webprofile fit_score=70 (Egypt HS 8517, import_from_cn=$1.35B 2025, YoY+69%); schedule confirms CNNSA→Red Sea coverage via CMA/MSC`

Default 审核状态:
- `待审核` when useful draft exists
- `需补充信息` when insufficient info
- `归档` or `拒绝` when clearly not a fit

### 7. Exception handling

If no useful public info:
- 信息获取状态 = `信息不足`
- 审核状态 = `需补充信息`
- 异常原因 = clear reason
- Keep basic info; do not create a confident pitch.

If business mismatch:
- 信息获取状态 = `已获取`
- 审核状态 = `归档` or `拒绝`
- 异常原因 = `业务不匹配：...`
- Keep basic info in the queue/document for traceability.

## Output style

When reporting back to the user, include:
- processed count
- created 待审核 rows count
- insufficient/mismatch count
- link to WeCom workbench
- any blockers or suggested schema improvements

## Suggested improvements to propose when useful

If the user is designing the system, recommend adding these fields to 待审核开发信:
- 证据链接 / Source URL
- 置信度 / Confidence
- 最近检查时间 / Last checked
- 建议语言 / CN or EN
- 去重键 / company + domain
- 审核人 / reviewer
- 发送结果 / sent, skipped, replied

Do not alter the WeCom schema unless the user asks.
