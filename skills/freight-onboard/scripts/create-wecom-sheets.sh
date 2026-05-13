#!/usr/bin/env bash
# create-wecom-sheets.sh — populate two operator-provided empty WeCom
# smartsheet docs with the 7 canonical sub-sheets that the freight skills
# expect. Driven by sheet-definitions.json (sibling file).
#
# Background:
#   wecom-cli has NO API for creating a smartsheet doc itself. The
#   operator must manually create 2 empty smartsheet docs in WeCom UI
#   (one per scenario) and provide their DocIDs. This script then uses:
#     - smartsheet_add_sheet   to add canonical sub-sheets to each doc
#     - smartsheet_add_fields  to add columns to each sub-sheet
#   per https://github.com/WecomTeam/wecom-cli/blob/main/skills/wecomcli-smartsheet/SKILL.md
#
# Each freshly-created doc starts with 1 default sub-sheet. This script
# does NOT touch the default — operator can delete it manually after.
#
# Usage:
#   create-wecom-sheets.sh <scenario_1_docid> <scenario_2_docid> <out-json>
#
# Output (stdout):
#   {
#     "ok": true,
#     "scenarios": {
#       "1": {"docid":"...", "sheets":[{"title":"客户线索表","sheet_id":"..."}, ...]},
#       "2": {"docid":"...", "sheets":[...]}
#     },
#     "errors": []
#   }
#
# Errors are non-fatal — script continues to next sheet on failure so
# partial progress is recoverable.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFS="$SCRIPT_DIR/sheet-definitions.json"

S1_DOCID="${1:-}"
S2_DOCID="${2:-}"
OUT="${3:-}"

if [ -z "$S1_DOCID" ] || [ -z "$S2_DOCID" ] || [ -z "$OUT" ]; then
  echo "Usage: $0 <scenario_1_docid> <scenario_2_docid> <out-json>" >&2
  exit 2
fi

if ! command -v wecom-cli >/dev/null 2>&1; then
  echo '{"ok": false, "reason": "wecom-cli not on PATH"}' | tee "$OUT"
  exit 1
fi

if ! [ -f "$DEFS" ]; then
  echo '{"ok": false, "reason": "sheet-definitions.json not found alongside script"}' | tee "$OUT"
  exit 1
fi

err_count=0
err_log=()

declare -A docids=( [1]="$S1_DOCID" [2]="$S2_DOCID" )

result='{"ok": true, "scenarios": {}, "errors": []}'

for scenario in 1 2; do
  docid="${docids[$scenario]}"
  scenario_block='{"docid":"'"$docid"'","sheets":[]}'

  sheet_count=$(jq ".scenarios[\"$scenario\"].sheets | length" "$DEFS")
  for i in $(seq 0 $((sheet_count - 1))); do
    title=$(jq -r ".scenarios[\"$scenario\"].sheets[$i].title" "$DEFS")
    fields_json=$(jq -c ".scenarios[\"$scenario\"].sheets[$i].fields" "$DEFS")

    # Step A — create the sub-sheet
    add_sheet_payload=$(jq -nc --arg docid "$docid" --arg title "$title" \
      '{docid: $docid, properties: {title: $title}}')

    sheet_resp=$(wecom-cli doc smartsheet_add_sheet "$add_sheet_payload" 2>&1) || sheet_resp="__ERROR__"

    if [ "$sheet_resp" = "__ERROR__" ] || ! echo "$sheet_resp" | jq -e '.errcode == 0' >/dev/null 2>&1; then
      err_count=$((err_count + 1))
      err_log+=("scenario=$scenario title=$title add_sheet failed: $sheet_resp")
      continue
    fi

    sheet_id=$(echo "$sheet_resp" | jq -r '.sheet_id // .properties.sheet_id // empty')
    if [ -z "$sheet_id" ]; then
      err_count=$((err_count + 1))
      err_log+=("scenario=$scenario title=$title add_sheet returned no sheet_id: $sheet_resp")
      continue
    fi

    # Step B — add fields to the new sub-sheet
    add_fields_payload=$(jq -nc --arg docid "$docid" --arg sheet_id "$sheet_id" --argjson fields "$fields_json" \
      '{docid: $docid, sheet_id: $sheet_id, fields: $fields}')

    fields_resp=$(wecom-cli doc smartsheet_add_fields "$add_fields_payload" 2>&1) || fields_resp="__ERROR__"

    if [ "$fields_resp" = "__ERROR__" ] || ! echo "$fields_resp" | jq -e '.errcode == 0' >/dev/null 2>&1; then
      err_count=$((err_count + 1))
      err_log+=("scenario=$scenario title=$title sheet_id=$sheet_id add_fields failed: $fields_resp")
    fi

    scenario_block=$(echo "$scenario_block" | jq --arg title "$title" --arg sheet_id "$sheet_id" \
      '.sheets += [{"title": $title, "sheet_id": $sheet_id}]')

    echo "[ok] scenario=$scenario  $title  sheet_id=$sheet_id" >&2
  done

  result=$(echo "$result" | jq --arg s "$scenario" --argjson block "$scenario_block" \
    '.scenarios[$s] = $block')
done

if [ "$err_count" -gt 0 ]; then
  for e in "${err_log[@]}"; do
    result=$(echo "$result" | jq --arg msg "$e" '.errors += [$msg]')
  done
  result=$(echo "$result" | jq '.ok = false')
fi

echo "$result" | jq '.' | tee "$OUT"
[ "$err_count" -eq 0 ]
