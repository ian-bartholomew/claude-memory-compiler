# Meeting Compilation Design

## Context

The knowledge base compiler currently processes daily conversation logs (`daily/`) into wiki articles. Meeting notes at `~/Documents/Work/meetings/` contain rich technical discussions, decisions, and project context captured as AI-generated summaries — but none of this knowledge flows into the wiki today. This feature adds a parallel compilation pipeline for meetings.

## Scope

A new script `scripts/compile-meetings.py` that reads meeting summary files and compiles them into wiki articles, following the same patterns as `compile.py`.

## Design

### Script: `scripts/compile-meetings.py`

Mirrors `compile.py` structure. One Claude Agent SDK call per meeting directory.

**CLI:**

```
uv run python scripts/compile-meetings.py                              # new/changed only
uv run python scripts/compile-meetings.py --all                        # force recompile all
uv run python scripts/compile-meetings.py --meeting 2026-04-14-karpenter  # specific meeting
uv run python scripts/compile-meetings.py --dry-run                    # preview
```

**Meeting discovery:** Scans `MEETINGS_DIR` for directories matching `YYYY-MM-DD-*`. For each, collects `summary-*.md` files as compilation sources. Ignores transcripts (`transcript-*.md`), audio files, and `_metadata.json`.

**State tracking:** Uses existing `state.json` under key `"meetings_ingested"` (parallel to `"ingested"` for daily logs). Key = directory name (e.g., `"2026-04-14-karpenter"`), value = `{hash, compiled_at, cost_usd}`. Hash computed from all summary files concatenated and sorted by name.

**Agent call:** Follows `compile_daily_log()` pattern — `claude_agent_sdk.query()` with `permission_mode="acceptEdits"`, `max_turns=30`, working directory = `VAULT_DIR`. Tools: `[Read, Write, Edit, Glob, Grep, Bash]`.

### Prompt: `_build_meeting_prompt()`

Provides the agent with:

- AGENTS.md schema
- Wiki master index (`wiki/_index.md`)
- Domain indexes (`wiki/_indexes/*.md`)
- Existing wiki articles (full content)
- All summary files for the meeting (concatenated)
- Meeting metadata from `_metadata.json` (date, name, speaker count)

**Extraction rules:**

- Technical decisions and concepts → `wiki/concepts/`
- Processes, procedures, runbooks discussed → `wiki/guides/`
- Organization/team-specific knowledge → `wiki/company/`
- Learnings, book/conference references → `wiki/learning/`
- Action items and blockers are **skipped** (ephemeral, not knowledge)
- Routine standup status updates are **skipped** unless they contain technical decisions
- Scheduling/logistics discussions are **skipped**
- Speaker attributions are stripped — articles are third-person, encyclopedia style

**Frontmatter:**

```yaml
---
title: "Article Title"
domain: [primary-domain]
maturity: developing
confidence: medium
compiled_from:
  - "meetings/2026-04-14-karpenter/summary-default.md"
related:
  - "[[related-slug]]"
last_compiled: 2026-04-22
---
```

The agent updates `wiki/_index.md`, relevant `wiki/_indexes/*.md`, and `wiki/_log.md` just like the daily log compiler.

### Config Changes: `scripts/config.py`

Add one constant:

```python
MEETINGS_DIR = VAULT_DIR / "meetings"
```

### Utils Changes: `scripts/utils.py`

Add four functions:

- `list_meeting_dirs() -> list[Path]` — sorted directories matching `YYYY-MM-DD-*` in `MEETINGS_DIR`
- `list_meeting_summaries(meeting_dir: Path) -> list[Path]` — `summary-*.md` files in a meeting directory
- `read_meeting_metadata(meeting_dir: Path) -> dict` — parse `_metadata.json`, return `{}` if missing
- `meeting_hash(meeting_dir: Path) -> str` — SHA-256 of all summary files concatenated (sorted by name), first 16 hex chars

### Files to Create/Modify

| File | Action |
|------|--------|
| `scripts/compile-meetings.py` | **Create** — new script (~250 lines) |
| `scripts/config.py` | **Modify** — add `MEETINGS_DIR` constant |
| `scripts/utils.py` | **Modify** — add 4 meeting helper functions |

### Cost Estimate

- Per meeting: ~$0.45-0.65 (same as daily log compilation)
- Initial backfill (21 meetings): ~$9-14
- Some meetings (short standups) may produce no articles and cost less
- Ongoing: ~$0.50 per new meeting

## Verification

1. Run `--dry-run` to confirm all 21 meetings are discovered
2. Compile a single technical meeting: `--meeting 2026-04-14-karpenter`
3. Verify wiki articles created with correct frontmatter, wikilinks, and `compiled_from` referencing the meeting
4. Verify `wiki/_index.md`, domain indexes, and `wiki/_log.md` are updated
5. Run again without `--all` — confirm it skips already-compiled meetings
6. Run `uv run python scripts/lint.py --structural-only` to check for broken links
