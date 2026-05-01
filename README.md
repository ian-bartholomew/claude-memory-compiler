# LLM Personal Knowledge Base

**Your AI conversations compile themselves into a searchable knowledge base.**

Adapted from [Karpathy's LLM Knowledge Base](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) architecture. Raw sources — daily conversation logs, web clippings, support threads, internal team discussions, docs, and meeting notes — are compiled by an LLM into structured, cross-referenced wiki articles. Claude Code hooks automatically capture your AI conversations into daily logs; you can also add web clippings (via Obsidian Web Clipper), support learnings, internal learnings, and documents to the `raw/` directory. The compiler processes all source types with source-specific instructions. Retrieval uses a simple index file instead of RAG - no vector database, no embeddings, just markdown.

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

Your vault needs a `raw/` directory structure for sources. Create it if it does not already exist:

```bash
mkdir -p ~/path/to/your/obsidian-vault/raw/{daily,daily_notes,clippings,support_learnings,internal_learnings,docs}
```

The compiler will automatically create the `wiki/` directory and its subdirectories (`concepts/`, `guides/`, `company/`, `learning/`, `qa/`, `_indexes/`) the first time it runs.

### What changes with an external vault

| | Clone into project (default) | External vault |
|---|---|---|
| Raw sources | `daily/` in repo | `raw/daily/`, `raw/clippings/`, etc. in vault |
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
    -> raw/daily/YYYY-MM-DD.md -> compile.py -> wiki/concepts/, guides/, company/
        -> SessionStart hook injects index into next session -> cycle repeats
```

Paths adapt based on vault configuration: with an external vault the compiler writes to `wiki/` in the vault; without one it writes to `knowledge/` in the repo.

- **Hooks** capture conversations automatically (session end + pre-compaction safety net)
- **flush.py** calls the Claude Agent SDK to decide what's worth saving, and after 6 PM triggers end-of-day compilation automatically
- **compile.py** compiles all raw source types (daily logs, clippings, support learnings, internal learnings, daily notes, docs, meetings) into organized wiki articles with cross-references
- **query.py** answers questions using index-guided retrieval (no RAG needed at personal scale)
- **lint.py** runs structural health checks (broken links, orphans, missing backlinks, sparse articles, staleness, contradictions)

## Key Commands

All commands are run from the compiler repo directory. Paths to daily logs and wiki articles adapt automatically based on your vault configuration.

```bash
# Compile all new/changed sources across all source types
uv run python scripts/compile.py

# Compile a specific source type
uv run python scripts/compile.py --source daily
uv run python scripts/compile.py --source clippings
uv run python scripts/compile.py --source support_learnings
uv run python scripts/compile.py --source internal_learnings
uv run python scripts/compile.py --source daily_notes
uv run python scripts/compile.py --source docs

# Compile a specific file (auto-detects source type)
uv run python scripts/compile.py --file raw/clippings/my-article.md

# Preview what would be compiled
uv run python scripts/compile.py --dry-run

# Force recompile everything
uv run python scripts/compile.py --all

# Compile meetings (separate script)
uv run python scripts/compile-meetings.py

# Query the knowledge base
uv run python scripts/query.py "question"
uv run python scripts/query.py "question" --file-back

# Health checks
uv run python scripts/lint.py                        # all checks (LLM contradiction check costs money)
uv run python scripts/lint.py --structural-only      # structural checks only (free, fast)
```

## Claude Code Skills (lyt-assistant plugin)

If you use the [lyt-assistant](https://github.com/ian-bartholomew/lyt-assistant) plugin, these skills provide interactive compilation with quality gates — an alternative to running the Python scripts directly.

| Skill | Purpose |
|-------|---------|
| `/compile` | Full pipeline: ingest unprocessed sources → validate new articles → discover missing links. The primary entry point. |
| `/compile clippings` | Scope compilation to a single source type (`daily`, `clippings`, `support_learnings`, `internal_learnings`, `daily_notes`, `docs`). |
| `/ingest` | Process raw sources into wiki articles with interactive review — dedup checks, source-type-specific guidance, reciprocal linking, post-compilation validation. |
| `/lint` | Run `lint.py` for structural checks, then layer on additional checks (maturity/confidence audit, duplicate detection, source attribution quality). Interactive fixes. |
| `/discover-links` | Find missing connections between wiki articles and add bidirectional `related:` links. |

**Recommended workflow:**

```
Morning:           /compile                 # processes yesterday's sources
After clipping:    /compile clippings       # immediate, while context is fresh
Weekly:            /lint                    # full wiki health check
                   /discover-links          # if lint found orphans or gaps
```

## Why No RAG?

Karpathy's insight: at personal scale (50-500 articles), the LLM reading a structured `index.md` outperforms vector similarity. The LLM understands what you're really asking; cosine similarity just finds similar words. RAG becomes necessary at ~2,000+ articles when the index exceeds the context window.

## Technical Reference

See **[AGENTS.md](AGENTS.md)** for the complete technical reference: article formats, hook architecture, script internals, cross-platform details, costs, and customization options. AGENTS.md is designed to give an AI agent everything it needs to understand, modify, or rebuild the system.
