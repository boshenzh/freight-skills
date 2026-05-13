# Onboarding intake questions — conversational order

Ask one at a time. Use freight-ops Chinese, not engineering English. Validate each answer before moving on. Acknowledge each answer (e.g. "OK，公司叫东方联动，下一步问您...").

## Q1 · 公司名

> 这是新装机的第一步——先确认您公司的中文全称（例如「东方联动国际货运代理有限公司」）和英文/拼音简称（例如 orientlinkage，会用在仓库名和路径里）。

Slots filled: `company_full_name`, `company_slug`.

## Q2 · 企微 workspace URL

> 请把您公司的企微 smartsheet workspace URL 给我（应该长这样：https://doc.weixin.qq.com/smartsheet/...）。我会在里面新建 7 张表，不动您已有的。

Slot filled: `wecom_workspace_url`. Validate: can the wecom-cli auth see this workspace?

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
> - 飞书/企微/钉钉 → 群机器人的完整 webhook URL

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

## Q8 · 准备好建表了吗

> 总结一下您给的信息：
> - 公司：{company_full_name} (slug: {company_slug})
> - WeCom workspace: {wecom_workspace_url}
> - 简报推送频道: {chat_channel} → {chat_channel_id}
> - 原始运价目录: {raw_rate_dir}
> - 审核人: {reviewer_handle}
> - Cron 时间: 每天 {cron_time} Asia/Shanghai
>
> 确认无误，我现在开始建 7 张企微表 + 写配置 + 注册 cron。回复 `确认` 或者 `不对，改 X`。

Halt until operator says 确认 (or English "yes" / "confirm"). On any "不对" or "改", loop back to the relevant question.
