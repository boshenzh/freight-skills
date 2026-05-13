#!/usr/bin/env bash
# Output-quality eval for freight-lead-profiling.
#
# Per https://agentskills.io/skill-creation/evaluating-skills
#
# For each test case in evals.json: spawn TWO subagent runs — one with the
# skill loaded, one without — capture outputs into workspace dirs, then
# grade each assertion using an LLM judge.
#
# Workspace layout:
#   ../freight-lead-profiling-workspace/iteration-N/
#     ├── eval-<id>/
#     │   ├── with_skill/{outputs/, timing.json, grading.json}
#     │   └── without_skill/{outputs/, timing.json, grading.json}
#     └── benchmark.json
#
# Total cost (3 test cases × 2 configs = 6 agent runs per iteration).
#
# Prereqs:
#   - `claude` CLI on PATH with subagent support
#   - skill discoverable in the with-skill run (~/.claude/skills/ or
#     openclaw-installed)
#   - jq, awk

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILL_NAME="freight-lead-profiling"

WORKSPACE="${WORKSPACE:-${SKILL_DIR%/skills/*}/${SKILL_NAME}-workspace}"
ITERATION="${ITERATION:-iteration-$(date +%Y%m%d-%H%M%S)}"
ROOT="$WORKSPACE/$ITERATION"
mkdir -p "$ROOT"

EVALS="$SCRIPT_DIR/evals.json"
count=$(jq '.evals | length' "$EVALS")

echo "==> Output-quality eval for $SKILL_NAME"
echo "    workspace: $ROOT"
echo "    test cases: $count × 2 configs = $((count * 2)) agent runs"
echo

# --------------------------------------------------------------------
# REPLACE the run_agent function with your actual subagent spawn logic.
# The function should:
#   - Spawn a fresh subagent with the given prompt
#   - For "with_skill": ensure the skill is loaded (skills dir / plugin)
#   - For "without_skill": ensure the skill is NOT loaded
#   - Provide the input files listed in evals.json under `files`
#   - Write outputs to $out_dir/outputs/
#   - Write {total_tokens, duration_ms} to $out_dir/timing.json
# --------------------------------------------------------------------
run_agent() {
  local config="$1"  # "with_skill" | "without_skill"
  local out_dir="$2"
  local prompt="$3"
  shift 3
  local files=("$@")

  mkdir -p "$out_dir/outputs"

  echo "  [$config] spawning: $prompt" >&2

  # PLACEHOLDER — real implementation depends on harness.
  # Example with claude CLI subagent:
  #   claude --skill-dir "$([ "$config" = "with_skill" ] && echo "$SKILL_DIR")" \
  #          -p "$prompt" \
  #          --files "${files[@]}" \
  #          --output-dir "$out_dir/outputs/" \
  #          --output-format json > "$out_dir/run.json"
  # Then extract token + duration into timing.json.
  echo '{"total_tokens": 0, "duration_ms": 0, "_placeholder": "implement run_agent for your harness"}' > "$out_dir/timing.json"
}

# --------------------------------------------------------------------
# REPLACE grade with an LLM call that takes (assertions, output_dir) and
# returns grading.json per the agentskills.io schema.
# --------------------------------------------------------------------
grade() {
  local out_dir="$1"
  local assertions="$2"  # JSON array of assertion strings

  echo '{"assertion_results": [], "summary": {"passed": 0, "failed": 0, "total": 0, "pass_rate": 0}, "_placeholder": "implement grade()"}' > "$out_dir/grading.json"
}

# Main loop
for i in $(seq 0 $((count - 1))); do
  eval_id=$(jq -r ".evals[$i].id" "$EVALS")
  prompt=$(jq -r ".evals[$i].prompt" "$EVALS")
  assertions=$(jq -c ".evals[$i].assertions" "$EVALS")
  mapfile -t files < <(jq -r ".evals[$i].files[]? // empty" "$EVALS")
  eval_root="$ROOT/eval-$eval_id"
  echo "▸ $eval_id"

  for config in with_skill without_skill; do
    out_dir="$eval_root/$config"
    mkdir -p "$out_dir"
    run_agent "$config" "$out_dir" "$prompt" "${files[@]}"
    grade "$out_dir" "$assertions"
  done
done

# Aggregate (placeholder — implement by reading all grading.json files)
echo '{"_placeholder": "compute pass_rate / tokens / duration mean+stddev across with_skill vs without_skill and write delta"}' > "$ROOT/benchmark.json"
echo
echo "==> Done. Review:"
echo "    $ROOT/benchmark.json"
echo "    $ROOT/eval-*/(with|without)_skill/grading.json"
