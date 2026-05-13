#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
create-wecom-sheets.py — fully-automated provisioning of WeCom smartsheet
workbenches for the freight-onboard skill (Mode A: fresh new company).

Per scenario:
  1. wecom-cli doc create_doc (doc_type=10) → new top-level smartsheet doc
     (comes with a default sub-sheet titled "智能表1" with a default field
     "文本"). Returns the docid.
  2. For each canonical sub-sheet defined in sheet-definitions.json:
     - First sub-sheet: reuse the default sub-sheet.
         * smartsheet_update_sheet  rename "智能表1" → canonical title
         * smartsheet_update_fields rename default "文本" → first canonical field
         * smartsheet_add_fields    add remaining N-1 canonical fields
     - Subsequent sub-sheets: create new via smartsheet_add_sheet (auto-
       creates a default field "智能表列").
         * smartsheet_update_fields rename "智能表列" → first canonical field
         * smartsheet_add_fields    add remaining N-1 canonical fields

This script handles wecom-cli's MCP JSON-RPC envelope (extracts inner JSON
from .result.content[0].text) and checks .errcode on every call.

Usage:
  create-wecom-sheets.py --company-slug <slug> --company-name <name> --out <out.json>

Output (stdout + --out file):
  {
    "company_slug": "...", "company_name": "...",
    "scenarios": {
      "1": {"docid": "...", "url": "...", "sheets": [{"title": "...", "sheet_id": "..."}, ...]},
      "2": {...}
    }
  }

Exit codes: 0 ok, 2 bad args, 4 wecom-cli/network failure, 5 file write failure.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


# -------- MCP envelope helpers --------

def call_wecom(method: str, payload: dict) -> dict:
    """Run `wecom-cli doc <method> --json '<payload>'`, strip the MCP JSON-RPC
    envelope, validate .errcode == 0, return the inner JSON payload."""
    if not shutil.which("wecom-cli"):
        raise RuntimeError("wecom-cli not on PATH; install via `npm install -g @wecom/cli`")

    cmd = ["wecom-cli", "doc", method, "--json", json.dumps(payload, ensure_ascii=False)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        raise RuntimeError(
            f"{method} returned exit {result.returncode}\n"
            f"  stderr: {result.stderr[:500]}\n"
            f"  stdout: {result.stdout[:500]}"
        )

    try:
        envelope = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"{method} stdout is not JSON: {result.stdout[:300]}") from e

    if envelope.get("isError", False):
        raise RuntimeError(f"{method} mcp isError=true: {result.stdout[:500]}")

    try:
        inner_text = envelope["result"]["content"][0]["text"]
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(
            f"{method} envelope missing .result.content[0].text: {result.stdout[:300]}"
        ) from e

    try:
        inner = json.loads(inner_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"{method} inner text not JSON: {inner_text[:300]}") from e

    if inner.get("errcode", 0) != 0:
        raise RuntimeError(
            f"{method} errcode={inner.get('errcode')} errmsg={inner.get('errmsg', '?')}\n"
            f"  payload sent: {json.dumps(payload, ensure_ascii=False)[:200]}"
        )

    return inner


# -------- per-sub-sheet provisioning --------

