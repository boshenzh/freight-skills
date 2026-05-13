#!/usr/bin/env bash
# create-wecom-sheets.sh — attempt to create the 7 required WeCom smartsheets
# via wecom-cli's smartsheet_create command. Falls back gracefully if the
# command is unsupported.
#
# Usage:
#   create-wecom-sheets.sh <company-slug> <out-json>
#
# Output (stdout):
#   JSON object with shape:
#     {
#       "supported": true|false,
#       "sheets": [
#         {"label": "...", "docid": "...", "sheet_id": "..."},
#         ...
#       ]
#     }
#   If "supported": false, the array is empty and the caller switches to the
#   manual-fallback flow.

set -uo pipefail

SLUG="${1:-}"
OUT="${2:-}"

if [ -z "$SLUG" ] || [ -z "$OUT" ]; then
  echo "Usage: $0 <company-slug> <out-json>" >&2
  exit 2
fi

if ! command -v wecom-cli >/dev/null 2>&1; then
  echo '{"supported": false, "reason": "wecom-cli not on PATH"}' | tee "$OUT"
  exit 0
fi

# Probe — does wecom-cli expose smartsheet_create at all?
if ! wecom-cli doc 2>&1 | grep -q "smartsheet_create"; then
  echo '{"supported": false, "reason": "wecom-cli does not expose doc smartsheet_create"}' | tee "$OUT"
  exit 0
fi

# Schema mirrors references/wecom-sheet-schemas.md exactly.
# Each entry: label | columns (pipe-separated "name:type")
SHEETS=(
  "运价表（人）|区域:text|POD:text|船公司:text|20GP:text|40GP:text|40HQ:text|有效期:text|POL:text|超重费标准和其他费用:text"
  "运价信息（人）|入库日期:text|区域:text|段落标题:text|原文:text|来源:text|解析状态:text|备注:text"
  "每日简报（AI）|日期:text|简报标题:text|推广审核状态:text|备注:text|更新时间:text"
  "推广审核（AI+人）|推广标题:text|推广信息草稿:text|内部依据摘要:text|成本价检查:checkbox|审核状态:text|目标客户/分组:text|人工指定发送渠道:text|更新时间:text"
  "发送记录（AI）|发送时间:text|客户名:text|联系人:text|邮箱:text|航线/区域:text|邮件主题:text|发送状态:text|错误原因:text|回复状态:text"
  "客户线索表|公司名:text|官网:text|联系人:text|来源渠道:text"
  "待审核开发信|客户名:text|官网:text|联系人:text|来源渠道:text|信息获取状态:text|主营业务摘要:text|市场定位:text|潜在需求分析:text|与我司业务匹配度:text|画像摘要:text|开发信草稿:text|审核状态:text|人工指定发送渠道:text|异常原因:text|更新时间:text"
)

results='[]'
ok_count=0
err_count=0

for entry in "${SHEETS[@]}"; do
  label="${entry%%|*}"
  rest="${entry#*|}"

  cols_json='['
  first=1
  IFS='|' read -ra parts <<< "$rest"
  for col in "${parts[@]}"; do
    name="${col%%:*}"
    type="${col#*:}"
    if [ "$first" -eq 1 ]; then first=0; else cols_json+=','; fi
    cols_json+="{\"name\":\"$name\",\"type\":\"$type\"}"
  done
  cols_json+=']'

  payload=$(jq -nc --arg title "$label" --argjson cols "$cols_json" \
    '{title: $title, columns: $cols}')

  resp=$(wecom-cli doc smartsheet_create --json "$payload" 2>&1) || resp="__ERROR__"

  if [ "$resp" = "__ERROR__" ] || ! echo "$resp" | jq -e '.docid // .sheet_id' >/dev/null 2>&1; then
    err_count=$((err_count + 1))
    item=$(jq -nc --arg label "$label" --arg err "$resp" \
      '{label: $label, error: $err}')
  else
    ok_count=$((ok_count + 1))
    item=$(echo "$resp" | jq --arg label "$label" \
      '{label: $label, docid: (.docid // .doc_id // null), sheet_id: (.sheet_id // .sheetId // null), raw: .}')
  fi

  results=$(echo "$results" | jq --argjson item "$item" '. + [$item]')
done

result=$(jq -n --argjson r "$results" --arg slug "$SLUG" \
  --argjson ok "$ok_count" --argjson err "$err_count" \
  '{supported: true, slug: $slug, ok: $ok, errors: $err, sheets: $r}')

echo "$result" | tee "$OUT"
[ "$err_count" -eq 0 ]
