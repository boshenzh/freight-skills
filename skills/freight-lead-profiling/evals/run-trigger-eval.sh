#!/usr/bin/env bash
# Trigger-rate eval for freight-lead-profiling skill.
#
# Per https://agentskills.io/skill-creation/optimizing-descriptions
#
# For each query in trigger_queries.json: run it through `claude -p` 3 times,
# count how many runs invoked the skill, compute trigger_rate. A query passes
# when trigger_rate matches its `should_trigger` label (>0.5 for true, <=0.5
# for false).
#
# Total cost: 20 queries × 3 runs = 60 `claude -p` invocations.
#
# Prereqs:
#   - `claude` CLI on PATH (Claude Code CLI, not the Claude API)
#   - The freight-lead-profiling skill discoverable by `claude` — either via
#     openclaw plugins install (VPS) or ~/.claude/skills/freight-lead-profiling
#     (local mac).
#   - jq.

set -euo pipefail

SKILL_NAME="freight-lead-profiling"
QUERIES_FILE="$(dirname "${BASH_SOURCE[0]}")/trigger_queries.json"
RUNS=3
THRESHOLD=0.5

# Detect a Skill tool_use call for our skill name in the JSON output.
check_triggered() {
  local query="$1"
  claude -p "$query" --output-format json 2>/dev/null \
    | jq -e --arg skill "$SKILL_NAME" \
        'any(.messages[].content[]; .type == "tool_use" and .name == "Skill" and .input.skill == $skill)' \
        > /dev/null 2>&1
}

count=$(jq length "$QUERIES_FILE")
pass=0
fail=0
results=()

for i in $(seq 0 $((count - 1))); do
  query=$(jq -r ".[$i].query" "$QUERIES_FILE")
  should_trigger=$(jq -r ".[$i].should_trigger" "$QUERIES_FILE")
  triggers=0

  for run in $(seq 1 $RUNS); do
    check_triggered "$query" && triggers=$((triggers + 1)) || true
  done

  rate=$(awk -v t="$triggers" -v r="$RUNS" 'BEGIN{printf "%.2f", t/r}')

  if [ "$should_trigger" = "true" ]; then
    if awk -v r="$rate" -v t="$THRESHOLD" 'BEGIN{exit !(r > t)}'; then
      verdict="PASS"; pass=$((pass+1))
    else
      verdict="FAIL"; fail=$((fail+1))
    fi
  else
    if awk -v r="$rate" -v t="$THRESHOLD" 'BEGIN{exit !(r <= t)}'; then
      verdict="PASS"; pass=$((pass+1))
    else
      verdict="FAIL"; fail=$((fail+1))
    fi
  fi

  result=$(jq -n \
    --arg query "$query" \
    --argjson should_trigger "$should_trigger" \
    --argjson triggers "$triggers" \
    --argjson runs "$RUNS" \
    --arg rate "$rate" \
    --arg verdict "$verdict" \
    '{query: $query, should_trigger: $should_trigger, triggers: $triggers, runs: $runs, trigger_rate: ($rate | tonumber), verdict: $verdict}')
  results+=("$result")
  echo "[$verdict] rate=$rate  expected=$should_trigger  $query" >&2
done

printf '%s\n' "${results[@]}" | jq -s --arg pass "$pass" --arg fail "$fail" --argjson total "$count" \
  '{summary: {pass: ($pass|tonumber), fail: ($fail|tonumber), total: $total}, results: .}'
