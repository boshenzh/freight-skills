# freight-lead-profiling evals

Test scaffold following [agentskills.io best practices](https://agentskills.io/skill-creation/).

## What's here

```
evals/
├── README.md                   ← you are here
├── trigger_queries.json        ← 20 labeled queries for description-trigger eval
├── run-trigger-eval.sh         ← run 20 queries × 3 = 60 claude -p calls, report trigger rate
├── evals.json                  ← 3 output-quality test cases with assertions
├── files/                      ← input fixtures referenced by evals.json
│   ├── leads-with-website.csv
│   ├── leads-without-website.csv
│   └── leads-non-fit.csv
└── run-quality-eval.sh         ← scaffold for output-quality eval (with-skill vs baseline)
```

## How to run

### Trigger eval (cheap, fast)

```bash
chmod +x run-trigger-eval.sh
./run-trigger-eval.sh > trigger-results.json 2>&1
jq '.summary' trigger-results.json
```

Cost: 60 `claude -p` invocations. Expect a few minutes wall-time depending on model speed.

Pass criteria: `should_trigger=true` queries should fire the skill in >50% of runs; `should_trigger=false` queries in ≤50%.

Read [agentskills.io optimizing-descriptions](https://agentskills.io/skill-creation/optimizing-descriptions) for how to iterate the description when trigger rates miss.

### Output-quality eval (more setup)

```bash
chmod +x run-quality-eval.sh
./run-quality-eval.sh   # placeholder — fill in run_agent + grade for your harness
```

The current `run-quality-eval.sh` is a **scaffold**, not runnable as-is. You need to fill in:

1. `run_agent()` — spawn a subagent with the prompt + input files, write outputs to `outputs/`, capture `timing.json`. Implementation varies by harness (Claude Code subagent, Anthropic batch API, etc.).
2. `grade()` — call an LLM judge with the assertions + outputs, write `grading.json` with PASS/FAIL + evidence per [agentskills.io evaluating-skills](https://agentskills.io/skill-creation/evaluating-skills).
3. Aggregate `benchmark.json` from all `grading.json` files (mean pass_rate, tokens, duration; delta with-skill vs without).

## Iteration log

When you run an eval, save the run dir into `../<skill>-workspace/iteration-N/` (NOT under git — they accumulate fast). Document material learnings in this README.

| Date | Iteration | Trigger pass rate | Output pass rate (with/without delta) | Notes |
|---|---|---|---|---|
| _yet to run_ | — | — | — | — |
