# freight-rate-daily-promotion evals

Test scaffold following [agentskills.io best practices](https://agentskills.io/skill-creation/).

## What's here

```
evals/
├── README.md                       ← you are here
├── trigger_queries.json            ← 20 labeled queries for description-trigger eval
├── run-trigger-eval.sh             ← run 20 queries × 3 = 60 claude -p calls
├── evals.json                      ← 3 output-quality test cases with assertions
├── files/                          ← synthetic input fixtures (JSON stand-ins for xlsx/docx)
│   ├── rate-table-happy.json       (mock 运价表 9GjUyn)
│   ├── rate-info-happy.json        (mock 运价信息 SepMHU, normal section)
│   └── rate-info-cost-section.json (mock 运价信息 with explicit 成本价 marker)
└── run-quality-eval.sh             ← scaffold for output-quality eval
```

## Caveats specific to this skill

- **Live integrations**: this skill calls `wecom-cli` (writes to WeCom workspace) and triggers chat-channel delivery via OpenClaw cron (current channel: Telegram per `cron.delivery.channel`; can be switched to 飞书/企微/钉钉). Running the output-quality eval against the live workspace would pollute production. Before running output evals, EITHER stub wecom-cli + OpenClaw delivery, OR point them at a test workbench + test chat ID.
- **Synthetic fixtures**: `files/*.json` are JSON stand-ins, not real .xlsx/.docx. The harness needs to either read these directly OR generate matching xlsx/docx on the fly. Real-format fixtures aren't committed because they'd contain customer pricing.

## How to run

### Trigger eval (safe — read-only)

```bash
chmod +x run-trigger-eval.sh
./run-trigger-eval.sh > trigger-results.json 2>&1
jq '.summary' trigger-results.json
```

Cost: 60 `claude -p` invocations. Read [optimizing-descriptions](https://agentskills.io/skill-creation/optimizing-descriptions) for iteration guidance.

### Output-quality eval (requires sandbox setup)

`run-quality-eval.sh` is a scaffold. Implementation steps:

1. **Sandbox wecom-cli** — wrap or stub so writes go to a test workbench, not the live one.
2. **Sandbox chat-channel delivery** — change `cron.delivery.to` to a test chat ID for the duration of the eval (whatever channel `cron.delivery.channel` uses — Telegram / 飞书 / 企微 / 钉钉).
3. **Implement `run_agent()`** — see sister script in `freight-lead-profiling/evals/`.
4. **Implement `grade()`** — LLM-judge over assertions + outputs.

## Assertion priorities

For this skill, the highest-stakes assertions are the **cost-price-leak** ones (test case `cost-price-leak-block` in `evals.json`). A failure there means real-world margin leak. If you run with limited budget, prioritize that test case.

## Iteration log

| Date | Iteration | Trigger pass rate | Output pass rate (with/without delta) | Notes |
|---|---|---|---|---|
| _yet to run_ | — | — | — | — |
