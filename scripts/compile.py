"""
Compile daily conversation logs into structured knowledge articles.

This is the "LLM compiler" - it reads daily logs (source code) and produces
organized knowledge articles (the executable).

Usage:
    uv run python compile.py                    # compile new/changed logs only
    uv run python compile.py --all              # force recompile everything
    uv run python compile.py --file daily/2026-04-01.md  # compile a specific log
    uv run python compile.py --dry-run          # show what would be compiled
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from config import (
    AGENTS_FILE,
    ARTICLE_SUBDIRS,
    COMPILER_DIR,
    DAILY_DIR,
    INDEX_FILE,
    INDEXES_DIR,
    LOG_FILE,
    VAULT_DIR,
    WIKI_DIR,
    _is_external_vault,
    now_iso,
    today_iso,
)
from utils import (
    file_hash,
    list_raw_files,
    list_wiki_articles,
    load_state,
    read_wiki_index,
    save_state,
)


# ── Prompt builders ──────────────────────────────────────────────────


def _build_default_prompt(
    schema: str,
    wiki_index: str,
    existing_articles_context: str,
    log_path: Path,
    log_content: str,
    timestamp: str,
) -> str:
    """Build the compilation prompt for the original single-repo layout."""
    from config import CONCEPTS_DIR, CONNECTIONS_DIR

    return f"""You are a knowledge compiler. Your job is to read a daily conversation log
and extract knowledge into structured wiki articles.

## Schema (AGENTS.md)

{schema}

## Current Wiki Index

{wiki_index}

## Existing Wiki Articles

{existing_articles_context if existing_articles_context else "(No existing articles yet)"}

## Daily Log to Compile

**File:** {log_path.name}

{log_content}

## Your Task

Read the daily log above and compile it into wiki articles following the schema exactly.

### Rules:

1. **Extract key concepts** - Identify 3-7 distinct concepts worth their own article
2. **Create concept articles** in `knowledge/concepts/` - One .md file per concept
   - Use the exact article format from AGENTS.md (YAML frontmatter + sections)
   - Include `sources:` in frontmatter pointing to the daily log file
   - Use `[[concepts/slug]]` wikilinks to link to related concepts
   - Write in encyclopedia style - neutral, comprehensive
3. **Create connection articles** in `knowledge/connections/` if this log reveals non-obvious
   relationships between 2+ existing concepts
4. **Update existing articles** if this log adds new information to concepts already in the wiki
   - Read the existing article, add the new information, add the source to frontmatter
5. **Update knowledge/index.md** - Add new entries to the table
   - Each entry: `| [[path/slug]] | One-line summary | source-file | {timestamp[:10]} |`
6. **Append to knowledge/log.md** - Add a timestamped entry:
   ```
   ## [{timestamp}] compile | {log_path.name}
   - Source: daily/{log_path.name}
   - Articles created: [[concepts/x]], [[concepts/y]]
   - Articles updated: [[concepts/z]] (if any)
   ```

### File paths:
- Write concept articles to: {CONCEPTS_DIR}
- Write connection articles to: {CONNECTIONS_DIR}
- Update index at: {WIKI_DIR / 'index.md'}
- Append log at: {WIKI_DIR / 'log.md'}

### Quality standards:
- Every article must have complete YAML frontmatter
- Every article must link to at least 2 other articles via [[wikilinks]]
- Key Points section should have 3-5 bullet points
- Details section should have 2+ paragraphs
- Related Concepts section should have 2+ entries
- Sources section should cite the daily log with specific claims extracted
"""


def _build_vault_prompt(
    schema: str,
    wiki_index: str,
    existing_articles_context: str,
    log_path: Path,
    log_content: str,
    timestamp: str,
) -> str:
    """Build the compilation prompt for an external Obsidian vault."""
    date_today = today_iso()

    # Read domain indexes for extra context
    domain_index_context = ""
    if INDEXES_DIR.exists():
        parts = []
        for idx_file in sorted(INDEXES_DIR.glob("*.md")):
            content = idx_file.read_text(encoding="utf-8")
            parts.append(f"### {idx_file.stem}.md\n```markdown\n{content}\n```")
        if parts:
            domain_index_context = "\n\n".join(parts)

    return f"""You are a knowledge compiler for an Obsidian vault. Your job is to read a daily
conversation log and extract knowledge into structured wiki articles following the vault's
conventions exactly.

## Schema (AGENTS.md)

{schema}

## Current Master Index (wiki/_index.md)

