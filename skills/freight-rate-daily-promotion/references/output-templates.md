# Output Templates / 输出模板

## Internal daily brief（业务员看的内部简报）

Default style follows `daily-rate-brief-source.md`: **按船司 + 区域分块**（禁止按 POD 分块），紧凑、决策导向、保留运营深度字段。

```markdown
# 每日运价简报 - {date}

## 市场对照（SCFI {week}）
SCFI 综合指数 {value}（前值 {prev}，WoW {pct}%）— {一句解读}

## 总览
- 事实源读取：{total} 条（卖价 {sell} / 成本价 {cost} / 未分类 {unknown}）
- 可推广（清洗后）：{ready} 条
- 拦截合计：{blocked} 条（数值异常 {anomaly} + 成本价 {cost} + 未分类 {unknown}）

## 今日可推 Top 5（按 20GP 由低到高，仅取直航 / 卖价已确认）
1. {POL}-{POD} {carrier} USD{20GP}/{40GP} CLS{date} {直航/中转}
2. ...

## 主体 — 按船司 + 区域分块（结构硬约束）

{carrier1}{区域}
{POL}-{POD1} USD{20GP}/{40GP} {可选：中转N天}
{POL}-{POD2} USD{20GP}/{40GP}
...
{POL}-{POD-x} 实单单询 {中转港}
CLS {POL} {date} {船名} {航次号} {操作变更，如：原船 X omit SHK，Y 替代收货}
{附加费/限重：如 AQJ 已含 EIS USD100/200}

-------------------------

{carrier2}{区域}（中转/直航/其他特殊属性）
...

-------------------------

...

## 风险拦截
- 成本价：{cost_count} 条 — 仅内部，不外发。
- 未分类：{unknown_count} 条 — 需业务在事实源补字段。
- 数值异常 / 字段错位：{items}
- 过期/疑似过期船期（CLS）：{items}（含 schedule-pp-cli next-cls 给的下一航次）

## 待业务确认
- {question 1}
- {question 2}
```

**关键约束**：
- 主体**禁止**按 POD 分块。
- 主体**必须**按船司+区域分块。
- 每块**必须**保留：船名+航次号、中转天数、免柜期、附加费、操作变更/跳港、限重（事实源里有的不能丢）。
- POL 用紧凑缩写（SK / NS / DCB / YT），不写 "SK蛇口"。
- 单询占位不拦截（写 "实单单询 JIB" 保留行）。
- 块之间用 `-------------------------` 分隔。

---

## Customer-safe promotion（客户外发版）

Default style follows `promotion-template-source.md`: 紧凑、单港单行、不带船名 / 成本 / 内部信息。

```markdown
{航线/区域}近期优势参考（更新：{YYYY-MM-DD}）

{POL}-{POD1} USD{20GP}/{40GP} CLS{截关日期} {直航/中转}
{POL}-{POD2} USD{20GP}/{40GP} CLS{截关日期} {直航/中转}
{POL}-{POD3} 实单单询 {中转港}

以上均为直航/中转服务，价格已含已确认基础附加费，具体以订舱确认为准。
欢迎询价订舱，更多船期及中转方案请随时联系！
```

**规则**：
- 同 POD 多船司只取最优一条（最低 20GP，或客户偏好直航优先）。
- 不带船名/航次号。
- 不带成本价/底价/采购价/利润/内部备注。
- 仅在客户关键场景保留附加费提示（如 NSA 含 CIC USD150/300）。
- 单询占位保留。

---

## Review message to salesperson（Telegram 通知给 Boshen 的格式）

```text
✅ 场景2 每日运价整理 + 推广（{YYYY-MM-DD} {HH:mm} 触发）已完成

📊 数据快照
- 事实源 {total} 条 → 卖价 {sell} / 成本价 {cost} / 未分类 {unknown}
- 可推广 {ready} 条；拦截 {blocked}
- SCFI 综合 {value} ({wow}% WoW) — {解读一句}
- CLS 校验：{schedule_routes} 条航线 ETD 在 {date_range}

🚀 今日可推 Top 5
1. {POL}-{POD} {carrier} USD{20GP}/{40GP} CLS{date}
... (5 条)

📝 推广审核（待业务侧确认）
- record_id: {row_id}
- 状态：待审核
- 草稿覆盖 {pod_count} 个 POD
- 目标客户/分组：留空待业务指定

❓ 需要人工确认
1. {question 1}
2. {question 2}

🔒 安全声明
未发送任何客户邮件。仅在审核状态被人工改为「通过」并明确要求发送时，才会进入下一步。

📂 本地 run 文件夹：{path}
```
