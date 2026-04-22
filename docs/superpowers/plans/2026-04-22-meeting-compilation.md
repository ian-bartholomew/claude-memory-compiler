# Meeting Compilation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `compile-meetings.py` script that processes meeting summary files into wiki articles, mirroring the existing daily-log compilation pipeline.

**Architecture:** New script `scripts/compile-meetings.py` iterates over meeting directories in `~/Documents/Work/meetings/`, reads `summary-*.md` files, and calls Claude Agent SDK to extract knowledge into wiki articles. Reuses existing config/utils infrastructure with small additions.

**Tech Stack:** Python 3.12+, claude-agent-sdk, existing config.py/utils.py modules

**Spec:** `docs/superpowers/specs/2026-04-22-meeting-compilation-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `scripts/config.py` | Modify (line 78) | Add `MEETINGS_DIR` constant |
| `scripts/utils.py` | Modify (after line 149) | Add 4 meeting helper functions |
| `scripts/compile-meetings.py` | Create | Main script — discovery, prompt, agent call, CLI |

---

### Task 1: Add MEETINGS_DIR to config.py

**Files:**

- Modify: `scripts/config.py:78` (after the `INDEXES_DIR` line)

- [ ] **Step 1: Add the MEETINGS_DIR constant**

In `scripts/config.py`, after line 78 (`INDEXES_DIR = WIKI_DIR / "_indexes"`), add:

```python
MEETINGS_DIR = VAULT_DIR / "meetings"
```

This goes right after `INDEXES_DIR` and before the `ARTICLE_SUBDIRS` block at line 81.

- [ ] **Step 2: Verify the import works**

Run: `cd /Users/ian.bartholomew/Dev/claude-memory-compiler && uv run python -c "from config import MEETINGS_DIR; print(MEETINGS_DIR)"`

Expected output: `/Users/ian.bartholomew/Documents/Work/meetings`

- [ ] **Step 3: Commit**

```bash
git add scripts/config.py
git commit -m "feat: add MEETINGS_DIR config constant"
```

---

### Task 2: Add meeting utility functions to utils.py

**Files:**

- Modify: `scripts/utils.py` (after `list_raw_files()` at line 149, and add `MEETINGS_DIR` to imports)

- [ ] **Step 1: Add MEETINGS_DIR to imports**

In `scripts/utils.py`, add `MEETINGS_DIR` to the import block at lines 8-17. The import should become:

```python
from config import (
    ARTICLE_SUBDIRS,
    DAILY_DIR,
    INDEX_FILE,
    INDEXES_DIR,
    LOG_FILE,
    MEETINGS_DIR,
    STATE_FILE,
    WIKI_DIR,
    _is_external_vault,
)
```

- [ ] **Step 2: Add the four meeting helper functions**

After `list_raw_files()` (line 149), add:

```python


# ── Meeting helpers ──────────────────────────────────────────────────


def list_meeting_dirs() -> list[Path]:
    """List meeting directories matching YYYY-MM-DD-* pattern."""
    if not MEETINGS_DIR.exists():
        return []
    return sorted(
        d for d in MEETINGS_DIR.iterdir()
        if d.is_dir() and re.match(r"\d{4}-\d{2}-\d{2}-", d.name)
    )


def list_meeting_summaries(meeting_dir: Path) -> list[Path]:
    """List summary-*.md files in a meeting directory."""
    return sorted(meeting_dir.glob("summary-*.md"))


