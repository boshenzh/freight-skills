#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
render-cron-config.py — render a freight-rate-daily cron config JSON from
the slots collected during the freight-onboard intake.

Usage:
  render-cron-config.py \
    --company-slug orientlinkage \
    --chat-channel telegram \
    --chat-id 123456789 \
    --cron-time 08:00 \
    --out /path/to/cron/freight-rate-daily.json

Output: a fully-formed openclaw cron config JSON, ready for
`openclaw cron add --from-json`.
"""

import argparse
import json
import re
import sys
import uuid
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Render freight-rate-daily cron config from onboarding intake.",
        epilog="Exit codes: 0 ok, 2 bad args, 5 write failure.",
    )
    p.add_argument("--company-slug", required=True, help="lowercase-hyphen slug, e.g. 'orientlinkage'")
    p.add_argument("--chat-channel", required=True, choices=["telegram", "feishu", "wecom", "dingtalk"])
    p.add_argument("--chat-id", required=True, help="chat ID or webhook URL for the chat channel")
    p.add_argument("--cron-time", default="08:00", help="HH:MM in Asia/Shanghai (default 08:00)")
    p.add_argument("--tz", default="Asia/Shanghai")
    p.add_argument("--model", default="openai-codex/gpt-5.5", help="OpenClaw model identifier")
    p.add_argument("--out", required=True, help="output JSON file path")
    return p.parse_args()


def validate_cron_time(s: str) -> tuple[int, int]:
    m = re.match(r"^(\d{1,2}):(\d{2})$", s)
    if not m:
        sys.stderr.write(f"Error: --cron-time must be HH:MM, got: {s!r}\n")
        sys.exit(2)
    h, mn = int(m.group(1)), int(m.group(2))
    if not (0 <= h <= 23 and 0 <= mn <= 59):
        sys.stderr.write(f"Error: --cron-time out of range: {s!r}\n")
        sys.exit(2)
    return h, mn


def main() -> int:
    args = parse_args()
    h, mn = validate_cron_time(args.cron_time)
    cron_expr = f"{mn} {h} * * *"

    job_id = str(uuid.uuid4())

    payload_message = (
        f"你正在执行场景2「每日运价整理 + 推广」每日 {args.cron_time} 自动任务。\n\n"
        f"请先阅读并严格遵守流程文档：`$HOME/.agents/skills/freight-rate-daily-promotion/SKILL.md`。\n\n"
        "关键业务规则：\n"
        "1. 读取企微双源：运价表（人）和 运价信息（人）。DocID 和 sheet_id 从\n"
        "   `$HOME/.openclaw/workspace/shipping-rate-automation/wecom/links.md` 读取。\n"
        "2. 先做 housekeeping：归档 30 天前 run 文件夹。\n"
        "3. 必须尝试 SCFI：`$HOME/go/bin/freightindex-pp-cli pull --json` + digest；失败 fail-soft。\n"
        "4. 必须尝试船期/CLS：`$HOME/go/bin/schedule-pp-cli pull` + `next-cls --json`；失败 fail-soft。\n"
        "5. 成本价/底价/采购价/拿价 不得进入客户推广信息；推广信息只写「推广审核（AI+人）」，状态 `待审核` 或 `需补充信息`。\n"
        "6. 写「每日简报（AI）」只写 5 列 index。\n"
        "7. 不发送任何客户邮件。\n\n"
        "简报格式（plain-text 硬约束，跨频道通用）：\n"
        "- 第一行：`场景2 每日运价简报 YYYY-MM-DD`。\n"
        "- 块之间用 `-------------------------`。\n"
        "- 不要 Markdown 标题/表格/code fence/PDF/HTML/emoji/视觉样式。\n"
        "- 直接贴到聊天频道正文，不要 `.txt` 附件，不要 `MEDIA:`，不要 `--media`，不要 `--force-document`。\n"
        "- 接近频道单条限制时分多条纯文本消息。\n\n"
        "最终回复结构：\n"
        "1. 直接贴完整简报正文。\n"
        "2. 简报后用很短几行说明：简报记录ID、审核记录ID、数量摘要、推广审核状态、明确「客户邮件：未发送」。\n"
    )

    config = {
        "id": job_id,
        "name": f"{args.company_slug}-每日{args.cron_time}运价简报与推广审核",
        "description": f"每天 {args.cron_time} {args.tz} 读企微事实源 → 生成 plain-text 简报推 {args.chat_channel} → 写推广审核，待人工审核。",
        "enabled": True,
        "schedule": {
            "kind": "cron",
            "expr": cron_expr,
            "tz": args.tz,
            "staggerMs": 0,
        },
        "sessionTarget": "isolated",
        "wakeMode": "now",
        "payload": {
            "kind": "agentTurn",
            "timeoutSeconds": 900,
            "model": args.model,
            "toolsAllow": ["exec", "read", "write"],
            "message": payload_message,
        },
        "delivery": {
            "mode": "announce",
            "channel": args.chat_channel,
            "to": args.chat_id,
        },
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        out.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as e:
        sys.stderr.write(f"Error writing {out}: {e}\n")
        return 5

    print(json.dumps({
        "ok": True,
        "job_id": job_id,
        "wrote": str(out),
        "cron_expr": cron_expr,
        "delivery": {"channel": args.chat_channel, "to": args.chat_id},
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
