"""Shared utilities for the personal knowledge base."""

import hashlib
import json
import re
from pathlib import Path

from config import (
    ARTICLE_SUBDIRS,
    CLIPPINGS_DIR,
    DAILY_DIR,
    DOCS_DIR,
    INTERNAL_LEARNINGS_DIR,
    INDEX_FILE,
    INDEXES_DIR,
    LOG_FILE,
    MEETINGS_DIR,
    STATE_FILE,
    SUPPORT_LEARNINGS_DIR,
    WIKI_DIR,
    _is_external_vault,
)


# ── State management ──────────────────────────────────────────────────

def load_state() -> dict:
    """Load persistent state from state.json."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"ingested": {}, "meetings_ingested": {}, "query_count": 0, "last_lint": None, "total_cost": 0.0}


def save_state(state: dict) -> None:
    """Save state to state.json."""
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


# ── File hashing ──────────────────────────────────────────────────────

def file_hash(path: Path) -> str:
    """SHA-256 hash of a file (first 16 hex chars)."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


# ── Slug / naming ─────────────────────────────────────────────────────

def slugify(text: str) -> str:
    """Convert text to a filename-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


# ── Wikilink helpers ──────────────────────────────────────────────────

def extract_wikilinks(content: str) -> list[str]:
    """Extract all [[wikilinks]] from markdown content."""
    return re.findall(r"\[\[([^\]]+)\]\]", content)


def _normalize_wikilink(link: str) -> str:
    """Strip display text (|...) and heading anchors (#...) from a wikilink."""
    link = link.split("|")[0]   # [[slug|display text]] → slug
    link = link.split("#")[0]   # [[slug#Heading]] → slug
    return link.strip()


def wiki_article_exists(link: str) -> bool:
    """Check if a wikilinked article exists on disk.

    Handles bare links ([[slug]]), path-prefixed links ([[concepts/slug]]),
    display text ([[slug|text]]), and heading anchors ([[slug#Heading]]).
    """
    link = _normalize_wikilink(link)
    if not link:
        return True  # bare anchor like [[#Heading]] refers to same file
    # Try direct path first (path-prefixed link like concepts/slug)
    if (WIKI_DIR / f"{link}.md").exists():
        return True
    # Search across all content subdirectories (bare link like slug)
    stem = Path(link).stem if "/" in link else link
    for subdir in ARTICLE_SUBDIRS:
        if (subdir / f"{stem}.md").exists():
            return True
    return False


def find_article_path(link: str) -> Path | None:
    """Find the actual file path for a wikilink. Returns None if not found."""
    link = _normalize_wikilink(link)
    if not link:
        return None
    # Try direct path first
    direct = WIKI_DIR / f"{link}.md"
    if direct.exists():
        return direct
    # Search subdirectories
    stem = Path(link).stem if "/" in link else link
    for subdir in ARTICLE_SUBDIRS:
        candidate = subdir / f"{stem}.md"
        if candidate.exists():
            return candidate
    return None


# ── Wiki content helpers ──────────────────────────────────────────────

def read_wiki_index() -> str:
    """Read the knowledge base index file."""
    if INDEX_FILE.exists():
        return INDEX_FILE.read_text(encoding="utf-8")
    if _is_external_vault:
        return "# Knowledge Base Index\n\n(empty - no articles compiled yet)"
    return (
        "# Knowledge Base Index\n\n"
        "| Article | Summary | Compiled From | Updated |\n"
        "|---------|---------|---------------|---------|"
    )


def read_domain_indexes() -> str:
    """Read all domain index files (external vault only)."""
    if not _is_external_vault or not INDEXES_DIR.exists():
        return ""
    parts = []
    for idx_file in sorted(INDEXES_DIR.glob("*.md")):
        content = idx_file.read_text(encoding="utf-8")
        parts.append(f"### Domain Index: {idx_file.stem}\n\n{content}")
    return "\n\n".join(parts)


def read_all_wiki_content() -> str:
    """Read index + all wiki articles into a single string for context."""
    parts = [f"## INDEX\n\n{read_wiki_index()}"]

    # Include domain indexes for external vault
    domain_idx = read_domain_indexes()
    if domain_idx:
        parts.append(f"## DOMAIN INDEXES\n\n{domain_idx}")

    for subdir in ARTICLE_SUBDIRS:
        if not subdir.exists():
            continue
        for md_file in sorted(subdir.glob("*.md")):
            rel = md_file.relative_to(WIKI_DIR)
            content = md_file.read_text(encoding="utf-8")
            parts.append(f"## {rel}\n\n{content}")

    return "\n\n---\n\n".join(parts)


def list_wiki_articles() -> list[Path]:
    """List all wiki article files."""
    articles = []
    for subdir in ARTICLE_SUBDIRS:
        if subdir.exists():
            articles.extend(sorted(subdir.glob("*.md")))
    return articles


def list_raw_files() -> list[Path]:
    """List all daily log files."""
    if not DAILY_DIR.exists():
        return []
    return sorted(DAILY_DIR.glob("*.md"))


def list_clippings() -> list[Path]:
    """List all web clipping files."""
    if not CLIPPINGS_DIR.exists():
        return []
    return sorted(CLIPPINGS_DIR.glob("*.md"))


def list_support_learnings() -> list[Path]:
    """List all support learnings files (excludes _metadata.yml)."""
    if not SUPPORT_LEARNINGS_DIR.exists():
        return []
    return sorted(f for f in SUPPORT_LEARNINGS_DIR.glob("*.md"))


def list_internal_learnings() -> list[Path]:
    """List all internal learnings files (excludes _metadata.yml)."""
    if not INTERNAL_LEARNINGS_DIR.exists():
        return []
    return sorted(f for f in INTERNAL_LEARNINGS_DIR.glob("*.md"))


def list_docs() -> list[Path]:
    """List all doc files."""
    if not DOCS_DIR.exists():
        return []
    return sorted(DOCS_DIR.glob("*.md"))


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


# ── Index helpers ─────────────────────────────────────────────────────

def count_inbound_links(target: str, exclude_file: Path | None = None) -> int:
    """Count how many wiki articles link to a given target.

    Handles bare wikilinks: [[slug]] matches target "concepts/slug" or just "slug".
    """
    # Extract just the filename stem for matching bare links
    target_stem = Path(target).stem if "/" in target else target
    count = 0
    for article in list_wiki_articles():
        if article == exclude_file:
            continue
        content = article.read_text(encoding="utf-8")
        # Match both [[full/path]] and [[bare-slug]]
        if f"[[{target}]]" in content or f"[[{target_stem}]]" in content:
            count += 1
    return count


def get_article_word_count(path: Path) -> int:
    """Count words in an article, excluding YAML frontmatter."""
    content = path.read_text(encoding="utf-8")
    # Strip frontmatter
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            content = content[end + 3:]
    return len(content.split())


def build_index_entry(rel_path: str, summary: str, sources: str, updated: str) -> str:
    """Build a single index table row (fallback mode only)."""
    link = rel_path.replace(".md", "")
    return f"| [[{link}]] | {summary} | {sources} | {updated} |"
