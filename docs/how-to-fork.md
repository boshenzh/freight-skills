# How to fork freight-skills for a new freight company

`freight-skills` is the **industry-generic** layer. Every freight forwarder using it needs a **private binding repo** that holds their company-specific config (real WeCom DocIDs, chat-channel IDs, raw rate templates with company branding, etc.).

## Two-repo pattern

```
github.com/boshenzh/freight-skills            (public, Apache-2.0)  ← you don't fork this
                                              (skills are loaded via plugin install)
github.com/<your-org>/freight-<your-company>  (PRIVATE)             ← you create this
    └── workspace-seed/                       company DocIDs + raw files
    └── cron/                                 company chat ID
    └── scripts/install.sh                    seeds workspace, registers cron
```

## Steps

### 1. Install freight-skills + companion plugins

```bash
# Clone each plugin repo, then install from the local path with -l
git clone https://github.com/boshenzh/freight-skills.git
git clone https://github.com/boshenzh/agent-infra-skills.git
git clone https://github.com/boshenzh/ocean-pp-cli.git
openclaw plugins install -l ./freight-skills
openclaw plugins install -l ./agent-infra-skills
openclaw plugins install -l ./ocean-pp-cli
openclaw config set plugins.allow '["freight-skills","agent-infra-skills","ocean-pp-cli"]'
```

### 2. Run the onboard skill

```bash
openclaw chat "Onboard a new freight company for <your-company>"
```

The `freight-onboard` skill (in this plugin) detects the fresh-install state and walks you through 8 intake questions, creates 7 WeCom smartsheets, writes `~/.openclaw/workspace/shipping-rate-automation/wecom/links.md`, and renders a cron config.

If `wecom-cli` on your VPS can't reach the WeCom backend (auth expired, network blocked, API rejection), the skill switches to manual-fallback mode and prints precise instructions for creating each sheet in the WeCom UI; you paste each new DocID back.

### 3. Snapshot the resulting binding as a private repo

After onboard succeeds, snapshot the company-specific state into a fresh private repo:

```bash
mkdir ~/Projects/freight-<your-company> && cd ~/Projects/freight-<your-company>
git init

# Copy the company-specific workspace state
mkdir -p workspace-seed
cp -r ~/.openclaw/workspace/shipping-rate-automation/wecom workspace-seed/
cp -r ~/.openclaw/workspace/shipping-rate-automation/knowledge-base workspace-seed/

# Capture the per-company cron parameters into cron/cron-params.json
mkdir -p cron
cat > cron/cron-params.json <<'JSON'
{
  "job_name": "freight-<your-company>-daily-rate-brief",
  "cron_expr": "0 8 * * *",
  "tz": "Asia/Shanghai",
  "model": "<model alias OpenClaw should run the job with>",
  "chat_channel": "<telegram|feishu|wecom|dingtalk>",
  "chat_id": "<chat id or webhook URL>"
}
JSON

# Copy raw rate templates (private)
mkdir -p workspace-seed/raw-templates
cp /path/to/your/private/templates/*.{docx,xlsx,pdf} workspace-seed/raw-templates/

# Add scripts (install.sh seeds workspace + registers cron on a NEW VPS)
# See boshenzh/freight-orientlinkage for an example install.sh shape.

git add . && git commit -m "feat: freight-<your-company> v0.1"
gh repo create <your-org>/freight-<your-company> --private --source . --push
```

### 4. From now on, edits land in the right place

| You want to change | Edit which repo |
|---|---|
| The skill workflow logic / Gotchas / output format | `freight-skills` (upstream — open a PR if you want it merged) |
| Your company's WeCom DocIDs (after creating new sheets) | `freight-<your-company>/workspace-seed/wecom/links.md` |
| The 08:00 cron time, chat channel, chat ID, model | `freight-<your-company>/cron/cron-params.json` |
| Your private rate templates / service agreements | `freight-<your-company>/workspace-seed/raw-templates/` |
| The customer leads in 客户线索表 | WeCom UI directly — never via skill, never via git |

## Why not just fork freight-skills wholesale?

You could `git clone freight-skills && rm -rf .git && git init` and add your DocIDs to SKILL.md. **Don't do that.** Reasons:

1. You lose upstream improvements (firecrawl integration, new Gotchas, schema-evolution fixes) — every upstream patch becomes a manual cherry-pick.
2. Your private fork would contain real DocIDs in `skills/*/SKILL.md` — and once that fork is installed as an OpenClaw plugin, those files sit unredacted under `~/.openclaw/extensions/`, where anyone with shell access can read your bindings.
3. The "skill body = industry contract; workspace = company binding" split is the same separation `claude-for-legal/<domain>-legal` uses. Stay on the upstream pattern.

## Reference implementation

See [`boshenzh/freight-orientlinkage`](https://github.com/boshenzh/freight-orientlinkage) (private — accessible to authorized collaborators) for a fully-worked binding repo: workspace-seed, install.sh, verify.sh, cron config, private raw templates.
