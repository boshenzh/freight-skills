# Manual fallback — when wecom-cli is unreachable

`scripts/create-wecom-sheets.py` does the entire Mode A provision via `wecom-cli doc create_doc` + `smartsheet_*` chain. If `wecom-cli` is unavailable for any reason (not installed, OAuth expired, network blocked, API down), fall back to guided manual instructions.

This page replaces the previous (v0.1) "manual create" flow which assumed `wecom-cli` had no `create_doc` API. That assumption was wrong — see Gotchas in `SKILL.md`.

## Diagnose first — don't go manual on a soft failure

When `create-wecom-sheets.py` raises:

1. **`wecom-cli not on PATH`** → install:
   ```bash
   npm install -g @wecom/cli
   wecom-cli init     # interactive auth setup
   ```
2. **`returned exit N` / non-JSON stdout** → run the failing call by hand to see the real error:
   ```bash
   wecom-cli doc create_doc --json '{"doc_type":10,"doc_name":"diagnostic"}'
   ```
   If this returns an authentication error (`errcode` 40001 / 40014 / 41001 etc.), re-run `wecom-cli init` to refresh credentials.
3. **`errcode=N errmsg=...`** → the call reached the WeCom backend but it rejected. Look the errcode up in WeCom's official docs. Common ones:
   - `48002` — API forbidden for this corp/agent → check IP allowlist or agent permissions
   - `60011` — no permission on this doc/space → operator's account doesn't have create rights in the chosen space
   - `48004` — API rate limit → wait and retry

Most "manual fallback" requests in practice are item 1 or item 2 — fixable, not requiring true manual.

## True manual fallback (only when `wecom-cli` truly cannot be made to work)

Tell the operator:

---

> 自动建表暂时不可用（wecom-cli 写入受阻）。下面是手工建 2 个 doc + 7 张子表的步骤。每建好一张子表，把 sheet_id 粘给我。
>
> ## Step 1 · 在企微 UI 建 2 个空 smartsheet doc
>
> 1. 打开企微 → 文档 → 新建 → 智能表格
> 2. 标题填 `{公司名} — 拓客`，保存
> 3. 浏览器地址栏 URL 粘给我（`https://doc.weixin.qq.com/smartsheet/s3_...?scode=...`）
> 4. 再建一个，标题填 `{公司名} — 运价推广`，URL 也给我
>
> ## Step 2 · 在拓客 doc 里建 2 张子表
>
> 默认子表（页面打开就在）：
> - 右键标题 → 重命名为 `客户线索表`
> - 默认列 `文本` → 重命名为 `公司名`
> - 加 3 列（都"文本"类型）：`官网` / `联系人` / `来源渠道`
>
> 添加第 2 张子表：
> - 标签栏点 `+` → 新建子表 → 标题 `待审核开发信`
> - 默认列 `智能表列` → 重命名为 `客户名`
> - 加 14 列（都"文本"类型）：`官网` / `联系人` / `来源渠道` / `信息获取状态` / `主营业务摘要` / `市场定位` / `潜在需求分析` / `与我司业务匹配度` / `画像摘要` / `开发信草稿` / `审核状态` / `人工指定发送渠道` / `异常原因` / `更新时间`
>
> 把 2 张子表的 sheet_id 粘给我（在企微 UI 的"子表设置"或"分享"对话框里能看到）。
>
> ## Step 3 · 在运价推广 doc 里建 5 张子表
>
> 默认子表：
> - 重命名为 `运价表（人）`
> - 默认列 `文本` → 重命名为 `区域`
> - 加 8 列（都"文本"）：`POD` / `船公司` / `20GP` / `40GP` / `40HQ` / `有效期` / `POL` / `超重费标准和其他费用`
>
> 加 4 张子表（每张参考 `wecom-sheet-schemas.md`）：
> - `运价信息（人）` — 7 列（首列重命名 + 加 6 列）
> - `每日简报（AI）` — 5 列
> - `推广审核（AI+人）` — 8 列（注意：`成本价检查` 是"勾选"类型，不是"文本"）
> - `发送记录（AI）` — 9 列
>
> 全部建好把每张 sheet_id 粘给我。

---

收齐 7 个 sheet_id 之后，agent 像 Mode A 自动流程的后半段一样写 `workspace/wecom/links.md` + 渲染 cron。

## Manual fallback for Mode B (adopt existing)

Mode B 本身大量需要 `smartsheet_get_sheet` + `smartsheet_get_fields` 只读调用。如果连只读也不通：

- **建议直接放弃 Mode B**——没有 CLI agent 推理不出现有 schema
- 让业务员去企微 UI 自己对照 `wecom-sheet-schemas.md` 看差异，决定要么 (a) 手工把现有表改成规范，再跑 Mode A（跳过 create_doc，传现有 docid）；要么 (b) 写 column-name mapping 进 links.md（见 `column-mapping-fallback.md`）

## 后果

手工模式的代价：
- **慢**——7 张子表手建大约 15-20 分钟
- **易错**——列名打错、漏列、列类型选错（勾选 vs 文本）会在第一次 cron 时 silently 出现行为不一致
- **不可重复**——一旦建错没法 idempotently 回滚，要么继续手工修要么删 doc 重来

所以这是**绝对兜底**。优先排查 wecom-cli 的鉴权/网络问题，不要默认走手工。
