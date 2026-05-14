---
name: freight-rate-daily-promotion
description: Run the daily freight-rate brief + customer promotion workflow — read WeCom 事实源 (运价表 + 运价信息 dual-source), pull SCFI market context, sanity-check 船期/CLS, classify 成本价 vs 卖价, generate the internal 简报 as plain text for the configured chat channel (Telegram / 飞书 / 企业微信 / 钉钉 etc., per cron.delivery.channel), and queue customer-safe 推广 copy to 推广审核 for human approval. Use when the user mentions 每日运价简报, daily rate promotion, 运价表/运价信息, 推广草稿, 推广审核, 简报, or asks to "generate today's brief / extract rates / push promotion for review / refresh SCFI". Triggers automatically via the daily 08:00 Asia/Shanghai cron. Do NOT use this skill to directly email customers — the human approval gate (推广审核 → 通过) is mandatory; AI never bypasses it.
---

# Freight Rate Daily Promotion / 场景2 每日运价整理 + 推广

## Audience and tone

This workflow is run **for the freight desk** — business users, not engineers. When you (the AI) **talk back** to the user (in chat-channel messages, run summaries, brief 备注, 推广审核 fields, error reports), use **freight/operations language**, not engineering jargon.

**Translate when reporting:**
- "skill / workflow file" → 流程文档 / 工作方法
- "CLI / binary" → 数据源 / 数据查询工具
- "freightindex-pp-cli" → 上海集装箱运价指数 (SCFI) 数据源
- "schedule-pp-cli" → 船期/航线数据源
- "webprofile-pp-cli" → 贸易流数据源（UN Comtrade）
- "API / endpoint" → 数据查询
- "schema / field validation" → 字段格式校验
- "edit_doc_content / smartpage_create" → 覆写文档 / 新建文档
- "cron / job" → 每日定时任务
- "model" → AI 引擎
- "PATH not found" → 系统找不到这个工具
- "fail-soft" → 失败后自动降级，不影响整体流程

**Freight terms stay as-is** — these are the user's native vocabulary:
POL、POD、CLS、截关、船期、航线、船司、直航、中转、卖价、底价、成本价、推广草稿、待审核、事实源、风险拦截、字段错位、有效期、20GP/40GP/40HQ、LCL、运价、订舱、转运、起运港、目的港、加价策略、免柜期、电放、SCFI、加班船。

**When engineering specificity is unavoidable**, wrap it in a business framing. Example: instead of "the schema requires `list[CellUrlValue]`", say "企微文档链接字段格式不对，需要按企微规定的链接格式重新写入" — keep the *meaning* (what action is needed) without the technical noise.

**Skill files and cron task descriptions stay technical** (the AI reads them); only **user-facing messages, brief text, sheet 备注, chat-channel notifications, and error reports** need the translation.

## Core rules

- Treat source files as internal pricing data. Do not expose 成本价 to customers.
- Separate internal brief from external promotion:
  - **内部简报** may include 成本价、卖价、利润/加价策略、备注、风险。
  - **推广信息** may include only customer-safe price/service facts approved for sending.
- Never email customers until the business-side review status is explicitly approved.
- If route/rate fields are ambiguous, mark `需人工确认`; do not guess POL/POD, carrier, validity, or price type.
- Preserve source traceability: file name, sheet/section, row/paragraph, extracted timestamp.

## Gotchas

Concrete corrections to mistakes the agent will make without being told. Read this before each run.

