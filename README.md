# freight-skills

Industry-generic skills for ocean-freight forwarders, designed to be downloaded and adapted to any forwarder's WeCom workspace + chat-channel setup. Modeled after [claude-for-legal/ai-governance-legal](https://github.com/anthropics/claude-for-legal) but for the 货代 industry.

## What's in here

| Skill | What it does |
|---|---|
| `freight-onboard` | Detects fresh-install state and guides a new company through setup — collects intake info, creates the 7 WeCom smartsheets the other skills depend on (with the exact column structure documented in `references/wecom-sheet-schemas.md`), writes the workspace config, renders a cron config. Mirrors the `cold-start-interview` pattern from claude-for-legal. |
| `freight-lead-profiling` | Customer lead profiling + outreach. Reads 客户线索表 facts, scrapes the customer's website via [firecrawl CLI](https://github.com/firecrawl/cli), scores against the company's 航线/货类/出货规模 portfolio, drafts a personalized 开发信 into 待审核开发信 for human review. |
| `freight-rate-daily-promotion` | Daily rate brief + customer promotion. Reads dual-source 运价表/运价信息 from WeCom, pulls SCFI market context (via `freightindex-pp-cli`), sanity-checks CLS (via `schedule-pp-cli`), generates plain-text 简报 for chat channel + customer-safe 推广 to 推广审核 queue. Triggered via cron daily. |

## Layer in the cosein-to-b architecture

```
Layer 1  ·  agent-infra-skills   (mirador-watch, himalaya — mailbox watch + read/write)
Layer 2  ·  ocean-pp-cli         (Go CLIs: SCFI / 船期 / Comtrade)
Layer 2.5 · freight-skills        ← you are here (industry-generic freight skills + onboarding)
Layer 3  ·  freight-<company>    (private — real DocIDs, real chat IDs, real customer data)
```

## Install

### OpenClaw (recommended)

```bash
openclaw plugins install --marketplace boshenzh/freight-skills
openclaw config set plugins.allow '["freight-skills"]'   # merge with existing allow list
```

### Other agent runtimes

```bash
git clone https://github.com/boshenzh/freight-skills.git
# Then symlink relevant SKILL.md into the runtime's skill directory:
#   Codex:        ~/.codex/skills/<name>/SKILL.md
#   Claude Code:  ~/.claude/skills/<name>/SKILL.md
#   OpenClaw:     ~/.agents/skills/<name>/SKILL.md
```

## Fork for a new freight company

Each forwarder needs a thin private repo containing their real WeCom DocIDs, chat-channel binding, and any private raw templates. See [`docs/how-to-fork.md`](docs/how-to-fork.md) for the step-by-step.

Short version on a fresh VPS:

```bash
# 1. Install Layer 1 + 2 + 2.5
openclaw plugins install --marketplace boshenzh/agent-infra-skills
openclaw plugins install --marketplace boshenzh/ocean-pp-cli
openclaw plugins install --marketplace boshenzh/freight-skills

# 2. Trigger onboarding — the agent walks you through it conversationally
openclaw chat "Onboard a new freight company"
# (matches the freight-onboard skill description; the skill creates your 7
#  smartsheets, writes workspace/wecom/links.md, and renders a cron config)

# 3. Drop your real customer raw rate files when the skill prompts you for them.
```

## Prerequisites

See [`docs/prerequisites.md`](docs/prerequisites.md). Short list:

- `wecom-cli` (企微 smartsheet read/write)
- `firecrawl-cli` v1.16+ ([github.com/firecrawl/cli](https://github.com/firecrawl/cli)) — primary website scraper for lead profiling
- `freightindex-pp-cli` / `schedule-pp-cli` / `webprofile-pp-cli` from [ocean-pp-cli](https://github.com/boshenzh/ocean-pp-cli)
- One chat channel (Telegram / 飞书 / 企微 / 钉钉) configured in OpenClaw's delivery layer

## License

Apache-2.0. The 5 templates under `templates/` are sanitized industry references — no proprietary content. You may use, adapt, and redistribute freely.
