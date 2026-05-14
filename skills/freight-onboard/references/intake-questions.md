# Onboarding intake questions — conversational order

Ask one at a time. Use freight-ops Chinese, not engineering English. Validate each answer before moving on. Acknowledge each answer (e.g. "OK，公司叫东方联动，下一步问您...").

The intake has 9 questions: a mode-selection question + 8 detail questions.

## Q0 · 模式选择（Mode A vs Mode B）

> 我先确认下您的起点：
>
> **(A) 全新公司**——您还没在企微里建任何 freight 表，从头开始。
> **(B) 已经手工维护**——您的运价表/客户线索表已经在企微里跑着，希望 agent 接到现有表上。

Slot filled: `mode` ∈ {A, B}.

- Mode A → continue to Q1
- Mode B → continue to Q1 (intake is the same; only the provisioning phase differs)

## Q1 · 公司名

> 您公司的中文全称（例如「东方联动国际货运代理有限公司」）和英文简称（例如 `orientlinkage`，会用在仓库名和路径里）：

Slots filled: `company_full_name`, `company_slug`.

## Q2 · 企微 workspace 接入

**Mode A 措辞**（跳过 — agent 会自动建文档）：

> Mode A 模式下我会**自动**给您建 2 个空 smartsheet 文档（一个"拓客"、一个"运价推广"），命名 "{公司名} — Scenario N..."。不需要您预先建。等下我会通过 `wecom-cli doc create_doc` 一键创建并填好 7 张子表。
>
> （你只需要确认企微账户有 smartsheet 创建权限——一般每个企微员工默认都有。）

Slot filled: 无（无需操作员输入；docids 在 provision 阶段才生成）。

**Mode B 措辞：**

> 您现有的两个工作台 URL：
>
> 1. **拓客 workbench**（含 客户线索表 / 待审核开发信 之类）的 URL
> 2. **运价推广 workbench**（含 运价表 / 推广审核 之类）的 URL
>
> 把完整 URL 给我（`https://doc.weixin.qq.com/smartsheet/s3_...?scode=...` 这一整串），我直接用 `url` 参数调 wecom-cli，不需要您单独提取 DocID。
>
> 如果您只有一个 workbench 把两套表混在一起，告诉我，我适应。

Slots filled: `scenario_1_workbench_url`, `scenario_2_workbench_url`. Special-case: if operator reports a single mixed workbench, both slots get the same URL and Mode B reconcile groups sub-sheets by scenario via naming patterns.

## Q3 · 聊天频道（chat channel）

> 每日 08:00 自动简报推到哪个聊天频道？选项：
> - `telegram` （需要 Telegram bot token）
> - `feishu` （飞书自定义机器人 webhook）
> - `wecom` （企微群机器人 webhook）
> - `dingtalk` （钉钉自定义机器人 webhook）

Slot filled: `chat_channel`.

## Q4 · 聊天频道 ID / webhook

> 上面那个频道的 chat ID 或 webhook URL：
> - Telegram → 您的 chat ID（一串数字，类似 `123456789`）
> - 飞书 / 企微 / 钉钉 → 群机器人的完整 webhook URL

Slot filled: `chat_channel_id`.

## Q5 · 客户运价文件位置

> 您的运价表 xlsx 和运价信息 docx 会从哪个本地路径取？默认是
> `~/.openclaw/workspace/shipping-rate-automation/raw/source-files/`，
> 我会建好这个目录，但您要自己往里放真实文件——AI 不替您填运价。

Slot filled: `raw_rate_dir`. Default to the path above unless operator overrides.

## Q6 · 业务员 / 审核人

> 推广审核、待审核开发信，要在企微/邮箱通知谁？给我对方的企微号或邮箱。

Slot filled: `reviewer_handle`. May be multiple — accept comma-separated list.

## Q7 · 每日 cron 时间

> 每日运价简报每天几点 Asia/Shanghai 自动跑？默认 08:00。

Slot filled: `cron_time`. Default `08:00`.

## Q8 · 确认 + 开始

**Mode A summary:**

> 总结一下：
> - 模式: **Mode A**（全新创建 — agent 自动建 2 个 doc）
> - 公司：{company_full_name} (slug: {company_slug})
> - 简报推送频道: {chat_channel} → {chat_channel_id}
> - 原始运价目录: {raw_rate_dir}
> - 审核人: {reviewer_handle}
> - Cron 时间: 每天 {cron_time} Asia/Shanghai
>
> 我会执行：
> 1. wecom-cli doc create_doc × 2（命名 "{公司} — Scenario 1 拓客" / "Scenario 2 运价推广"）
> 2. 给每个 doc 填好规范子表（共 7 张）和它们的列
> 3. 注册 OpenClaw 每日 cron（agent 直接调 `openclaw cron add`，message 用通用模板，不含任何公司数据）
>
> 确认就回复 "确认"，要改回 "改 X"。

**Mode B summary:**

> 总结一下：
> - 模式: **Mode B**（接入现有 workbench）
> - 公司：{company_full_name} (slug: {company_slug})
> - 拓客 workbench: {scenario_1_workbench_url}
> - 运价 workbench: {scenario_2_workbench_url}
> - 简报推送频道: {chat_channel} → {chat_channel_id}
> - 原始运价目录: {raw_rate_dir}
> - 审核人: {reviewer_handle}
> - Cron 时间: 每天 {cron_time} Asia/Shanghai
>
> 我会先 get_sheet + get_fields 拉您现有结构，跟规范对比，给您 diff 报告，逐项让您拍板怎么 reconcile（用现有的、改列名对齐、新加缺列、删多余列、新建标准子表、或保留 schema 漂移 + 写映射）。
>
> 确认无误回复 `确认` / `yes` / `开始`。需要改哪一项就告诉我。

Halt until operator confirms. Loop back to any specific question on "不对，改 X"。