- **成本价/底价/采购价/拿价/cost/net/未分类价格 NEVER appear in 推广信息.** Only 卖价 / 指导卖价 / 红卖 may go to customer-facing output. Run the quality gate at §"Quality gates" before writing to `推广审核`; if any internal price term leaks, stop and route to `需补充信息` instead of `待审核`. Reason: leaking cost = leaking margin = career-ending mistake for the desk.
- **Workspace path is `~/.openclaw/workspace/shipping-rate-automation/`** (historical convention). Repo folder is `freight-orientlinkage`; workspace dir is `shipping-rate-automation`. The decoupling is intentional — do not "fix" it.
- **Cron-spawned PATH excludes `~/go/bin/`.** Always invoke `$HOME/go/bin/freightindex-pp-cli` / `$HOME/go/bin/schedule-pp-cli` with FULL path. Bare `freightindex-pp-cli` from cron silently fails → §1a/§2a fall-soft fires unnecessarily and you miss SCFI/CLS data when it was actually available.
- **SCFI + CLS calls are fail-soft, but the *attempt* is required.** Every run must call `freightindex-pp-cli pull` + `digest` and `schedule-pp-cli pull` + `next-cls`. Capture stdout+stderr into the run folder so logs prove the attempt was made. Only after a real failure write `SCFI 数据暂缺（原因：…）` / `船期校验暂缺（原因：…）` and continue. Never write `暂缺` without first calling.
- **Chat-channel simplicity is a hard constraint.** Applies regardless of `cron.delivery.channel` (Telegram / 飞书 / 企业微信 / 钉钉 / etc.) — Boshen's standing rule across channels is plain-text-only. Final reply MUST contain the full 简报正文 as plain text in chat — first line `场景2 每日运价简报 YYYY-MM-DD`, blocks separated by `-------------------------`. NO Markdown headers (`#`/`##`), NO tables, NO fenced code blocks, NO PDF, NO HTML, NO emoji, NO visual styling, NO `MEDIA:`, NO `.txt` attachment, NO `--media`, NO `--force-document`. If 简报 nears the chat channel's per-message length limit, split into multiple plain-text messages — still no attachment.
- **每日简报 sheet writes 5 columns only.** `日期 / 简报标题 / 推广审核状态 / 备注 / 更新时间`. 简报正文 does NOT go into the sheet (WeCom TEXT field silently truncates). Old fields (简报正文, 简报类型, 企微文档链接, DocID, 来源批次, 推广审核记录, 输出文件夹) are removed — do not re-introduce them.
- **`scripts/md2pdf.py` is DEPRECATED.** Kept in repo for history. Do NOT call it. Boshen's latest rule is plain-text only; PDF generation is banned. If a task description mentions PDF, treat it as stale.
- **Dual-source merge key.** Build the working set by `(区域, POD, 船公司, POL)`. On conflict, prefer 运价表（人） (structured) over 运价信息（人） (docx prose). Lines from 运价信息 not present in 运价表 → add to working set, mark `来源=运价信息`. Sheet IDs come from workspace/wecom/links.md — never hardcoded.
- **Cost-vs-sell labeling from headers/text:** keywords `成本/底价/拿价/采购价/cost/net/内部/利润` → 成本价（不进推广候选）. Keywords `卖价/指导卖价/红卖/价格表为卖价` → 卖价（可进推广候选）. No clear marker → default to 拦截.
- **No vessel name in 推广** unless user explicitly asks. 内部简报 may contain vessel name + voyage; 推广信息 default is 起运港/目的港/运价/CLS/直航or中转 only.
- **Run-folder housekeeping runs FIRST**, before reading 事实源. Archive `>30 day` folders to `archive/<name>.tar.gz` and `rm -rf` the originals. Skipping this lets folders accumulate (~365 per year) and slows future reads.
- **Risk-interception rows do NOT go to the chat-channel body.** Field 错位 / 过期 CLS / 数值异常 / `#REF` 公式错误 / 实单单询未确认 → write only to local `run-status.md` and 企微 备注 / 审核依据. Do not pollute the daily brief 业务员 sees in chat.

## Scenario 2 WeCom workbench

**DocIDs and sheet IDs are NOT in this skill file** — they are per-company and live in:
`$HOME/.openclaw/workspace/shipping-rate-automation/wecom/links.md`

