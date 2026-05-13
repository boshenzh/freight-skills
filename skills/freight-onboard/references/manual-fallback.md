# Manual fallback — when wecom-cli `smartsheet_create` is unavailable

If `wecom-cli doc smartsheet_create` returns "unknown subcommand" (older wecom-cli versions don't have it), fall back to a guided manual create flow.

Print this verbatim to the operator, freight-ops language. Wait for their DocID/sheet_id paste-backs.

---

## 业务员手动建 7 张表的步骤

打开您的企微 smartsheet workspace（URL：{wecom_workspace_url}）。点击 **新建 smartsheet**，按下面 7 张表的顺序一张一张建，每建一张就把它的 DocID 和 sheet_id 粘给我。

### 表 1 · 运价表（人）

新建一个 smartsheet，标题填「运价表（人）」。把它的 9 列依次设为：
- 区域 (文本)
- POD (文本)
- 船公司 (文本)
- 20GP (文本)
- 40GP (文本)
- 40HQ (文本)
- 有效期 (文本，允许多行)
- POL (文本)
- 超重费标准和其他费用 (文本，允许多行)

建好后，从浏览器地址栏复制 URL 给我，类似：
`https://doc.weixin.qq.com/smartsheet/s3_REDACTED-WORKBENCH...?scode=...`

我会从中解出 DocID 和 sheet_id。

### 表 2 · 运价信息（人）

7 列：入库日期 / 区域 / 段落标题 / 原文 / 来源 / 解析状态 / 备注。粘 URL 给我。

### 表 3 · 每日简报（AI）

5 列：日期 / 简报标题 / 推广审核状态 / 备注 / 更新时间。粘 URL 给我。

### 表 4 · 推广审核（AI+人）

8 列：推广标题 / 推广信息草稿 / 内部依据摘要 / 成本价检查 (checkbox) / 审核状态 / 目标客户/分组 / 人工指定发送渠道 / 更新时间。粘 URL 给我。

### 表 5 · 发送记录（AI）

9 列：发送时间 / 客户名 / 联系人 / 邮箱 / 航线/区域 / 邮件主题 / 发送状态 / 错误原因 / 回复状态。粘 URL 给我。

### 表 6 · 客户线索表

4 列：公司名 / 官网 / 联系人 / 来源渠道。粘 URL 给我。

⚠️ 这张表 AI 永远不写——业务员手填。

### 表 7 · 待审核开发信

15 列：客户名 / 官网 / 联系人 / 来源渠道 / 信息获取状态 / 主营业务摘要 / 市场定位 / 潜在需求分析 / 与我司业务匹配度 / 画像摘要 / 开发信草稿 / 审核状态 / 人工指定发送渠道 / 异常原因 / 更新时间。粘 URL 给我。

---

## 我（agent）拿到 7 个 URL 后做的事

从每个 URL 里解出：
- DocID：`s3_REDACTED-WORKBENCH...` 之间那一段（具体格式因企微版本而异——用 `wecom-cli doc info --url <url>` 验一下）
- sheet_id：URL 里 `&sheet_id=` 后面那段，或者打开 smartsheet 后从右上角"分享"对话框里读到的 sheet ID

把这 7 组 (DocID, sheet_id) 写进 `workspace/wecom/links.md` 按 wecom-sheet-schemas.md 的归类填好，然后继续 onboarding 的下一步（render cron）。

如果某个 URL 解析失败，停下来明确告诉业务员"表 X 的 URL 我没解析到 sheet_id，能不能从分享对话框里手动粘一下 sheet_id？"，不要试错猜。