{wiki_index}

## Domain Indexes (wiki/_indexes/)

{domain_index_context if domain_index_context else "(No domain indexes yet)"}

## Existing Wiki Articles

{existing_articles_context if existing_articles_context else "(No existing articles yet)"}

## Daily Log to Compile

**File:** {log_path.name}

{log_content}

## Your Task

Read the daily log above and compile it into wiki articles for this Obsidian vault.

### Article Placement

Place articles in the correct subdirectory based on content type:
- `wiki/concepts/` — "What is X?" — atomic knowledge, patterns, decisions, technical concepts
- `wiki/guides/` — "How do I X?" — step-by-step procedures, runbooks, tutorials
- `wiki/company/` — Organization-specific knowledge (Fanatics, team processes, internal tools)
- `wiki/learning/` — Books, courses, conferences, learning resources

### Frontmatter Format

Every article MUST use this exact YAML frontmatter structure:

```yaml
---
title: "Article Title"
domain: [primary-domain]
maturity: developing
confidence: medium
compiled_from:
  - "raw/daily/{log_path.name}"
related:
  - "[[related-slug]]"
last_compiled: {date_today}
---
```

- **domain**: One or more of: `sre`, `engineering`, `observability`, `infrastructure`, `databases`, `fanatics`, `learning`
- **maturity**: Default to `developing` for new articles. Use `draft` only for very thin content. Set `mature` only when updating an already substantial article.
- **confidence**: Default to `medium` for new articles. Use `high` only for well-established facts.
- **compiled_from**: List of daily log files that contributed to this article
- **related**: List of bare `[[slug]]` wikilinks to related articles
- **last_compiled**: Today's date: `{date_today}`

### Wikilink Convention

Use bare `[[kebab-case-slug]]` wikilinks — NO path prefixes. Examples:
- Correct: `[[circuit-breaker-pattern]]`
- Wrong: `[[concepts/circuit-breaker-pattern]]`

### Rules

1. **Extract key concepts** — Identify 3-7 distinct topics worth their own article
2. **Create articles** in the appropriate subdirectory (concepts/, guides/, company/, or learning/)
3. **Update existing articles** if this log adds information to topics already in the wiki
   - Add the daily log to `compiled_from:` frontmatter
   - Update `last_compiled:` to `{date_today}`
   - Add new related links to `related:` frontmatter
4. **NO connection articles** — Express relationships via `related:` frontmatter field instead
5. **Update wiki/_index.md** — Add new articles to the "Recently Compiled" section:
   ```
   - [[slug]] — one-line summary (compiled {date_today})
   ```
6. **Update the relevant domain index** in `wiki/_indexes/` — Add entries to the matching
   domain file (e.g., `wiki/_indexes/sre.md` for SRE articles). Create the domain index file
   if it doesn't exist.
7. **Append to wiki/_log.md** — Add a timestamped entry:
   ```
   ## [{date_today}] compile | Article Title
   - Source: raw/daily/{log_path.name}
   - Created: [[slug-a]], [[slug-b]]
   - Updated: [[slug-c]] (if any)
   ```

### File paths:
- Article directories: wiki/concepts/, wiki/guides/, wiki/company/, wiki/learning/
- Master index: {INDEX_FILE}
- Domain indexes: {INDEXES_DIR}/
- Build log: {LOG_FILE}

### Obsidian Tooling

You have access to the `obsidian` CLI which talks to the running Obsidian instance. **Prefer
the Obsidian CLI over raw Write/Edit** for vault operations when possible:

- **Create articles:** `obsidian create name="article-slug" content="..." path="wiki/concepts/"`
- **Append to log:** `obsidian append file="wiki/_log" content="..."`
- **Read articles:** `obsidian read file="article-slug"`
- **Search vault:** `obsidian search query="term" limit=10`

If the Obsidian CLI is not available (e.g., Obsidian is not running), fall back to Write/Edit.

### Obsidian Markdown Conventions

Use Obsidian-flavored Markdown throughout:
- **Wikilinks:** `[[slug]]` for internal links, `[[slug|display text]]` for custom display
- **Heading links:** `[[slug#Heading]]` to link to a specific section
- **Tags:** `#tag` inline or `tags: [tag1, tag2]` in frontmatter
- **Callouts:** `> [!note]`, `> [!tip]`, `> [!warning]` for highlighted information
- **Properties:** YAML frontmatter at the top of every file
- **Highlights:** `==highlighted text==` for emphasis

