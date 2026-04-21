# AGENTS.md - Personal Knowledge Base Compiler Schema

> Adapted from [Andrej Karpathy's LLM Knowledge Base](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) architecture.
> Instead of ingesting external articles, this system compiles knowledge from your own AI conversations into an Obsidian vault.

## The Compiler Analogy

```
daily/          = source code    (your conversations - the raw material)
raw/            = libraries      (external sources - web clips, RFCs, docs)
LLM             = compiler       (extracts and organizes knowledge)
wiki/           = executable     (structured, queryable knowledge base)
lint            = test suite     (health checks for consistency)
queries         = runtime        (using the knowledge)
```

You don't manually organize your knowledge. You have conversations, curate sources, and the LLM handles the synthesis, cross-referencing, and maintenance.

The **compiler repo** (`claude-memory-compiler/`) contains the code — scripts, hooks, and this schema. The **vault** (`~/Documents/Work/`) contains the data — daily logs, raw sources, and compiled wiki articles. They are separate repositories connected by configuration.

---

## Architecture

### Two-Location Layout

```
claude-memory-compiler/        # The compiler (code)
├── AGENTS.md                  # This file — compiler specification
├── scripts/                   # CLI tools (compile, query, lint, flush)
├── hooks/                     # Claude Code hooks (session capture)
└── pyproject.toml             # Dependencies

~/Documents/Work/              # The vault (data) — an Obsidian vault
├── daily/                     # Layer 1: conversation logs
├── raw/                       # External source documents (user-owned)
│   ├── clippings/             #   Web clips, tweets, articles
│   └── docs/                  #   RFCs, whitepapers, internal docs
├── wiki/                      # Layer 2: compiled knowledge (LLM-owned)
├── projects/                  # Active project workspaces
├── meetings/                  # Meeting recordings and transcripts
├── output/                    # Generated reports, visualizations
└── archive/                   # Completed projects, stale content
```

### Layer 1: `daily/` - Conversation Logs (Immutable Source)

Daily logs capture what happened in your AI coding sessions. These are the "raw sources" — append-only, never edited after the fact. They live in the vault, not the compiler repo.

```
~/Documents/Work/daily/
├── 2026-04-01.md
├── 2026-04-02.md
├── ...
```

Each file follows this format:

```markdown
# Daily Log: YYYY-MM-DD

## Sessions

### Session (HH:MM) - Brief Title

**Context:** What the user was working on.

**Key Exchanges:**
- User asked about X, assistant explained Y
- Decided to use Z approach because...
- Discovered that W doesn't work when...

**Decisions Made:**
- Chose library X over Y because...
- Architecture: went with pattern Z

**Lessons Learned:**
- Always do X before Y to avoid...
- The gotcha with Z is that...

**Action Items:**
- [ ] Follow up on X
- [ ] Refactor Y when time permits
```

### Layer 2: `wiki/` - Compiled Knowledge (LLM-Owned)

The LLM owns this directory entirely. Humans read it but rarely edit it directly. Organized by knowledge type, navigated via indexes.

```
wiki/
├── _index.md             # Master catalog with domain index links
├── _log.md               # Append-only chronological activity record
├── _indexes/             # Domain-specific indexes
│   ├── sre.md
│   ├── engineering.md
│   ├── observability.md
│   ├── infrastructure.md
│   ├── databases.md
│   ├── fanatics.md
│   └── learning.md
├── _attachments/         # PDFs, images, screenshots
├── concepts/             # "What is X?" - patterns, principles, mental models
├── guides/               # "How do I X?" - runbooks, processes, how-tos
├── company/              # "How does our org do X?" - Fanatics-specific
├── learning/             # "What did I learn from X?" - books, courses, conferences
└── qa/                   # Filed Q&A answers
```

### Layer 3: This File (AGENTS.md)

The schema that tells the LLM how to compile and maintain the knowledge base. This is the "compiler specification." It lives in the compiler repo, not the vault.

---

## Structural Files

### `wiki/_index.md` - Master Catalog

A frontmatter-headed document linking to all domain indexes, with recently compiled articles and items needing attention. The LLM reads this FIRST when answering any query, then navigates to domain indexes to find relevant articles.

Format:

```markdown
---
title: Knowledge Base Index
type: index
last_updated: YYYY-MM-DD
article_count: N
---

# Knowledge Base Index

Total articles: N | Domains: 7

## Domain Indexes

- [[sre]] — reliability, resilience, distributed systems, SLOs (N articles)
- [[engineering]] — laws, principles, mental models (N articles)
- [[observability]] — monitoring, alerting, logging (N articles)
- [[infrastructure]] — Kubernetes, Terraform, IaC (N articles)
- [[databases]] — RDS, caching, consistency (N articles)
- [[fanatics]] — company-specific knowledge (N articles)
- [[learning]] — books, conferences, career (N articles)

## Recently Compiled

- [[article-slug]] — YYYY-MM-DD
- [[another-slug]] — YYYY-MM-DD

## Needs Attention

- [[draft-article]] — Article Title (draft)
```

### `wiki/_log.md` - Activity Log

Append-only chronological record of every compile, query, and lint operation.

Format:

```markdown
---
title: Wiki Log
type: log
---

# Wiki Log

## [YYYY-MM-DD] compile | Article Title
- Source: daily/YYYY-MM-DD.md
- Created: [[slug-a]], [[slug-b]]
- Updated: [[slug-c]] (if any)

## [YYYY-MM-DD] query (filed) | Question summary
- Question: What is...
- Consulted: [[slug-a]], [[slug-b]]
- Filed to: [[qa/slug]]

## [YYYY-MM-DD] lint | Health check
- Errors: N, Warnings: N, Suggestions: N
```

### `wiki/_indexes/*.md` - Domain Indexes

Each domain has its own index listing articles grouped by subtopic, with maturity status.

Format:

```markdown
---
title: SRE Domain Index
type: index
last_updated: YYYY-MM-DD
article_count: N
---

# SRE

## Resilience Patterns

- [[circuit-breaker]] — Fault isolation pattern (mature)
- [[bulkhead-pattern]] — Resource isolation (mature)
- [[blast-radius]] — Failure scope analysis (developing)

## Distributed Systems

- [[cap-theorem]] — Consistency/Availability/Partition tolerance (mature)
- [[consistency-models]] — Consistency Models (draft)
```

---

## Article Format

### Frontmatter Schema

Every wiki article MUST use this YAML frontmatter:

```yaml
---
title: "Article Title"
domain: [primary-domain, secondary-domain]
maturity: developing        # draft | developing | mature
confidence: high            # low | medium | high
compiled_from:
  - "daily/YYYY-MM-DD.md"
related:
  - "[[related-article]]"
last_compiled: YYYY-MM-DD
---
```

**Field definitions:**

- **title** — Human-readable title
- **domain** — One or more of the available domains (see below)
- **maturity** — Article lifecycle stage (see Maturity Lifecycle)
- **confidence** — How well-sourced and verified the content is
- **compiled_from** — Daily log files (or raw sources) that contributed to this article
- **related** — Bare `[[slug]]` wikilinks to related articles
- **last_compiled** — Date of most recent compilation update

### Article Body

```markdown
# Article Title

[2-4 sentence core explanation]

## Key Points

- [Bullet points, each self-contained]

## Details

[Deeper explanation, encyclopedia-style paragraphs]

## Sources

- Compiled from daily/YYYY-MM-DD.md — specific claim or context extracted
```

### Q&A Articles (`wiki/qa/`)

Filed answers from queries. Every complex question answered by the system can be permanently stored, making future queries smarter.

```markdown
---
title: "Q: Original Question"
domain: [relevant-domain]
maturity: developing
confidence: medium
type: qa
question: "The exact question asked"
consulted:
  - "[[article-1]]"
  - "[[article-2]]"
last_compiled: YYYY-MM-DD
---

# Q: Original Question

## Answer

[The synthesized answer with [[wikilinks]] to sources]

## Sources Consulted

- [[article-1]] — Relevant because...
- [[article-2]] — Provided context on...

## Follow-Up Questions

- What about edge case X?
- How does this change if Y?
```

---

## Article Placement Rules

Place articles based on the question they answer:

| Subfolder | Question | Examples |
|-----------|----------|----------|
| `wiki/concepts/` | "What is X?" | Patterns, principles, mental models, technologies |
| `wiki/guides/` | "How do I X?" | Runbooks, step-by-step processes, how-tos |
| `wiki/company/` | "How does our org do X?" | Organization architecture, tooling, team practices |
| `wiki/learning/` | "What did I learn from X?" | Book notes, course summaries, conference talks |
| `wiki/qa/` | Filed answer | Specific questions answered by querying the wiki |

**Decision heuristic:** If the content describes a concept, pattern, or technology in the abstract, it goes in `concepts/`. If it is a procedure someone would follow step-by-step, it goes in `guides/`. If it is specific to Fanatics (the company), it goes in `company/`. If it came from a book, course, or conference, it goes in `learning/`.

---

## Available Domains

Articles are tagged with one or more domains in their `domain:` frontmatter field. Each domain has a corresponding index file in `wiki/_indexes/`.

| Domain | Scope |
|--------|-------|
| `sre` | Reliability, resilience, distributed systems, SLOs, incident management |
| `engineering` | Laws, principles, mental models, software design |
| `observability` | Monitoring, alerting, logging, tracing |
| `infrastructure` | Kubernetes, Terraform, IaC, cloud platforms |
| `databases` | RDS, caching, consistency, data storage |
| `fanatics` | Company-specific knowledge — architecture, deployment, tooling |
| `learning` | Books, conferences, career development, learning resources |

---

## Cross-Cutting Relationships

There are no dedicated "connection" articles. Cross-cutting relationships are expressed through:

1. **`related:` frontmatter** — Every article lists related articles as bare `[[slug]]` wikilinks in its frontmatter. This is the primary mechanism for expressing relationships.
2. **Inline wikilinks** — Article body text uses `[[slug]]` links naturally when referencing other concepts.
3. **Domain indexes** — The `wiki/_indexes/*.md` files group related articles by subtopic, making clusters of related knowledge discoverable.

This approach keeps relationships distributed and maintainable rather than creating a separate layer of "connection" documents that drift out of sync.

---

## Maturity Lifecycle

```
draft  →  developing  →  mature  →  archive
```

- **Draft** — Initial compilation from a single source. May have gaps. Thin content.
- **Developing** — Multiple sources synthesized. Core content solid, edges rough.
- **Mature** — Well-sourced, cross-linked, reviewed. Reliable reference.
- **Archive** — Superseded or no longer relevant. Moved to `archive/`.

Maturity is tracked in frontmatter (`maturity: draft | developing | mature`). Compilation should default to `developing` for new articles. Use `draft` only for very thin content. Set `mature` only when updating an already substantial article with strong sourcing.

---

## Wikilink Conventions

- **Bare `[[kebab-case]]`** — No path prefixes. Write `[[circuit-breaker]]`, not `[[concepts/circuit-breaker]]`.
- **No `.md` extension** — Write `[[slug]]`, not `[[slug.md]]`.
- **Display text** — `[[slug|Display Text]]` for custom link text.
- **Heading links** — `[[slug#Heading]]` to link to a specific section.
- **Kebab-case filenames** — All wiki articles use lowercase hyphenated names (e.g., `circuit-breaker.md`, `graceful-degradation.md`).
- **Writing style** — Encyclopedia-style, factual, third-person where appropriate.
- **Dates** — ISO 8601 (`YYYY-MM-DD`).

---

## Obsidian Tooling

The vault is an Obsidian vault. All compile and query agents have access to the `obsidian` CLI and should use Obsidian-flavored Markdown.

### Obsidian CLI

The `obsidian` command-line tool talks to a running Obsidian instance. **Prefer it over raw Write/Edit** for vault operations — it ensures Obsidian's indexes, backlinks, and cache stay in sync.

Key commands:

| Command | Purpose | Example |
|---------|---------|---------|
| `obsidian create` | Create a new note | `obsidian create name="slug" content="..." path="wiki/concepts/"` |
| `obsidian read` | Read a note | `obsidian read file="slug"` |
| `obsidian append` | Append to a note | `obsidian append file="wiki/_log" content="..."` |
| `obsidian search` | Search the vault | `obsidian search query="term" limit=10` |
| `obsidian backlinks` | Show backlinks | `obsidian backlinks file="slug"` |
| `obsidian unresolved` | List broken links | `obsidian unresolved` |
| `obsidian property:set` | Set frontmatter property | `obsidian property:set file="slug" property="maturity" value="mature"` |

If Obsidian is not running, fall back to raw `Write`/`Edit` tools.

### Obsidian Markdown

Use Obsidian-flavored Markdown throughout all wiki articles:

- **Wikilinks:** `[[slug]]` for internal links, `[[slug|display text]]` for custom display
- **Embeds:** `![[slug]]` to embed a note, `![[image.png]]` for images
- **Callouts:** `> [!note]`, `> [!tip]`, `> [!warning]` for highlighted information
- **Tags:** `#tag` inline or `tags: [tag1, tag2]` in frontmatter
- **Highlights:** `==highlighted text==` for emphasis
- **Properties:** YAML frontmatter at the top of every file (required)
- **Block IDs:** `^block-id` to create linkable blocks

---

## Core Operations

### 1. Compile (daily/ -> wiki/)

When processing a daily log:

1. Read the daily log file
2. Read `wiki/_index.md` to understand current knowledge state
3. Read relevant domain indexes in `wiki/_indexes/`
4. Read existing articles that may need updating
5. For each piece of knowledge found in the log:
   - If an existing article covers this topic: UPDATE it with new information, add the daily log to `compiled_from:`
   - If it's a new topic: CREATE a new article in the appropriate subfolder (concepts/, guides/, company/, or learning/)
6. UPDATE `wiki/_index.md` with new/modified entries in "Recently Compiled"
7. UPDATE the relevant domain index in `wiki/_indexes/`
8. APPEND to `wiki/_log.md`

**Important guidelines:**

- A single daily log may touch 3-10 knowledge articles
- Prefer updating existing articles over creating near-duplicates
- Use bare `[[wikilinks]]` without path prefixes
- Write in encyclopedia style — factual, concise, self-contained
- Every article must have YAML frontmatter matching the schema above
- Every article must link back to its source daily logs via `compiled_from:`
- Express relationships via `related:` frontmatter, not connection articles

### 2. Query (Ask the Knowledge Base)

1. Read `wiki/_index.md` (the master catalog)
2. Navigate to the relevant domain index in `wiki/_indexes/`
3. Based on the question, identify 3-10 relevant articles from the indexes
4. Read those articles in full
5. Synthesize an answer with bare `[[wikilink]]` citations
6. If `--file-back` is specified: create a `wiki/qa/` article and update `_index.md` and `_log.md`

**Why this works without RAG:** At personal knowledge base scale (~hundreds of articles), the LLM reading a structured index outperforms cosine similarity. The LLM understands what the question is really asking and selects pages accordingly. Embeddings find similar words; the LLM finds relevant concepts.

### 3. Lint (Health Checks)

Seven checks, run periodically:

1. **Broken links** — `[[wikilinks]]` pointing to non-existent articles
2. **Orphan pages** — Articles with zero inbound links from other articles
3. **Orphan sources** — Daily logs that haven't been compiled yet
4. **Stale articles** — Source daily log changed since article was last compiled
5. **Contradictions** — Conflicting claims across articles (requires LLM judgment)
6. **Missing backlinks** — A links to B but B doesn't link back to A
7. **Sparse articles** — Below 200 words, likely incomplete

Output: a markdown report with severity levels (error, warning, suggestion).

---

## Vault Configuration

The compiler needs to know where the vault lives. Resolution order:

1. **`MEMORY_VAULT_DIR` environment variable** — Highest priority. Set in your shell profile:

   ```bash
   export MEMORY_VAULT_DIR=~/Documents/Work
   ```

2. **`scripts/vault-config.json`** — Checked if env var is not set:

   ```json
   { "vault_dir": "~/Documents/Work" }
   ```

3. **Fallback** — If neither is set, falls back to the compiler repo directory itself (original single-repo layout with `knowledge/` instead of `wiki/`).

When an external vault is configured, the compiler adapts automatically:

- `knowledge/` becomes `wiki/`
- `index.md` becomes `_index.md`
- `log.md` becomes `_log.md`
- Article subdirectories expand to include `concepts/`, `guides/`, `company/`, `learning/`, and `qa/`
- Wikilinks switch to bare `[[slug]]` format (no path prefixes)
- Domain indexes in `_indexes/` are used for navigation

---

## Full Project Structure

```
claude-memory-compiler/                  # Compiler repo (code)
├── .claude/
│   └── settings.json                    # Hook configuration (project-local)
├── .gitignore                           # Excludes runtime state, temp files
├── AGENTS.md                            # This file — schema + technical reference
├── README.md                            # Concise overview + quick start
├── pyproject.toml                       # Dependencies (at root so hooks can find it)
├── scripts/                             # CLI tools
│   ├── compile.py                       #   Compile daily logs -> wiki articles
│   ├── query.py                         #   Ask questions (index-guided, no RAG)
│   ├── lint.py                          #   7 health checks
│   ├── flush.py                         #   Extract memories from conversations
│   ├── config.py                        #   Path constants + vault resolution
│   ├── utils.py                         #   Shared helpers
│   ├── vault-config.json                #   Vault directory configuration
│   └── state.json                       #   Compilation state (gitignored)
├── hooks/                               # Claude Code hooks
│   ├── session-start.py                 #   Injects knowledge into every session
│   ├── session-end.py                   #   Extracts conversation -> daily log
│   └── pre-compact.py                   #   Captures context before compaction
└── reports/                             # Lint reports (gitignored)

~/Documents/Work/                        # Obsidian vault (data)
├── daily/                               # Layer 1: conversation logs (immutable)
│   ├── 2026-04-01.md
│   └── ...
├── raw/                                 # External sources (user-owned, immutable)
│   ├── clippings/                       #   Web clips, articles
│   └── docs/                            #   RFCs, whitepapers
├── wiki/                                # Layer 2: compiled knowledge (LLM-owned)
│   ├── _index.md                        #   Master catalog
│   ├── _log.md                          #   Append-only activity record
│   ├── _indexes/                        #   Domain indexes
│   ├── _attachments/                    #   PDFs, images
│   ├── concepts/                        #   Patterns, principles, mental models
│   ├── guides/                          #   Runbooks, how-tos
│   ├── company/                         #   Fanatics-specific knowledge
│   ├── learning/                        #   Books, courses, conferences
│   └── qa/                              #   Filed Q&A answers
├── projects/                            # Active project workspaces
├── meetings/                            # Meeting notes and transcripts
├── output/                              # Generated reports
└── archive/                             # Completed projects, stale content
```

---

## Hook System (Automatic Capture)

Hooks fire automatically during Claude Code sessions. They can be configured either locally (in the compiler repo's `.claude/settings.json`) or globally (in `~/.claude/settings.json`) for use across all projects.

### Global Hook Configuration

To capture knowledge from sessions in **any** project, configure hooks globally with absolute paths and the `MEMORY_VAULT_DIR` environment variable:

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "MEMORY_VAULT_DIR=~/Documents/Work uv run --directory /path/to/claude-memory-compiler python /path/to/claude-memory-compiler/hooks/session-start.py",
        "timeout": 15
      }]
    }],
    "PreCompact": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "MEMORY_VAULT_DIR=~/Documents/Work uv run --directory /path/to/claude-memory-compiler python /path/to/claude-memory-compiler/hooks/pre-compact.py",
        "timeout": 10
      }]
    }],
    "SessionEnd": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "MEMORY_VAULT_DIR=~/Documents/Work uv run --directory /path/to/claude-memory-compiler python /path/to/claude-memory-compiler/hooks/session-end.py",
        "timeout": 10
      }]
    }]
  }
}
```

Replace `/path/to/claude-memory-compiler` with the actual path to your compiler repo. The `MEMORY_VAULT_DIR` env var tells the scripts where the vault lives.

### Local Hook Configuration (`.claude/settings.json`)

When running Claude Code inside the compiler repo itself, use relative paths:

```json
{
  "hooks": {
    "SessionStart": [{ "matcher": "", "hooks": [{ "type": "command", "command": "uv run python hooks/session-start.py", "timeout": 15 }] }],
    "PreCompact": [{ "matcher": "", "hooks": [{ "type": "command", "command": "uv run python hooks/pre-compact.py", "timeout": 10 }] }],
    "SessionEnd": [{ "matcher": "", "hooks": [{ "type": "command", "command": "uv run python hooks/session-end.py", "timeout": 10 }] }]
  }
}
```

Empty `matcher` catches all events.

### Hook Details

**`session-start.py`** (SessionStart)

- Pure local I/O, no API calls, runs in under 1 second
- Reads `wiki/_index.md` and the most recent daily log
- Outputs JSON to stdout: `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}`
- Claude sees the knowledge base index at the start of every session
- Max context: 20,000 characters

**`session-end.py`** (SessionEnd)

- Reads hook input from stdin (JSON with `session_id`, `transcript_path`, `cwd`)
- Copies the raw JSONL transcript to a temp file (no parsing in the hook — keeps it fast)
- Spawns `flush.py` as a fully detached background process
- Recursion guard: exits immediately if `CLAUDE_INVOKED_BY` env var is set

**`pre-compact.py`** (PreCompact)

- Same architecture as session-end.py
- Fires before Claude Code auto-compacts the context window
- Guards against empty `transcript_path` (known Claude Code bug #13668)
- Critical for long sessions: captures context before summarization discards it

**Why both PreCompact and SessionEnd?** Long-running sessions may trigger multiple auto-compactions before you close the session. Without PreCompact, intermediate context is lost to summarization before SessionEnd ever fires.

### Background Flush Process (`flush.py`)

Spawned by both hooks as a fully detached background process:

- **Windows:** `CREATE_NO_WINDOW` flag
- **Mac/Linux:** Default process creation (no session detachment needed for background survival)

This ensures flush.py survives after Claude Code's hook process exits.

**What flush.py does:**

1. Sets `CLAUDE_INVOKED_BY=memory_flush` env var (prevents recursive hook firing)
2. Reads the pre-extracted conversation context from the temp `.md` file
3. Skips if context is empty or if same session was flushed within 60 seconds (deduplication)
4. Calls Claude Agent SDK (`query()` with `allowed_tools=[]`, `max_turns=2`)
5. Claude decides what's worth saving — returns structured bullet points or `FLUSH_OK`
6. Appends result to `daily/YYYY-MM-DD.md` in the vault
7. Cleans up temp context file
8. **End-of-day auto-compilation:** If it's past 6 PM local time (`COMPILE_AFTER_HOUR = 18`) and today's daily log has changed since its last compilation (hash comparison against `state.json`), spawns `compile.py` as another detached background process. This means compilation happens automatically once a day without needing a cron job or manual trigger.

### JSONL Transcript Format

Claude Code stores conversations as `.jsonl` files. Messages are nested under a `message` key:

```python
entry = json.loads(line)
msg = entry.get("message", {})
role = msg.get("role", "")     # "user" or "assistant"
content = msg.get("content", "")  # string or list of content blocks
```

Content can be a string or a list of blocks (`{"type": "text", "text": "..."}` dicts).

---

## Script Details

### compile.py - The Compiler

Uses the Claude Agent SDK's async streaming `query()`:

```python
async for message in query(
    prompt=compile_prompt,
    options=ClaudeAgentOptions(
        cwd=str(VAULT_DIR),
        system_prompt={"type": "preset", "preset": "claude_code"},
        allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
        permission_mode="acceptEdits",
        max_turns=30,
    ),
):
```

- Builds a prompt with: AGENTS.md schema, current `_index.md`, domain indexes, all existing articles, and the daily log
- Claude reads the daily log, decides what concepts to extract, and writes files directly to the vault
- `Bash` tool included so the agent can use the `obsidian` CLI for vault-aware operations
- `permission_mode="acceptEdits"` auto-approves all file operations
- `cwd` is set to `VAULT_DIR` so file operations target the vault, not the compiler repo
- Incremental: tracks SHA-256 hashes of daily logs in `state.json`, skips unchanged files
- Selects vault-specific or default prompt based on whether an external vault is configured
- Cost: ~$0.45-0.65 per daily log (increases as KB grows)

**CLI:**

```bash
uv run python scripts/compile.py              # compile new/changed only
uv run python scripts/compile.py --all        # force recompile everything
uv run python scripts/compile.py --file daily/2026-04-01.md
uv run python scripts/compile.py --dry-run
```

### query.py - Index-Guided Retrieval

Loads the entire knowledge base into context (master index + domain indexes + all articles). No RAG.

At personal KB scale (~hundreds of articles), the LLM reading a structured index outperforms vector similarity. The LLM understands what you're really asking; cosine similarity just finds similar words.

- Navigates from `_index.md` to domain indexes to specific articles
- Uses bare `[[slug]]` wikilinks for citations
- When filing back, creates Q&A articles with vault-convention frontmatter

**CLI:**

```bash
uv run python scripts/query.py "What auth patterns do I use?"
uv run python scripts/query.py "What's my error handling strategy?" --file-back
```

With `--file-back`, creates a Q&A article in `wiki/qa/` and updates the index and log. This is the compounding loop — every question makes the KB smarter.

### lint.py - Health Checks

Seven checks:

| Check | Type | Catches |
|-------|------|---------|
| Broken links | Structural | `[[wikilinks]]` to non-existent articles |
| Orphan pages | Structural | Articles with zero inbound links |
| Orphan sources | Structural | Daily logs not yet compiled |
| Stale articles | Structural | Source logs changed since compilation |
| Missing backlinks | Structural | A links to B but B doesn't link back |
| Sparse articles | Structural | Under 200 words |
| Contradictions | LLM | Conflicting claims across articles |

Handles both bare `[[slug]]` wikilinks (vault mode) and path-prefixed `[[concepts/slug]]` wikilinks (fallback mode).

**CLI:**

```bash
uv run python scripts/lint.py                    # all checks
uv run python scripts/lint.py --structural-only  # skip LLM check (free)
```

Reports saved to `reports/lint-YYYY-MM-DD.md`.

---

## State Tracking

`scripts/state.json` tracks:

- `ingested` — map of daily log filenames to SHA-256 hashes, compilation timestamps, and costs
- `query_count` — total queries run
- `last_lint` — timestamp of most recent lint
- `total_cost` — cumulative API cost

`scripts/last-flush.json` tracks flush deduplication (session_id + timestamp).

Both are gitignored and regenerated automatically.

---

## Dependencies

`pyproject.toml` (at compiler repo root):

- `claude-agent-sdk>=0.1.29` — Claude Agent SDK for LLM calls with tool use
- `python-dotenv>=1.0.0` — Environment variable management
- `tzdata>=2024.1` — Timezone data
- Python 3.12+, managed by [uv](https://docs.astral.sh/uv/)

No API key needed — uses Claude Code's built-in credentials at `~/.claude/.credentials.json`.

---

## Costs

| Operation | Cost |
|-----------|------|
| Compile one daily log | $0.45-0.65 |
| Query (no file-back) | ~$0.15-0.25 |
| Query (with file-back) | ~$0.25-0.40 |
| Full lint (with contradictions) | ~$0.15-0.25 |
| Structural lint only | $0.00 |
| Memory flush (per session) | ~$0.02-0.05 |

---

## Customization

### Additional Article Types

Add directories like `people/`, `tools/` to `wiki/`. Define the article format in this file (AGENTS.md), add the directory to `ARTICLE_SUBDIRS` in `config.py`, and update `utils.py`'s `list_wiki_articles()` to include them.

### Additional Domains

Add a new domain index at `wiki/_indexes/<domain>.md` and start tagging articles with the new domain name in their `domain:` frontmatter.

### Obsidian Integration

The vault is a native Obsidian vault. The `wiki/` directory uses pure markdown with `[[wikilinks]]` — graph view, backlinks, and search work natively. The `_index.md` and `_indexes/` structure provides deterministic navigation without requiring Obsidian's search or graph features.

### Scaling Beyond Index-Guided Retrieval

At ~2,000+ articles / ~2M+ tokens, the index becomes too large for the context window. At that point, add hybrid RAG (keyword + semantic search) as a retrieval layer before the LLM. See Karpathy's recommendation of `qmd` by Tobi Lutke for search at scale.
