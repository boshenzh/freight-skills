# Manual fallback — when wecom-cli is unavailable or rejects calls

`wecom-cli`'s `smartsheet_add_sheet` + `smartsheet_add_fields` APIs are required by both Mode A and Mode B. If for any reason wecom-cli is unavailable on the VPS (not installed, auth expired, network blocked), the agent falls back to guided manual instructions.

Below assume **all wecom-cli writes are blocked**. If only some writes fail (e.g. auth works but `smartsheet_delete_sheet` is forbidden), do the parts that work via CLI and use this fallback only for the blocked parts.

## Manual flow — Mode A (fresh new company)

Tell the operator:

---

> 自动建表失败（wecom-cli 写入受阻）。下面是手工建 7 张子表的步骤——业务员在企微 UI 操作，每建好一张回来粘 sheet_id 给我。
>
> 在场景 1 doc（DocID `{scenario_1_docid}`）里建 2 张子表：
>
> ### 子表 1 · 客户线索表
> 1. 打开 doc，点 "新建子表"，标题填 `客户线索表`
> 2. 加 4 列（都是"文本"类型）：公司名 / 官网 / 联系人 / 来源渠道
> 3. 浏览器地址栏里的 `sheet_id=xxxxxx` 部分粘给我
>
> ### 子表 2 · 待审核开发信
> 1. 同上，标题 `待审核开发信`
> 2. 加 15 列（全文本）：客户名 / 官网 / 联系人 / 来源渠道 / 信息获取状态 / 主营业务摘要 / 市场定位 / 潜在需求分析 / 与我司业务匹配度 / 画像摘要 / 开发信草稿 / 审核状态 / 人工指定发送渠道 / 异常原因 / 更新时间
> 3. 粘 sheet_id 给我
>
> 在场景 2 doc（DocID `{scenario_2_docid}`）里建 5 张子表：
>
> ### 子表 3 · 运价表（人）
> 9 列（都是文本）：区域 / POD / 船公司 / 20GP / 40GP / 40HQ / 有效期 / POL / 超重费标准和其他费用
> 粘 sheet_id 给我。
>
> ### 子表 4 · 运价信息（人）
> 7 列（都是文本）：入库日期 / 区域 / 段落标题 / 原文 / 来源 / 解析状态 / 备注
> 粘 sheet_id 给我。
>
> ### 子表 5 · 每日简报（AI）
> 5 列（都是文本）：日期 / 简报标题 / 推广审核状态 / 备注 / 更新时间
> 粘 sheet_id 给我。
>
> ### 子表 6 · 推广审核（AI+人）
> 8 列：推广标题（文本）/ 推广信息草稿（文本）/ 内部依据摘要（文本）/ **成本价检查（勾选）** / 审核状态（文本）/ 目标客户/分组（文本）/ 人工指定发送渠道（文本）/ 更新时间（文本）
> 粘 sheet_id 给我。
>
> ⚠️ 这张表有一个**勾选**类型的列（"成本价检查"），其他都是文本——不要忘了。
>
> ### 子表 7 · 发送记录（AI）
> 9 列（都是文本）：发送时间 / 客户名 / 联系人 / 邮箱 / 航线/区域 / 邮件主题 / 发送状态 / 错误原因 / 回复状态
> 粘 sheet_id 给我。

---

收齐 7 个 sheet_id 之后，agent 像 Mode A 自动流程的后半段一样写 workspace/wecom/links.md + 渲染 cron。

## Manual flow — Mode B (adopt existing)

Mode B 本身大量需要 `smartsheet_get_sheet` + `smartsheet_get_fields` 只读调用。如果连只读也不通，建议**直接放弃 Mode B**——没有 CLI 看不到现有 schema，agent 没法推理 diff。让业务员去企微 UI 自己对照 `wecom-sheet-schemas.md` 看差异，然后选择：
- 手动把现有表改成符合规范（业务员自己加列、改列名）→ 之后跑一次 Mode A 走"创建"流程，只是 doc 已经有现成子表（agent 会重复 add_sheet 失败但 add_fields 可能成功——需要操作员手工把现有 sheet_id 粘给 agent，跳过 add_sheet 步骤）
- 接受 schema 漂移 → 写 column-name mapping 进 links.md（见 `column-mapping-fallback.md`）

## 后果

手工模式的代价：
- **慢**——7 张子表手建大约 10-15 分钟
- **易错**——列名打错、漏列、列类型选错（勾选 vs 文本）都会在操作员第一次跑 cron 时 silently 出现行为不一致
- **不可重复**——一旦建错没法 idempotently 回滚

所以这是**绝对兜底**，先排查为什么 wecom-cli 写入失败：
1. `wecom-cli --version` 有响应吗？没有 → 没装 / PATH 不对
2. `wecom-cli doc smartsheet_get_sheet '{"docid":"<known-docid>"}'` 返回什么？401 → 没鉴权登录；500 → 服务端问题；具体业务码（如 41011）→ 查企微开发文档
3. 鉴权可以走 `wecom-cli login` 流程（如果有），或者按 wecom-cli 的官方鉴权方式（cookie/token/secret）补齐凭据