That file is created by the `freight-onboard` skill on first install. The canonical labels and column structures (the skill's actual contract) are:

| Label in workspace/wecom/links.md | 维护者 | 用途 |
|---|---|---|
| 运价表（人） | 业务 | 结构化运价 9 列：区域 / POD / 船公司 / 20GP / 40GP / 40HQ / 有效期(多行) / POL / 超重费标准和其他费用(多行) |
| 运价信息（人） | 业务 | docx 段落原文：入库日期 / 区域 / 段落标题 / 原文 / 来源 / 解析状态 / 备注 |
| 每日简报（AI） | AI | **index sheet 5 列**：日期 / 简报标题 / 推广审核状态 / 备注 / 更新时间。简报正文不进 sheet（见 §4b）|
| 推广审核（AI+人） | AI 写 + 人审 | 推广草稿待审核队列 |
| 发送记录（AI） | AI | 批准后的客户外发记录 |

Full column schemas: see [`wecom-sheet-schemas.md`](../freight-onboard/references/wecom-sheet-schemas.md).

Before writing, query fields with `wecom-cli doc smartsheet_get_fields` because schema may evolve.

### WeCom field-shape gotchas

WeCom smartsheet `add_records` / `update_records` accept a value-union per field. Pick the right discriminator or the call fails with cryptic pydantic + server errors. Cheat sheet:

- `FIELD_TYPE_TEXT` →
  ```json
  [{"text": "value", "type": "text"}]
  ```
- `FIELD_TYPE_URL` (e.g. `每日简报.企微文档链接`) →
  ```json
  [{"link": "https://...", "text": "display text", "type": "url"}]
  ```
  All three keys (`link`, `text`, `type:"url"`) required; bare `{link, text}` errors with `2022016 invalid url value`; passing as object instead of list errors with pydantic `list[CellUrlValue]`.
- `FIELD_TYPE_CHECKBOX` → `true` / `false` (raw bool, not list).
- Unsure? Read one existing record via `smartsheet_get_records` and copy the exact value shape returned.

## Canonical input files

Default source directory:
`$HOME/.openclaw/workspace/shipping-rate-automation/raw/source-files/`

Common source files:
- `运价表*.xlsx` — structured rates, may include cost/sell prices, POL/POD, carrier, schedule, remarks.
- `运价信息*.docx` — unstructured route notes and promotional wording.
- `每日运价简报*.docx` — style/sample reference, not authoritative pricing unless user says so.
- `推广模板*.docx` — promotion style reference only.

References load on demand. Each file pulls into context only when the trigger condition fires — not every run.

| File | Load when |
|---|---|
| `references/field-normalization.md` | Classifying a column / paragraph price — cost vs sell vs unclear |
| `references/output-templates.md` | Drafting brief or promotion output structure |
| `references/daily-rate-brief-source.md` | Generating the 08:00 internal 简报 (mandatory read — distilled from `每日运价简报---b1d9bb06-...docx`) |
| `references/promotion-template-source.md` | Generating customer-facing 推广 copy (distilled from `推广模板---d43cac25-...docx`) |

## Available scripts

Scripts live under `scripts/`. Invoke them with a path relative to the skill directory — `scripts/<name>` — not an absolute path (the skill's install location varies by runtime).

| Script | Purpose | Invocation |
|---|---|---|
| `scripts/extract_rate_inputs.py` | Parse latest `运价表*.xlsx` + `运价信息*.docx` → normalized JSON + rough Markdown digest. Used in §1. | `python3 scripts/extract_rate_inputs.py --input-dir <raw-dir> --out-dir <run-dir>` |

> Historical note: an earlier `md2pdf.py` script existed for generating PDF briefs. It was removed in v0.2 — Boshen's standing rule is plain-text-only delivery to any chat channel (see Gotchas §"Chat-channel simplicity"). PDF generation is permanently banned. If a task description mentions PDF, treat it as stale.

## Required workflow

### 1. Locate and extract sources

**Empty-state guard — check this FIRST, before housekeeping or anything else.** If `raw/source-files/` contains no `运价表*.xlsx` and no `运价信息*.docx`:

- This is the normal state on day 1 (operator hasn't dropped files yet) and on any day nobody uploaded rates. It is **not** an error.
- **Do NOT silently abort.** Post one short plain-text message to the configured chat channel (`cron.delivery.channel`), e.g.:
  ```
  场景2 每日运价简报 YYYY-MM-DD
  今日无运价数据上传，简报跳过。
  ```
  Then exit cleanly (success, not failure).
- Skip SCFI/CLS calls and all sheet writes — there is nothing to brief on.
- Rationale: a silent abort is indistinguishable from "the cron never fired." An observable skip message tells the operator the automation is alive and simply had no input today.

1. Find the latest `运价表*.xlsx` and/or `运价信息*.docx` unless the user provides paths.
2. Run `scripts/extract_rate_inputs.py` to produce:
   - normalized JSON (`daily-rate-extract.json`)
   - rough Markdown digest (`daily-rate-extract.md`)
3. Inspect the digest before finalizing; scripts are helpers, not final authority.

Example:

```bash
python3 scripts/extract_rate_inputs.py \
  --input-dir $HOME/.openclaw/workspace/shipping-rate-automation/raw/source-files \
  --out-dir $HOME/.openclaw/workspace/shipping-rate-automation/scenarios/scenario-2-daily-rate-promotion/runs/$(date +%F)
```

#### 1a. SCFI big-picture context (freightindex-pp-cli) — required attempt, fail-soft

To anchor the brief in market reality, pull this week's SCFI snapshot and produce a small lane digest. Do this **before** classifying rates so the brief can flag rates that diverge from market trend.

> ⚠️ Path note for cron-isolated agents: `freightindex-pp-cli` lives in `~/go/bin/`, which is not on the default `PATH` for cron-spawned sessions. **Always invoke via the full path** below, or the call will silently fail and you'll skip straight to the fallback. Same applies to `schedule-pp-cli` and `webprofile-pp-cli` in §2a / scenario 1.

```bash
# Refresh local SCFI snapshot store; safe to run daily
$HOME/go/bin/freightindex-pp-cli pull --json

# Render the lanes the desk cares about (replace --lane filters as needed)
$HOME/go/bin/freightindex-pp-cli digest --lane 'Persian Gulf' --lane 'Mediterranean' --lane 'Red Sea' --markdown
```

Use the digest to fill the brief's market-context section:
- comprehensive index level + WoW %
- lane-level moves for the lanes our desk runs
- if SCFI shows a lane up >5% WoW but our 卖价 didn't move, surface it as `今日观察`

Required attempt: **call `pull` and `digest` every run**. Capture the raw output (or stderr) into the run folder so the run log proves the attempt was made.

Fail-soft rule: if SCFI fetch fails (network, rate limit, etc.) **or** the binary is genuinely missing, write the brief with `SCFI 数据暂缺（原因：<one-line reason>）` in the market-context section and continue. Never block on this. Do not write `暂缺` without first attempting the call.

### 2. Normalize and classify rates

For each route/rate item, fill what is available:
- 航线/区域
- 起运港 POL
- 目的港/国家/区域 POD
- 船司/服务
- 20GP / 40GP / 40HQ / LCL / 空运 if present
- 成本价 / 卖价 / 未分类价格
- 币种
- 截关/开船/航程/中转/免柜期/有效期
- 备注/限制
- source file + sheet/row or paragraph

Price classification:
- Headers or nearby text containing 成本、底价、拿价、采购价、cost => 成本价.
- Headers or nearby text containing 卖价、报价、对外、销售价、sell => 卖价.
- If unclear, use `未分类价格` and mark `需人工确认`.

#### 2a. Sailing/CLS sanity check (schedule-pp-cli) — required attempt, fail-soft

For each rate row that has POL + carrier identifiable, cross-check with Weiyun schedule data. **Always attempt** these calls; only fall back to "no-CLS-check" if the binary or API actually fails.

```bash
$HOME/go/bin/schedule-pp-cli pull
$HOME/go/bin/schedule-pp-cli next-cls <route-code> --json   # e.g. NS-JEDDAH
```

Use the result as a **sanity signal**:
- If our 有效期 / CLS in 事实源 falls before the next sailing's CLS returned by `next-cls`, push the row to **风险拦截 / 过期船期** and include the next sailing CLS for context.
- If POL/carrier doesn't resolve via `schedule-pp-cli`, **do not** invent a sailing — keep the original 事实源 timing and continue, log the unresolved route in the run log.

Required attempt: **call `pull` once and `next-cls` for each unique route** that has POL+carrier. Save the JSON outputs in the run folder so the run log proves the attempt was made.

Fail-soft rule: if `schedule-pp-cli` is missing or all calls fail, write `船期校验暂缺（原因：<one-line reason>）` in the brief's risk section and continue with the original 事实源 timing. Never block.

Never overwrite the 事实源 with schedule-pp-cli output; the 事实源 is human-maintained truth. Schedule data is corroboration only.

### 3. Apply quotation strategy

If the user or business team gives a strategy, apply it explicitly. Examples:
- 固定加价：成本价 + USD 50/柜
- 百分比：成本价 × 1.08
- 分航线策略：红海加 USD 100，印巴加 USD 50
- 保留原卖价：使用表内卖价

If no strategy is provided:
- Use existing 卖价 when clearly present.
- If only 成本价 exists, do **not** invent customer quote; generate internal brief with `待报价策略`.

### 4. Generate outputs

Create two outputs:

1. **《每日运价简报》内部版**
   - **必读** `references/daily-rate-brief-source.md` — 包含结构模板、提取规则、禁区。
   - **结构是硬约束**：按 **船司 + 区域分块**（如 "PIL 红海"、"KMTC 蛇口出红海中转船"、"深圳 CUL 红海"、"TSL 印巴"、"SJJ 印巴"），**禁止按 POD 分块**。每块格式严格对齐参考文件里的模板。
   - **每行字段顺序**：`POL-POD USD<20GP>/<40GP>` + 备注（中转天数、免柜期、附加费、限重、跳港等）。POL 用紧凑缩写（SK / NS / DCB / YT），不要 "SK蛇口" 这种冗余写法。
   - **必须保留的业务深度字段**（在事实源里有的就提取，不要丢）：
     - 船名 + 航次号（来自「船司/服务」或「原始备注」，如 `KOTA PELANGI 0048W`）
     - 中转天数（来自「航程」或「原始备注」，如 `MUN 中转约 26 天`）
     - 免柜期（来自「免柜期」字段，如 `21 天免柜`）
     - 附加费（来自「附加费/本地费」字段，如 `AQJ 已含 EIS USD100/200`、`NSA 含 CIC USD150/300`）
     - 操作变更/跳港（来自「限制条件」或「原始备注」，如 `本航次跳港巴生`、`原船 CEPAT omit SHK，KAMIL 替代收货`）
   - **单询占位**：某船司有港名但卖价空时，写 "实单单询 JIB"（或对应中转港）保留行，**不拦截**。
   - **块之间用 `-------------------------` 分隔**。
   - **块内不能混入** 成本价、底价、采购价、利润、加价策略 — 这些进单独的内部 review 段。
   - **纯文本硬约束**：业务员收到的每日简报必须是直接贴在聊天频道（`cron.delivery.channel` — Telegram / 飞书 / 企微 / 钉钉 等）正文里的 plain text，不要作为 `.txt` 附件；不要 Markdown 标题、表格、code fence、PDF、HTML、emoji 或任何视觉样式。
   - **顶部最多 1 行紧凑统计**：如 `[运价表 77 行 / 运价信息 9 段 / SCFI 1954.21 +2.24%]`。不要输出 SCFI 表格、Top5、总览大段。
   - **不要在发给业务员的聊天正文里附风险拦截段**：字段错位、过期 CLS、数值异常等只写入本地 `run-status.md` 和企微备注/审核依据，不作为聊天频道简报正文。

2. **推广信息外发版**
   - read `references/promotion-template-source.md` first
   - follow the raw promotion template style: extract each port's best direct/transshipment price and schedule; include POL, rate, and CLS/sailing only; do not include vessel name unless the user asks
   - short, customer-safe route blocks
   - no 成本价, no internal margin, no source-file internals
   - include validity caveat: `以上均为直航/中转服务，价格已含已确认基础附加费，具体以订舱确认为准。欢迎询价订舱，更多船期及中转方案请随时联系！`
   - if facts are incomplete, ask for route parameters instead of quoting

### 4b. 简报落地 — 本地 plain txt 追溯 → 聊天频道正文 + 5 列 index sheet（2026-05-11 修正）

⚠️ **当前架构（以 Boshen 最新要求为准）**：
- 最早：滚动 brief doc（已废弃）。
- 上一版：简报正文塞进 sheet（**WeCom TEXT 字段静默截断**，废弃）。
- 上一版：本地 markdown + PDF（**废弃**，Boshen 明确要求 `no style / plain txt`）。
- 当前：本地 UTF-8 plain `.txt` 仅作追溯备份 + 聊天频道（`cron.delivery.channel`）直接发送完整简报正文，sheet 只做 5 列 index。

简报输出三处：
1. **本地** `runs/cron-YYYY-MM-DD-HHMMSS/daily-brief.txt`（完整纯文本，追溯用）
2. **聊天频道**（cron.delivery.channel：当前 Telegram；可切飞书/企微/钉钉）直接把完整简报正文贴到 chat（不要 `.txt` 附件；业务员/Boshen 主要阅读位置）
3. **企微每日简报（AI）** 只写 5 列 index，不写正文

#### 纯文本格式硬约束

- 不要生成 `daily-brief.md` 作为主产物；不要生成 PDF/HTML；不要调用 `md2pdf.py`。
- 不要 Markdown 标题（`#` / `##`）、表格、fenced code block、加粗/斜体、emoji、视觉排版。
- 第一行：`场景2 每日运价简报 YYYY-MM-DD`。
- 第二行可选紧凑统计：`[运价表 N 行 / 运价信息 M 段 / SCFI xxx +x.xx%]`。
- 之后直接进入船司+区域分块；块之间用 `-------------------------`。
- 风险拦截、Top5、SCFI 表格、运行日志不要进入发送给业务员的聊天正文；只写 `run-status.md` / 企微备注。

#### 发简报正文到聊天频道（channel-agnostic）

定时任务最终回复必须直接包含完整简报正文（plain text），不要只发摘要，不要使用 `MEDIA:`，不要调用附件发送，不要把 `daily-brief.txt` 作为 document 发出。规则适用于 cron.delivery.channel 配置的任何频道（Telegram / 飞书 / 企微 / 钉钉 等）。

如果简报过长接近所在频道的单条消息长度上限，优先分成多条连续纯文本消息；仍然不要发附件。

#### 5 列 index sheet 写一行

`每日简报（AI）` sheet (sheet_id resolved from workspace/wecom/links.md) 只写 5 列：

| 字段 | 内容 |
|------|------|
| 日期 | `YYYY-MM-DD` |
| 简报标题 | `场景2 每日运价简报 YYYY-MM-DD HH:mm` |
| 推广审核状态 | `待审核` / `需补充信息` / `通过` / `拒绝` / `无可推` |
| 备注 | Top5 摘要 + 关键数据签名（如「77 表行 / 9 docx 段 / 0 拦截异常 / 红海占 100%」） |
| 更新时间 | `YYYY-MM-DD HH:mm` ISO |

旧字段已删除（简报正文 / 简报类型 / 企微文档链接 / DocID / 来源批次 / 推广审核记录 / 输出文件夹）— **不要再写**。

First resolve DocID + sheet_id from workspace:

```bash
DAILY_BRIEF_DOCID=$(awk '/Scenario 2/,0' "$HOME/.openclaw/workspace/shipping-rate-automation/wecom/links.md" | awk -F': ' '/^DocID/ {print $2; exit}')
DAILY_BRIEF_SHEET=$(awk '/每日简报/ {print $NF; exit}' "$HOME/.openclaw/workspace/shipping-rate-automation/wecom/links.md")

wecom-cli doc smartsheet_add_records '{
  "docid": "'"$DAILY_BRIEF_DOCID"'",
  "sheet_id": "'"$DAILY_BRIEF_SHEET"'",
  "records": [{"values": {
    "日期": [{"text":"2026-05-11","type":"text"}],
    "简报标题": [{"text":"场景2 每日运价简报 2026-05-11 08:30","type":"text"}],
    "推广审核状态": [{"text":"待审核","type":"text"}],
    "备注": [{"text":"77 表行 / 9 docx 段 / 0 拦截异常 / 红海占 100%","type":"text"}],
    "更新时间": [{"text":"2026-05-11 08:35","type":"text"}]
  }}]
}'
```

**禁止调用** `smartpage_create` / `create_doc` / `edit_doc_content`。不要重建简报字段。

#### Dual-source 合并

每次 cron 读取两个源并合并工作集（不写回任何「人」表）：

- 用 `(区域, POD, 船公司, POL)` 做 key 去重；同一 key 优先取「运价表（人）」（结构清晰）。
- 「运价信息（人）」原文里出现但运价表没有的航线/船司 → 解析后补进工作集，简报「来源」标 `运价信息`。
- 解析 docx 原文：识别一段顶部「{船司} {区域} {价格类型}」title（PIL红海卖价大票/KMTC红海中转船卖价/中山RCL红海成本价/深圳CUL红海...），每个 POD 行抽出 20GP/40GP/40HQ + 服务（直航/中转）+ 免柜期 + 备注，做为虚拟「行」加入工作集。
- 段标题或行里出现「成本价/底价/采购价/拿价/cost/net/内部/利润」→ 该段所有行**仅内部展示**，不进推广候选。
- 段标题或行里出现「卖价/指导卖价/红卖/价格表为卖价」→ 该段所有行可进推广候选。
- 既无明确卖价标记也无成本标记 → 默认拦截。

### 5. Push for business review

Default review output should be written to a local run folder and, when WeCom docs are configured by the user, to the relevant WeCom review table/document.

Recommended review statuses:
- `待审核` — ready for business review
- `需补充信息` — missing strategy or ambiguous fields
- `通过` — approved by human
- `拒绝/归档` — not to send

### 6. Send approved promotions

Only after approval:
1. Select customer segments matched to the route.
2. Generate one email per customer/segment.
3. Include only approved external promotion text.
4. Send via configured email tool if the user explicitly instructs sending.
5. Record send result and timestamp.

## 08:30 automation design (2026-05-11 重构)

每日定时任务流水线（每日 08:00 Asia/Shanghai cron 触发，模型由 cron 配置指定）：

1. **Housekeeping**：tar+rm 30 天前的 run 文件夹（见下方）。
2. **双源读**：从 workspace/wecom/links.md 解析出 运价表（人）和 运价信息（人） 的 sheet_id，再 `wecom-cli doc smartsheet_get_records` 同时拉它们。
3. **SCFI 拉取**（§1a）+ **CLS 校验**（§2a）— 失败 fail-soft 不中断。
4. **合并 + 分类**：按 dual-source 合并规则建立工作集；提取卖价候选与拦截行。
5. **生成 daily-brief.txt** 本地，按「模板一」紧凑分块格式（见 §4 + `references/daily-rate-brief-source.md`），但必须是纯文本。
6. **发完整简报正文到聊天频道**（`cron.delivery.channel` 配置的频道：当前 Telegram，可切飞书/企微/钉钉）plain text，不要 `.txt` 附件，不要 `MEDIA:`。不要生成/发送 PDF。
7. **写 5 列 index** 到 `每日简报（AI）` sheet (sheet_id from workspace/wecom/links.md)（见 §4b）。
8. **写推广审核** 到 `推广审核（AI+人）` sheet (sheet_id from workspace/wecom/links.md)，状态 `待审核` 或 `需补充信息`。
9. **cron announce 短文本** 摘要到聊天频道：简报记录 ID + 审核记录 ID + 数量 + 需人工确认问题 + 「未发客户邮件」声明。
10. **绝不发客户邮件**：步骤 6 (`发送记录`) 必须由人工把推广审核改为 `通过` 并明确指示发送后才能进入。

Do not combine the brief/promotion-draft step and customer-send into an unattended pipeline.

## Run folder maintenance (housekeeping)

Each cron writes to `$HOME/.openclaw/workspace/shipping-rate-automation/scenarios/scenario-2-daily-rate-promotion/runs/cron-YYYY-MM-DD-HHMMSS/`. Without cleanup these accumulate (currently 365 folders/year).

At the **start** of each cron run, archive folders older than 30 days into a single tarball, then delete the originals:

```bash
RUNS=$HOME/.openclaw/workspace/shipping-rate-automation/scenarios/scenario-2-daily-rate-promotion/runs
ARCHIVE_DIR=$HOME/.openclaw/workspace/shipping-rate-automation/scenarios/scenario-2-daily-rate-promotion/archive
mkdir -p "$ARCHIVE_DIR"

# Find folders >30 days old; tar+gzip each into archive/ then rm -rf the original
find "$RUNS" -maxdepth 1 -mindepth 1 -type d -mtime +30 -print0 | while IFS= read -r -d '' dir; do
  name=$(basename "$dir")
  tar -czf "$ARCHIVE_DIR/${name}.tar.gz" -C "$RUNS" "$name" && rm -rf "$dir"
  echo "archived $name → $ARCHIVE_DIR/${name}.tar.gz"
done
```

Rules:
- Run housekeeping **first**, before reading 事实源 — so a slow archive doesn't push the brief past 08:30 visibility.
- `-mtime +30` uses file mtime; folders are created once and rarely re-touched, so mtime = creation day. Safe.
- Archive directory keeps the .tar.gz forever (cheap), so audit/legal can still reach old runs.
- If the cron's parent process is killed mid-archive, partial tarballs are harmless on rerun (find+tar idempotent for new files).

## Quality gates

Before reporting success:
- Confirm extraction ran without fatal errors.
- Count rates/items extracted from Excel and Word separately.
- Count items with 成本价, 卖价, and 未分类价格.
- State whether customer-safe promotion contains any internal price/cost terms; if yes, block sending.
- State blockers: missing source file, no strategy, ambiguous columns, no approved recipients.
- For step 1a / 2a CLI calls, state whether they succeeded; CLI failure is **not** a blocker — note it in the run log and proceed without that section.