### Quality standards:
- Every article must have complete YAML frontmatter in the format above
- Every article must reference at least 2 related articles via `related:` frontmatter
- Use bare `[[slug]]` wikilinks throughout article body text
- Key Points section should have 3-5 bullet points
- Details section should have 2+ paragraphs
- Write in encyclopedia style — factual, concise, self-contained
- Sources section should cite the daily log with specific claims extracted
"""


# ── Compilation ──────────────────────────────────────────────────────


async def compile_daily_log(log_path: Path, state: dict) -> float:
    """Compile a single daily log into knowledge articles.

    Returns the API cost of the compilation.
    """
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ResultMessage,
        TextBlock,
        query,
    )

    log_content = log_path.read_text(encoding="utf-8")
    schema = AGENTS_FILE.read_text(encoding="utf-8")
    wiki_index = read_wiki_index()

    # Read existing articles for context
    existing_articles_context = ""
    existing = {}
    for article_path in list_wiki_articles():
        rel = article_path.relative_to(WIKI_DIR)
        existing[str(rel)] = article_path.read_text(encoding="utf-8")

    if existing:
        parts = []
        for rel_path, content in existing.items():
            parts.append(f"### {rel_path}\n```markdown\n{content}\n```")
        existing_articles_context = "\n\n".join(parts)

    timestamp = now_iso()

    # Select prompt based on vault mode
    prompt_args = dict(
        schema=schema,
        wiki_index=wiki_index,
        existing_articles_context=existing_articles_context,
        log_path=log_path,
        log_content=log_content,
        timestamp=timestamp,
    )

    if _is_external_vault:
        prompt = _build_vault_prompt(**prompt_args)
        tools = ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
    else:
        prompt = _build_default_prompt(**prompt_args)
        tools = ["Read", "Write", "Edit", "Glob", "Grep"]

    cost = 0.0

    try:
        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                cwd=str(VAULT_DIR),
                system_prompt={"type": "preset", "preset": "claude_code"},
                allowed_tools=tools,
                permission_mode="acceptEdits",
                max_turns=30,
            ),
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        pass  # compilation output - LLM writes files directly
            elif isinstance(message, ResultMessage):
                cost = message.total_cost_usd or 0.0
                print(f"  Cost: ${cost:.4f}")
    except Exception as e:
        print(f"  Error: {e}")
        return 0.0

    # Update state
    rel_path = log_path.name
    state.setdefault("ingested", {})[rel_path] = {
        "hash": file_hash(log_path),
        "compiled_at": now_iso(),
        "cost_usd": cost,
    }
    state["total_cost"] = state.get("total_cost", 0.0) + cost
    save_state(state)

    return cost


def main():
    parser = argparse.ArgumentParser(description="Compile daily logs into knowledge articles")
    parser.add_argument("--all", action="store_true", help="Force recompile all logs")
    parser.add_argument("--file", type=str, help="Compile a specific daily log file")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be compiled")
    args = parser.parse_args()

    state = load_state()

    # Determine which files to compile
    if args.file:
        target = Path(args.file)
        if not target.is_absolute():
            target = DAILY_DIR / target.name
        if not target.exists():
            # Try resolving relative to vault root
            target = VAULT_DIR / args.file
        if not target.exists():
            print(f"Error: {args.file} not found")
            sys.exit(1)
        to_compile = [target]
    else:
        all_logs = list_raw_files()
        if args.all:
            to_compile = all_logs
        else:
            to_compile = []
            for log_path in all_logs:
                rel = log_path.name
                prev = state.get("ingested", {}).get(rel, {})
                if not prev or prev.get("hash") != file_hash(log_path):
                    to_compile.append(log_path)

    if not to_compile:
        print("Nothing to compile - all daily logs are up to date.")
        return

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Files to compile ({len(to_compile)}):")
    for f in to_compile:
        print(f"  - {f.name}")

    if args.dry_run:
        return

    # Compile each file sequentially
    total_cost = 0.0
    for i, log_path in enumerate(to_compile, 1):
        print(f"\n[{i}/{len(to_compile)}] Compiling {log_path.name}...")
        cost = asyncio.run(compile_daily_log(log_path, state))
        total_cost += cost
        print(f"  Done.")

    articles = list_wiki_articles()
    print(f"\nCompilation complete. Total cost: ${total_cost:.2f}")
    print(f"Knowledge base: {len(articles)} articles")


if __name__ == "__main__":
    main()