def read_meeting_metadata(meeting_dir: Path) -> dict:
    """Read _metadata.json from a meeting directory. Returns {} if missing."""
    meta_file = meeting_dir / "_metadata.json"
    if not meta_file.exists():
        return {}
    try:
        return json.loads(meta_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def meeting_hash(meeting_dir: Path) -> str:
    """SHA-256 hash of all summary files in a meeting (first 16 hex chars).

    Summaries are sorted by name and concatenated before hashing,
    so the hash is stable regardless of filesystem ordering.
    """
    summaries = list_meeting_summaries(meeting_dir)
    if not summaries:
        return ""
    combined = b"".join(s.read_bytes() for s in summaries)
    return hashlib.sha256(combined).hexdigest()[:16]
```

- [ ] **Step 3: Verify the helpers work**

Run:

```bash
cd /Users/ian.bartholomew/Dev/claude-memory-compiler && uv run python -c "
from utils import list_meeting_dirs, list_meeting_summaries, read_meeting_metadata, meeting_hash
dirs = list_meeting_dirs()
print(f'Found {len(dirs)} meeting dirs')
print(f'First: {dirs[0].name}')
summaries = list_meeting_summaries(dirs[0])
print(f'Summaries: {[s.name for s in summaries]}')
meta = read_meeting_metadata(dirs[0])
print(f'Metadata: {meta}')
h = meeting_hash(dirs[0])
print(f'Hash: {h}')
"
```

Expected: 21 meeting dirs found, summaries listed, metadata parsed, hash computed.

- [ ] **Step 4: Commit**

```bash
git add scripts/utils.py
git commit -m "feat: add meeting discovery and hashing utilities"
```

---

### Task 3: Create compile-meetings.py — scaffold and CLI

**Files:**

- Create: `scripts/compile-meetings.py`

- [ ] **Step 1: Create the script with imports, CLI, and main loop (no prompt or agent call yet)**

Create `scripts/compile-meetings.py`:

```python
"""
Compile meeting summaries into structured knowledge articles.

Reads meeting summary files from the meetings/ directory and extracts
knowledge into wiki articles using the same pipeline as compile.py.

Usage:
    uv run python compile-meetings.py                              # new/changed only
    uv run python compile-meetings.py --all                        # force recompile all
    uv run python compile-meetings.py --meeting 2026-04-14-karpenter  # specific meeting
    uv run python compile-meetings.py --dry-run                    # preview
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from config import (
    AGENTS_FILE,
    INDEXES_DIR,
    INDEX_FILE,
    LOG_FILE,
    MEETINGS_DIR,
    VAULT_DIR,
    WIKI_DIR,
    now_iso,
    today_iso,
)
from utils import (
    list_meeting_dirs,
    list_meeting_summaries,
    list_wiki_articles,
    load_state,
    meeting_hash,
    read_meeting_metadata,
    read_wiki_index,
    save_state,
)


# ── Prompt builder ──────────────────────────────────────────────────


def _build_meeting_prompt(
    schema: str,
    wiki_index: str,
    existing_articles_context: str,
    meeting_dir: Path,
    summaries_content: str,
    metadata: dict,
) -> str:
    """Build the compilation prompt for meeting summaries."""
    # Placeholder — implemented in Task 4
    raise NotImplementedError


# ── Compilation ──────────────────────────────────────────────────────


async def compile_meeting(meeting_dir: Path, state: dict) -> float:
    """Compile a single meeting's summaries into knowledge articles.

    Returns the API cost of the compilation.
    """
    # Placeholder — implemented in Task 5
    raise NotImplementedError


def main():
    parser = argparse.ArgumentParser(
        description="Compile meeting summaries into knowledge articles"
    )
    parser.add_argument("--all", action="store_true", help="Force recompile all meetings")
    parser.add_argument("--meeting", type=str, help="Compile a specific meeting directory")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be compiled")
    args = parser.parse_args()

    state = load_state()

    # Determine which meetings to compile
    if args.meeting:
        target = MEETINGS_DIR / args.meeting
        if not target.exists():
            print(f"Error: meeting directory '{args.meeting}' not found in {MEETINGS_DIR}")
            sys.exit(1)
        summaries = list_meeting_summaries(target)
        if not summaries:
            print(f"Error: no summary-*.md files in {target}")
            sys.exit(1)
        to_compile = [target]
    else:
        all_meetings = list_meeting_dirs()
        if args.all:
            to_compile = [d for d in all_meetings if list_meeting_summaries(d)]
        else:
            to_compile = []
            for meeting_dir in all_meetings:
                if not list_meeting_summaries(meeting_dir):
                    continue
                prev = state.get("meetings_ingested", {}).get(meeting_dir.name, {})
                if not prev or prev.get("hash") != meeting_hash(meeting_dir):
                    to_compile.append(meeting_dir)

    if not to_compile:
        print("Nothing to compile - all meetings are up to date.")
        return

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Meetings to compile ({len(to_compile)}):")
    for d in to_compile:
        summaries = list_meeting_summaries(d)
        print(f"  - {d.name} ({len(summaries)} summary file(s))")

    if args.dry_run:
        return

    # Compile each meeting sequentially
    total_cost = 0.0
    for i, meeting_dir in enumerate(to_compile, 1):
        print(f"\n[{i}/{len(to_compile)}] Compiling {meeting_dir.name}...")
        cost = asyncio.run(compile_meeting(meeting_dir, state))
        total_cost += cost
        print(f"  Done.")

    articles = list_wiki_articles()
    print(f"\nCompilation complete. Total cost: ${total_cost:.2f}")
    print(f"Knowledge base: {len(articles)} articles")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify CLI and dry-run work**

Run: `cd /Users/ian.bartholomew/Dev/claude-memory-compiler && uv run python scripts/compile-meetings.py --dry-run`

Expected: Lists all 21 meetings (or however many have summary files) with their summary file counts. No compilation happens.

- [ ] **Step 3: Verify --meeting flag with dry-run**

Run: `cd /Users/ian.bartholomew/Dev/claude-memory-compiler && uv run python scripts/compile-meetings.py --meeting 2026-04-14-karpenter --dry-run`

Expected: Lists just the one meeting.

- [ ] **Step 4: Commit**

```bash
git add scripts/compile-meetings.py
git commit -m "feat: scaffold compile-meetings.py with CLI and meeting discovery"
```

---

### Task 4: Implement the meeting prompt

**Files:**

- Modify: `scripts/compile-meetings.py` (replace `_build_meeting_prompt` placeholder)

- [ ] **Step 1: Replace the placeholder _build_meeting_prompt function**

Replace the `_build_meeting_prompt` function (and its `raise NotImplementedError`) with:

```python
def _build_meeting_prompt(
    schema: str,
    wiki_index: str,
    existing_articles_context: str,
    meeting_dir: Path,
    summaries_content: str,
    metadata: dict,
) -> str:
    """Build the compilation prompt for meeting summaries."""
    date_today = today_iso()
    meeting_name = metadata.get("meeting_name", meeting_dir.name)
    meeting_date = metadata.get("date", meeting_dir.name[:10])
    num_speakers = metadata.get("num_speakers", "unknown")

    # Read domain indexes for extra context
    domain_index_context = ""
    if INDEXES_DIR.exists():
        parts = []
        for idx_file in sorted(INDEXES_DIR.glob("*.md")):
            content = idx_file.read_text(encoding="utf-8")
            parts.append(f"### {idx_file.stem}.md\n```markdown\n{content}\n```")
        if parts:
            domain_index_context = "\n\n".join(parts)

    # Build relative paths for compiled_from references
    summary_files = list_meeting_summaries(meeting_dir)
    compiled_from_lines = "\n".join(
        f'  - "meetings/{meeting_dir.name}/{s.name}"' for s in summary_files
    )

    return f"""You are a knowledge compiler for an Obsidian vault. Your job is to read meeting
summaries and extract durable knowledge into structured wiki articles.

## Schema (AGENTS.md)

{schema}

## Current Master Index (wiki/_index.md)

{wiki_index}

## Domain Indexes (wiki/_indexes/)

{domain_index_context if domain_index_context else "(No domain indexes yet)"}

## Existing Wiki Articles

{existing_articles_context if existing_articles_context else "(No existing articles yet)"}

## Meeting to Compile

**Meeting:** {meeting_name}
**Date:** {meeting_date}
**Speakers:** {num_speakers}
**Source directory:** meetings/{meeting_dir.name}/

{summaries_content}

## Your Task

Read the meeting summary above and compile durable knowledge into wiki articles for this
Obsidian vault. Focus on extractable knowledge — not ephemeral meeting logistics.

### What to Extract

- **Technical decisions and concepts** — architecture choices, technology selections,
  design patterns discussed → `wiki/concepts/`
- **Processes and procedures** — how things are done, runbooks, workflows discussed →
  `wiki/guides/`
- **Organization-specific knowledge** — team responsibilities, project phases, internal
  tooling, infrastructure details → `wiki/company/`
- **Learnings** — book references, conference talks, external resources mentioned →
  `wiki/learning/`

### What to Skip

- **Action items and blockers** — these are ephemeral and belong in project tracking, not
  the knowledge base
- **Routine status updates** — "I worked on X yesterday" unless it contains a technical
  decision or insight
- **Scheduling and logistics** — meeting times, availability, calendar coordination
- **Speaker attributions** — write in third person, encyclopedia style. Do not reference
  "Speaker 1" or individual names in article content

### If There Is Nothing Worth Extracting

Some meetings (especially short standups or pure planning sessions) may contain no durable
knowledge. If so, simply state: "No extractable knowledge in this meeting." and do not
create any articles.

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
{compiled_from_lines}
related:
  - "[[related-slug]]"
last_compiled: {date_today}
---
```

- **domain**: One or more of: `sre`, `engineering`, `observability`, `infrastructure`,
  `databases`, `fanatics`, `learning`, `tools`
- **maturity**: Default to `developing` for new articles. Use `draft` only for very thin
  content.
- **confidence**: Default to `medium` for new articles.
- **compiled_from**: List of meeting summary files that contributed to this article
- **related**: List of bare `[[slug]]` wikilinks to related articles
- **last_compiled**: Today's date: `{date_today}`

### Wikilink Convention

Use bare `[[kebab-case-slug]]` wikilinks — NO path prefixes. Examples:

- Correct: `[[karpenter-node-management]]`
- Wrong: `[[concepts/karpenter-node-management]]`

### Rules

1. **Extract key concepts** — Identify distinct topics worth their own article (typically 1-5
   per meeting, but 0 is fine for lightweight meetings)
2. **Create articles** in the appropriate subdirectory
3. **Update existing articles** if this meeting adds information to topics already in the wiki
   - Add the meeting summary to `compiled_from:` frontmatter
   - Update `last_compiled:` to `{date_today}`
   - Merge new information into the article body
4. **Update wiki/_index.md** — Add new articles to the "Recently Compiled" section
5. **Update the relevant domain index** in `wiki/_indexes/`
6. **Append to wiki/_log.md** — Add a timestamped entry:

   ```
   ## [{date_today}] meeting-compile | Article Title
   - Source: meetings/{meeting_dir.name}/summary-*.md
   - Created: [[slug-a]], [[slug-b]]
   - Updated: [[slug-c]] (if any)
   ```

### Obsidian Tooling

You have access to the `obsidian` CLI which talks to the running Obsidian instance. **Prefer
the Obsidian CLI over raw Write/Edit** for vault operations when possible:

- **Create articles:** `obsidian create name="article-slug" content="..." path="wiki/concepts/"`
- **Append to log:** `obsidian append file="wiki/_log" content="..."`
- **Read articles:** `obsidian read file="article-slug"`
- **Search vault:** `obsidian search query="term" limit=10`

If the Obsidian CLI is not available, fall back to Write/Edit.

### Obsidian Markdown Conventions

- **Wikilinks:** `[[slug]]` for internal links, `[[slug|display text]]` for custom display
- **Heading links:** `[[slug#Heading]]` to link to a specific section
- **Tags:** `#tag` inline or `tags: [tag1, tag2]` in frontmatter
- **Callouts:** `> [!note]`, `> [!tip]`, `> [!warning]` for highlighted information

### Quality standards

- Every article must have complete YAML frontmatter in the format above
- Every article must reference at least 2 related articles via `related:` frontmatter
- Use bare `[[slug]]` wikilinks throughout article body text
- Key Points section should have 3-5 bullet points
- Details section should have 2+ paragraphs
- Write in encyclopedia style — factual, concise, self-contained
"""

```

- [ ] **Step 2: Verify prompt builds without error**

Run:
```bash
cd /Users/ian.bartholomew/Dev/claude-memory-compiler && uv run python -c "
from compile_meetings import _build_meeting_prompt
from config import AGENTS_FILE
from utils import read_wiki_index
from pathlib import Path

schema = AGENTS_FILE.read_text()
wiki_index = read_wiki_index()
meeting_dir = Path('/Users/ian.bartholomew/Documents/Work/meetings/2026-04-14-karpenter')
summary = meeting_dir.joinpath('summary-default.md').read_text()
prompt = _build_meeting_prompt(
    schema=schema,
    wiki_index=wiki_index,
    existing_articles_context='',
    meeting_dir=meeting_dir,
    summaries_content=summary,
    metadata={'meeting_name': 'karpenter', 'date': '2026-04-14', 'num_speakers': 7},
)
print(f'Prompt length: {len(prompt)} chars')
print(f'Contains meeting name: {\"karpenter\" in prompt}')
print(f'Contains compiled_from: {\"meetings/2026-04-14-karpenter\" in prompt}')
"
```

Expected: Prompt builds successfully, contains meeting name and compiled_from path.

- [ ] **Step 3: Commit**

```bash
git add scripts/compile-meetings.py
git commit -m "feat: implement meeting compilation prompt"
```

---

### Task 5: Implement the compile_meeting agent call

**Files:**

- Modify: `scripts/compile-meetings.py` (replace `compile_meeting` placeholder)

- [ ] **Step 1: Replace the placeholder compile_meeting function**

Replace the `compile_meeting` function (and its `raise NotImplementedError`) with:

```python
async def compile_meeting(meeting_dir: Path, state: dict) -> float:
    """Compile a single meeting's summaries into knowledge articles.

    Returns the API cost of the compilation.
    """
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ResultMessage,
        TextBlock,
        query,
    )

    # Read all summary files
    summaries = list_meeting_summaries(meeting_dir)
    if not summaries:
        print(f"  Skipped: no summary files")
        return 0.0

    summaries_content_parts = []
    for s in summaries:
        content = s.read_text(encoding="utf-8")
        summaries_content_parts.append(f"### {s.name}\n\n{content}")
    summaries_content = "\n\n---\n\n".join(summaries_content_parts)

    metadata = read_meeting_metadata(meeting_dir)
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

    prompt = _build_meeting_prompt(
        schema=schema,
        wiki_index=wiki_index,
        existing_articles_context=existing_articles_context,
        meeting_dir=meeting_dir,
        summaries_content=summaries_content,
        metadata=metadata,
    )

    cost = 0.0

    try:
        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                cwd=str(VAULT_DIR),
                system_prompt={"type": "preset", "preset": "claude_code"},
                allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
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
    state.setdefault("meetings_ingested", {})[meeting_dir.name] = {
        "hash": meeting_hash(meeting_dir),
        "compiled_at": now_iso(),
        "cost_usd": cost,
    }
    state["total_cost"] = state.get("total_cost", 0.0) + cost
    save_state(state)

    return cost
```

- [ ] **Step 2: Commit**

```bash
git add scripts/compile-meetings.py
git commit -m "feat: implement meeting compilation agent call"
```

---

### Task 6: End-to-end verification

- [ ] **Step 1: Run dry-run to confirm discovery**

Run: `cd /Users/ian.bartholomew/Dev/claude-memory-compiler && uv run python scripts/compile-meetings.py --dry-run`

Expected: Lists all meetings with summary files and their counts.

- [ ] **Step 2: Compile a single technical meeting**

Run: `cd /Users/ian.bartholomew/Dev/claude-memory-compiler && uv run python scripts/compile-meetings.py --meeting 2026-04-14-karpenter`

Expected: Agent runs, creates/updates wiki articles, prints cost.

- [ ] **Step 3: Verify wiki output**

Check:

- New articles exist in `wiki/concepts/` or `wiki/company/` with correct frontmatter
- `compiled_from:` references `meetings/2026-04-14-karpenter/summary-default.md`
- `wiki/_index.md` has new entries in "Recently Compiled"
- `wiki/_log.md` has a new entry with `meeting-compile` type
- Relevant `wiki/_indexes/*.md` file was updated

- [ ] **Step 4: Verify incremental state tracking**

Run: `cd /Users/ian.bartholomew/Dev/claude-memory-compiler && uv run python scripts/compile-meetings.py --dry-run`

Expected: The karpenter meeting is NOT listed (already compiled). Other meetings still appear.

- [ ] **Step 5: Run structural lint**

Run: `cd /Users/ian.bartholomew/Dev/claude-memory-compiler && uv run python scripts/lint.py --structural-only`

Expected: No new broken links from the meeting-compiled articles.

- [ ] **Step 6: Final commit**

```bash
git add scripts/compile-meetings.py scripts/config.py scripts/utils.py
git commit -m "feat: complete meeting compilation pipeline"
```