def provision_sub_sheet(
    docid: str,
    use_default: bool,
    sheet_title: str,
    fields_spec: list[dict],
) -> str:
    """Make one canonical sub-sheet inside `docid`.

    - use_default=True: reuse the doc's auto-created default sub-sheet (only
      for the FIRST canonical sub-sheet per scenario; saves one add_sheet call).
    - use_default=False: smartsheet_add_sheet to create a new sub-sheet.

    Common path:
      get_fields → identify the single default field
      → update_fields rename to first canonical field
      → add_fields add remaining fields (if any)

    Returns the resulting sheet_id.
    """
    if use_default:
        # The default sub-sheet that came with create_doc — typically titled "智能表1"
        resp = call_wecom("smartsheet_get_sheet", {"docid": docid})
        sheets = resp.get("sheet_list", [])
        if not sheets:
            raise RuntimeError(f"docid {docid} has no default sub-sheet — create_doc shape changed?")
        sheet_id = sheets[0]["sheet_id"]
        # Rename to canonical
        call_wecom("smartsheet_update_sheet", {
            "docid": docid,
            "properties": {"sheet_id": sheet_id, "title": sheet_title},
        })
    else:
        resp = call_wecom("smartsheet_add_sheet", {
            "docid": docid,
            "properties": {"title": sheet_title},
        })
        sheet_id = resp["properties"]["sheet_id"]

    # Identify the single default field (every new sub-sheet has exactly one)
    fields_resp = call_wecom("smartsheet_get_fields", {
        "docid": docid, "sheet_id": sheet_id,
    })
    fields = fields_resp.get("fields", [])
    if len(fields) != 1:
        raise RuntimeError(
            f"sub-sheet {sheet_id} ({sheet_title}) has {len(fields)} default fields, expected 1 — "
            f"wecom-cli behavior changed?"
        )
    default_field_id = fields[0]["field_id"]

    if not fields_spec:
        raise RuntimeError(f"sub-sheet {sheet_title} has no canonical fields defined")

    first_field = fields_spec[0]
    remaining = fields_spec[1:]

    # Rename default field to first canonical
    call_wecom("smartsheet_update_fields", {
        "docid": docid, "sheet_id": sheet_id,
        "fields": [{
            "field_id": default_field_id,
            "field_title": first_field["field_title"],
            "field_type": first_field["field_type"],
        }],
    })

    # Add remaining canonical fields in one call
    if remaining:
        call_wecom("smartsheet_add_fields", {
            "docid": docid, "sheet_id": sheet_id,
            "fields": remaining,
        })

    return sheet_id


# -------- main --------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Provision 2 WeCom smartsheet docs with the 7 canonical sub-sheets for freight-onboard Mode A.",
    )
    parser.add_argument("--company-slug", required=True,
                        help="lowercase-hyphen slug, e.g. 'orientlinkage' — used in doc-name only")
    parser.add_argument("--company-name", required=True,
                        help="full company name in Chinese, e.g. '东方联动国际货运代理'")
    parser.add_argument("--out", required=True, help="output JSON file path")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    defs_path = script_dir / "sheet-definitions.json"
    if not defs_path.is_file():
        sys.stderr.write(f"missing {defs_path}\n")
        return 2

    try:
        defs = json.loads(defs_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        sys.stderr.write(f"failed to read {defs_path}: {e}\n")
        return 2

    output: dict = {
        "ok": True,
        "company_slug": args.company_slug,
        "company_name": args.company_name,
        "scenarios": {},
    }

    scenarios_meta = {
        "1": "Scenario 1 · 拓客 / lead profiling workbench",
        "2": "Scenario 2 · 运价推广 / daily rate promotion workbench",
    }

    for scenario_num, description in scenarios_meta.items():
        scenario = defs["scenarios"][scenario_num]
        doc_name = f"{args.company_name} — {description}"

        print(f"[scenario {scenario_num}] create_doc: {doc_name}", file=sys.stderr)

        try:
            create_resp = call_wecom("create_doc", {
                "doc_type": 10,
                "doc_name": doc_name,
            })
        except RuntimeError as e:
            sys.stderr.write(f"create_doc failed for scenario {scenario_num}: {e}\n")
            return 4

        docid = create_resp["docid"]
        url = create_resp.get("url", "")
        print(f"[scenario {scenario_num}] docid={docid}", file=sys.stderr)

        sheets_out = []
        for idx, sheet_def in enumerate(scenario["sheets"]):
            use_default = (idx == 0)  # First canonical reuses the auto-created default
            label = sheet_def["title"]
            print(f"[scenario {scenario_num}] provision sub-sheet: {label} (use_default={use_default})", file=sys.stderr)

            try:
                sheet_id = provision_sub_sheet(
                    docid=docid,
                    use_default=use_default,
                    sheet_title=label,
                    fields_spec=sheet_def["fields"],
                )
            except RuntimeError as e:
                sys.stderr.write(f"provision sub-sheet {label} failed: {e}\n")
                return 4

            sheets_out.append({"title": label, "sheet_id": sheet_id})
            print(f"[scenario {scenario_num}]   sheet_id={sheet_id}", file=sys.stderr)

        output["scenarios"][scenario_num] = {
            "docid": docid,
            "url": url,
            "sheets": sheets_out,
        }

    out_path = Path(args.out)
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as e:
        sys.stderr.write(f"failed to write {out_path}: {e}\n")
        return 5

    # Echo JSON to stdout for the caller
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
