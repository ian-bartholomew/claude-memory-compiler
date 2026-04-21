# LLM Personal Knowledge Base

**Your AI conversations compile themselves into a searchable knowledge base.**

Adapted from [Karpathy's LLM Knowledge Base](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) architecture, but instead of clipping web articles, the raw data is your own conversations with Claude Code. When a session ends (or auto-compacts mid-session), Claude Code hooks capture the conversation transcript and spawn a background process that uses the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk) to extract the important stuff - decisions, lessons learned, patterns, gotchas - and appends it to a daily log. You then compile those daily logs into structured, cross-referenced knowledge articles organized by concept. Retrieval uses a simple index file instead of RAG - no vector database, no embeddings, just markdown.

Anthropic has clarified that personal use of the Claude Agent SDK is covered under your existing Claude subscription (Max, Team, or Enterprise) - no separate API credits needed. Unlike OpenClaw, which requires API billing for its memory flush, this runs on your subscription.

## Quick Start

Tell your AI coding agent:

> "Clone <https://github.com/ian-bartholomew/claude-memory-compiler> into this project. Set up the Claude Code hooks so my conversations automatically get captured into daily logs, compiled into a knowledge base, and injected back into future sessions. Read the AGENTS.md for the full technical reference on how everything works."

The agent will:

1. Clone the repo and run `uv sync` to install dependencies
2. Copy `.claude/settings.json` into your project (or merge the hooks into your existing settings)
3. The hooks activate automatically next time you open Claude Code

From there, your conversations start accumulating. After 6 PM local time, the next session flush automatically triggers compilation of that day's logs into knowledge articles. You can also run `uv run python scripts/compile.py` manually at any time.

By default, all data (`daily/` logs and `knowledge/` articles) lives inside the cloned repo. If you want your knowledge base in a separate Obsidian vault instead, see [External Vault](#external-vault) below.

## External Vault

For users who want their knowledge base to live in an existing Obsidian vault (separate from the compiler repo), configure the compiler to point at your vault.

### Option A: Config file

Create `scripts/vault-config.json` in the compiler repo:

```json
{
  "vault_dir": "~/path/to/your/obsidian-vault"
}
```

### Option B: Environment variable

Set the `MEMORY_VAULT_DIR` environment variable:

```bash
export MEMORY_VAULT_DIR=~/path/to/your/obsidian-vault
```

The environment variable takes precedence over the config file if both are set.

### Vault setup

Your vault needs a `daily/` directory for conversation logs. Create it if it does not already exist:

```bash
mkdir -p ~/path/to/your/obsidian-vault/daily
```

The compiler will automatically create the `wiki/` directory and its subdirectories (`concepts/`, `guides/`, `company/`, `learning/`, `qa/`, `_indexes/`) the first time it runs.

### What changes with an external vault

| | Clone into project (default) | External vault |
|---|---|---|
| Daily logs | `daily/` in repo | `daily/` in vault |
| Compiled articles | `knowledge/` | `wiki/` |
| Index file | `knowledge/index.md` | `wiki/_index.md` |
| Article categories | concepts, connections, qa | concepts, guides, company, learning, qa |

### Cross-project hooks

To capture conversations from any project (not just the one where you cloned the compiler), add the hooks to your global Claude Code settings at `~/.claude/settings.json`. Use absolute paths:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run --project /absolute/path/to/claude-memory-compiler python /absolute/path/to/claude-memory-compiler/hooks/session-start.py",
            "timeout": 15
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run --project /absolute/path/to/claude-memory-compiler python /absolute/path/to/claude-memory-compiler/hooks/pre-compact.py",
            "timeout": 10
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run --project /absolute/path/to/claude-memory-compiler python /absolute/path/to/claude-memory-compiler/hooks/session-end.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

Replace `/absolute/path/to/claude-memory-compiler` with the actual path where you cloned the repo.

## How It Works

```
Conversation -> SessionEnd/PreCompact hooks -> flush.py extracts knowledge
    -> daily/YYYY-MM-DD.md -> compile.py -> wiki/concepts/, guides/, qa/
        -> SessionStart hook injects index into next session -> cycle repeats
```

Paths adapt based on vault configuration: with an external vault the compiler writes to `wiki/` in the vault; without one it writes to `knowledge/` in the repo.

- **Hooks** capture conversations automatically (session end + pre-compaction safety net)
- **flush.py** calls the Claude Agent SDK to decide what's worth saving, and after 6 PM triggers end-of-day compilation automatically
- **compile.py** turns daily logs into organized concept articles with cross-references (triggered automatically or run manually)
- **query.py** answers questions using index-guided retrieval (no RAG needed at personal scale)
- **lint.py** runs 7 health checks (broken links, orphans, contradictions, staleness)

## Key Commands

All commands are run from the compiler repo directory. Paths to daily logs and wiki articles adapt automatically based on your vault configuration.

```bash
uv run python scripts/compile.py                    # compile new daily logs
uv run python scripts/query.py "question"            # ask the knowledge base
uv run python scripts/query.py "question" --file-back # ask + save answer back
uv run python scripts/lint.py                        # run health checks
uv run python scripts/lint.py --structural-only      # free structural checks only
```

## Why No RAG?

Karpathy's insight: at personal scale (50-500 articles), the LLM reading a structured `index.md` outperforms vector similarity. The LLM understands what you're really asking; cosine similarity just finds similar words. RAG becomes necessary at ~2,000+ articles when the index exceeds the context window.

## Technical Reference

See **[AGENTS.md](AGENTS.md)** for the complete technical reference: article formats, hook architecture, script internals, cross-platform details, costs, and customization options. AGENTS.md is designed to give an AI agent everything it needs to understand, modify, or rebuild the system.
