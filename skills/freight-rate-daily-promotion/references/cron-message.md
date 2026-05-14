你正在执行「场景2 每日运价整理 + 推广」的每日定时任务。

按 **freight-rate-daily-promotion** skill 的完整流程执行。所有 WeCom DocID / sheet_id 在运行时从 `~/.openclaw/workspace/shipping-rate-automation/wecom/links.md` 解析 —— 绝不硬编码。

关键硬约束（细节以 skill 为准）：
- 先做空态检查：若 `raw/source-files/` 没有 `运价表*.xlsx` / `运价信息*.docx`，POST 一条「今日无运价数据上传，简报跳过」到聊天频道后正常退出，不要 silent abort。
- 成本价 / 底价 / 采购价 / 拿价 / cost / net / 内部 / 利润 绝不进客户推广信息。
- 推广草稿只写「推广审核」表，状态 `待审核` 或 `需补充信息`；绝不直接发客户邮件。
- 简报以 plain text 直接贴到聊天频道正文，不发 `.txt` 附件、不发 PDF、不用 `MEDIA:`。
- SCFI 拉取 + 船期/CLS 校验每次必须尝试，失败 fail-soft 并写 run-status.md。
- 「每日简报」表只写 5 列 index，简报正文不进表。

最终回复：
1. 直接贴完整简报正文（无数据时贴跳过提示）。
2. 之后用很短几行说明：简报记录 ID、推广审核记录 ID、数量摘要、推广审核状态、明确「客户邮件：未发送」。
