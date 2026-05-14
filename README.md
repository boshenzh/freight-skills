# freight-skills

Industry-generic skills for ocean-freight forwarders (货代), designed to be downloaded and adapted to any forwarder's WeCom (企业微信) workspace and chat-channel setup. Modeled after [claude-for-legal/ai-governance-legal](https://github.com/anthropics/claude-for-legal) — same pattern (forkable plugin + per-company binding), different industry.

Public, Apache-2.0, no proprietary content. Three skills cover the most common 货代 workflows; the bundled `freight-onboard` skill walks a new company through setup conversationally.

## Skills

| Skill | What it does |
|---|---|
| `freight-onboard` | Conversational cold-start interview for new installs. Detects fresh-install state, runs an 8-question intake, then provisions the 7 canonical WeCom smartsheets (via `wecom-cli doc smartsheet_add_sheet` + `smartsheet_add_fields`) inside the 2 operator-pre-created empty docs. Also has a `Mode B` for *adopting* an existing manually-maintained 企微 workbench — inspects current schema, reports diff vs canonical, reconciles per-item with operator approval. Writes `workspace/wecom/links.md` and renders a daily cron config. |
| `freight-lead-profiling` | Customer lead profiling + first-touch 开发信 drafting. Reads 客户线索表 facts, scrapes the customer's website via [firecrawl CLI](https://github.com/firecrawl/cli) (or `web_fetch` fallback), scores against the company's 航线/货类/出货规模 portfolio, drafts a personalized 90–140 word 开发信 into 待审核开发信 for human review. Optional cross-references via [`webprofile-pp-cli`](https://github.com/boshenzh/ocean-pp-cli) (UN Comtrade trade flows) and [`schedule-pp-cli`](https://github.com/boshenzh/ocean-pp-cli) (lane coverage). |
| `freight-rate-daily-promotion` | Daily rate brief + customer promotion. Reads dual-source 运价表 / 运价信息 from WeCom, pulls SCFI market context via [`freightindex-pp-cli`](https://github.com/boshenzh/ocean-pp-cli), sanity-checks 船期/CLS via `schedule-pp-cli`, generates a plain-text 简报 to your chat channel (Telegram / 飞书 / 企微 / 钉钉), and queues customer-safe 推广 copy to a `推广审核` table for human approval. Triggered daily via cron. |

## Quick start (new freight company)

Three pieces:

1. **Install the plugin** (OpenClaw / Claude Code / Cursor / etc.)
2. **Pre-create 2 empty smartsheet docs** in 企微 UI (one for 拓客, one for 运价 — `wecom-cli` has no API to create top-level docs)
3. **Tell the agent to onboard you**

```bash
# Plugin install (example — OpenClaw): clone the repo, install from the local path
git clone https://github.com/boshenzh/freight-skills.git
openclaw plugins install -l ./freight-skills
openclaw config set plugins.allow '["freight-skills"]'   # merge with your existing allow list

# Trigger onboarding — the agent runs the cold-start interview
openclaw chat "Onboard a new freight company"
```

The agent then runs through an intake (company name, 2 DocIDs, chat channel, cron time, …) and provisions all 7 WeCom sub-sheets with their canonical column structures. Total time: ~15 minutes for a fresh install. See [`docs/how-to-fork.md`](docs/how-to-fork.md) for the full step-by-step.

If your company already has 企微 sheets you've been maintaining manually, the same skill handles *adopting* — see "Mode B" in [`skills/freight-onboard/SKILL.md`](skills/freight-onboard/SKILL.md).

## Install on other agent runtimes

```bash
git clone https://github.com/boshenzh/freight-skills.git

# OpenClaw — install the clone as a plugin (skills load from ~/.openclaw/extensions/):
openclaw plugins install -l ./freight-skills

# Other runtimes — symlink each SKILL.md into the runtime's skill directory:
#   Codex:        ~/.codex/skills/<name>/SKILL.md
#   Claude Code:  ~/.claude/skills/<name>/SKILL.md
```

## Prerequisites

See [`docs/prerequisites.md`](docs/prerequisites.md) for per-tool install. Short list:

- **`wecom-cli`** (企微 smartsheet read/write) — required by all three skills. Get from [WecomTeam/wecom-cli](https://github.com/WecomTeam/wecom-cli).
- **`firecrawl-cli`** v1.16+ ([github.com/firecrawl/cli](https://github.com/firecrawl/cli)) — primary website scraper for `freight-lead-profiling`. Falls back to `web_fetch` if absent.
- **[ocean-pp-cli](https://github.com/boshenzh/ocean-pp-cli)** binaries (`freightindex-pp-cli`, `schedule-pp-cli`, `webprofile-pp-cli`) — SCFI / 船期 / Comtrade data sources. Required by scenarios 1 and 2.
- **One chat channel** (Telegram / 飞书 / 企微 / 钉钉) configured in your agent runtime's delivery layer — for the daily 简报 push.

## How forking works

`freight-skills` is the **shared workflow** layer. Real company-specific binding (real WeCom DocIDs, real chat channel IDs, private rate templates, private customer data) lives in a **separate private repo** owned by each forwarder. The two pieces communicate via a workspace contract:

```
freight-skills (public)                              your-company/freight-<co> (private)
├── SKILL.md (workflow logic)                        ├── workspace-seed/wecom/links.md (real DocIDs)
└── reads from:                                      ├── cron/cron-params.json (real chat ID + model)
    ~/.openclaw/workspace/.../wecom/links.md   ◄──── ├── scripts/install.sh (seeds the workspace)
                                                     └── workspace-seed/raw-templates/ (your private docs)
```

Skill bodies stay **completely free** of real DocIDs / chat IDs / customer names. All company-specific values live in the workspace file `wecom/links.md`, which is created either by `freight-onboard` (new company) or by your private binding repo's `install.sh` (re-installing on a new VPS).

The same pattern as [claude-for-legal/ai-governance-legal](https://github.com/anthropics/claude-for-legal): one upstream workflow plugin, many private company forks. See [`docs/how-to-fork.md`](docs/how-to-fork.md) and [`docs/workspace-spec.md`](docs/workspace-spec.md) for the full contract.

## Companion plugins

These are independently-installable plugins that `freight-skills` references and depends on but does NOT bundle. Install separately:

| Plugin | Why you'd want it |
|---|---|
| [`agent-infra-skills`](https://github.com/boshenzh/agent-infra-skills) | Cross-business infrastructure — mirador-watch (IMAP IDLE long-poll for inbound-mail triggers), himalaya (mailbox read/write), wecomcli-smartsheet pointer. Required if you plan to run an email-triggered scenario (e.g. customer inquiry → quote draft). |
| [`ocean-pp-cli`](https://github.com/boshenzh/ocean-pp-cli) | The three Go CLIs (SCFI / 船期 / UN Comtrade) the skills query. Required by `freight-lead-profiling` and `freight-rate-daily-promotion`. |

## License

Apache-2.0. Skill bodies and references contain no proprietary content. You may use, adapt, and redistribute freely. The distilled industry structure documents the agent uses live as markdown under each skill's `references/` directory (e.g. `skills/freight-rate-daily-promotion/references/daily-rate-brief-source.md`) — those are agent-facing specifications, not customer-facing or company-branded artifacts. A new freight desk gets their initial empty smartsheets directly through the `freight-onboard` skill, with no need for separate xlsx/docx starter files.
