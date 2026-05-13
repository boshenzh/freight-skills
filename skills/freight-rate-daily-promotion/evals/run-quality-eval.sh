#!/usr/bin/env bash
# Output-quality eval for freight-rate-daily-promotion.
# See sister script in freight-lead-profiling/evals/run-quality-eval.sh
# for the common pattern documentation.
#
# This skill needs additional setup vs freight-lead-profiling:
# 1. WeCom mocks — the skill calls `wecom-cli doc smartsheet_*`.
#    For sandbox runs, intercept wecom-cli or stub the WeCom API so the
#    eval doesn't touch the live workspace (you'd corrupt production data).
# 2. SCFI / schedule-pp-cli — let them run live (they're read-only) OR
#    mock to test fail-soft branches.
# 3. Chat channel — point cron.delivery.to at a test chat (Telegram /
#    飞书 / 企微 / 钉钉 — whichever channel cron.delivery.channel uses)
#    for the duration of the eval, or stub the openclaw delivery layer.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILL_NAME="freight-rate-daily-promotion"

WORKSPACE="${WORKSPACE:-${SKILL_DIR%/skills/*}/${SKILL_NAME}-workspace}"
ITERATION="${ITERATION:-iteration-$(date +%Y%m%d-%H%M%S)}"
ROOT="$WORKSPACE/$ITERATION"
mkdir -p "$ROOT"

EVALS="$SCRIPT_DIR/evals.json"
count=$(jq '.evals | length' "$EVALS")

echo "==> Output-quality eval for $SKILL_NAME"
echo "    ⚠️  This skill writes to live WeCom and Telegram. Make sure you've"
echo "        stubbed wecom-cli and pointed Telegram delivery at a test chat"
echo "        BEFORE running this eval."
echo "    workspace: $ROOT"
echo "    test cases: $count × 2 configs = $((count * 2)) agent runs"
echo

# Implement run_agent + grade per the freight-lead-profiling sister script.
# Keep separate harness state between with_skill and without_skill runs so
# the without_skill baseline doesn't inadvertently consult cached SKILL.md.

echo "Not yet implemented — fill in run_agent + grade for your harness."
exit 1
