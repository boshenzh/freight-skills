# Column-name mapping fallback (Mode B)

When a company's existing 企微 sub-sheets have different column names than the canonical schema and the operator chooses **NOT** to rename in 企微 (option (e) in Mode B's reconcile), the operational skills (`freight-lead-profiling`, `freight-rate-daily-promotion`) need a translation layer at read/write time.

This translation lives in `~/.openclaw/workspace/shipping-rate-automation/wecom/links.md` as a `## Column mapping` block appended after the regular DocID/sheet_id sections.

## Format

```markdown
## Column mapping

# Format: <canonical_field_title> -> <operator's actual field_title>
# One mapping per line. Lines starting with # are comments.
# Only list mappings where canonical and actual differ; identical ones implicit.

[运价表（人）]
船公司 -> 承运人
POL -> 起运港
POD -> 目的港

[客户线索表]
公司名 -> 客户公司
来源渠道 -> 渠道
```

## How the operational skills use it

Pseudocode of skill behavior when reading a record:

```
canonical_field = "船公司"
mapping = parse(workspace/wecom/links.md → ## Column mapping → [运价表（人）])
actual_field = mapping.get(canonical_field, canonical_field)   # fallback: identical
value = record.values[actual_field]
```

Pseudocode for writing:

```
canonical_field = "审核状态"
mapping = parse(... → [推广审核（AI+人）])
actual_field = mapping.get(canonical_field, canonical_field)
record.values[actual_field] = "待审核"
```

## When mapping is the right tool

Mapping is the **escape hatch**, not the default. Prefer renaming in 企微 (`smartsheet_update_fields`) when the existing column name is just a synonym (船公司 ↔ 承运人) — renames cost zero ongoing maintenance.

Mapping is right when:
- The existing column name is **load-bearing for other people/workflows** (other 业务员 are used to seeing "承运人", a rename would surprise them)
- The existing column is referenced in 企微 视图 / 公式 / 触发器 that we can't see and renaming would silently break them
- The operator wants to defer the cleanup for a later session

## When mapping is the wrong tool

- **Different `field_type` between canonical and actual** — mapping doesn't translate values, only names. E.g. canonical says `成本价检查: FIELD_TYPE_CHECKBOX`, operator has `成本价检查: FIELD_TYPE_TEXT` storing "是"/"否" strings — that needs a value coercion layer, which we don't have. Solution: create a new column of the correct type.
- **Missing canonical fields** — mapping can't conjure a column that doesn't exist. Use `smartsheet_add_fields` to add it.
- **More than ~5 mappings per sheet** — at that scale just rename. Mapping becomes opaque.

## Bidirectional consistency

When mapping is in place, the same operational skill writes and reads through the mapping — both directions translate via the same table. There's no "outbound differs from inbound" case.

`freight-onboard` writes the mapping into links.md based on what the operator chose during Mode B reconcile. Subsequent operational skill runs read from links.md every time (don't cache across runs — operator may edit links.md between runs).
