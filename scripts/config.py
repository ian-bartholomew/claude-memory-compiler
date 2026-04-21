"""Path constants and configuration for the personal knowledge base."""

import json
import os
from pathlib import Path
from datetime import datetime, timezone


# ── Compiler paths (where the code lives) ────────────────────────────
COMPILER_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = COMPILER_DIR / "scripts"
HOOKS_DIR = COMPILER_DIR / "hooks"
AGENTS_FILE = COMPILER_DIR / "AGENTS.md"
STATE_FILE = SCRIPTS_DIR / "state.json"
REPORTS_DIR = COMPILER_DIR / "reports"


# ── Vault resolution ─────────────────────────────────────────────────

def _resolve_vault_dir() -> Path:
    """Resolve the vault directory from env var, config file, or fallback.

    Resolution order:
    1. MEMORY_VAULT_DIR environment variable
    2. scripts/vault-config.json file
    3. Fallback to COMPILER_DIR (original single-repo layout)
    """
    # 1. Environment variable
    env_val = os.environ.get("MEMORY_VAULT_DIR", "").strip()
    if env_val:
        return Path(env_val).expanduser().resolve()

    # 2. Config file
    config_file = SCRIPTS_DIR / "vault-config.json"
    if config_file.exists():
        try:
            data = json.loads(config_file.read_text(encoding="utf-8"))
            vault_path = data.get("vault_dir", "").strip()
            if vault_path:
                return Path(vault_path).expanduser().resolve()
        except (json.JSONDecodeError, OSError):
            pass

    # 3. Fallback to compiler dir (original layout)
    return COMPILER_DIR


VAULT_DIR = _resolve_vault_dir()


# ── Vault paths (where the data lives) ───────────────────────────────

# Wiki structure — adapts to vault layout
# External vault: wiki/ with _index.md, _log.md, _indexes/
# Fallback (no vault configured): knowledge/ with index.md, log.md
_is_external_vault = VAULT_DIR != COMPILER_DIR

if _is_external_vault:
    # External vault uses the Karpathy three-layer architecture:
    #   raw/   (source)  →  wiki/  (compiled)  →  projects/  (active work)
    # Daily conversation logs are raw source material, so they go in raw/daily/.
    DAILY_DIR = VAULT_DIR / "raw" / "daily"
    WIKI_DIR = VAULT_DIR / "wiki"
    INDEX_FILE = WIKI_DIR / "_index.md"
    LOG_FILE = WIKI_DIR / "_log.md"
else:
    DAILY_DIR = VAULT_DIR / "daily"
    WIKI_DIR = VAULT_DIR / "knowledge"
    INDEX_FILE = WIKI_DIR / "index.md"
    LOG_FILE = WIKI_DIR / "log.md"

CONCEPTS_DIR = WIKI_DIR / "concepts"
GUIDES_DIR = WIKI_DIR / "guides"
COMPANY_DIR = WIKI_DIR / "company"
LEARNING_DIR = WIKI_DIR / "learning"
QA_DIR = WIKI_DIR / "qa"
CONNECTIONS_DIR = WIKI_DIR / "connections"
INDEXES_DIR = WIKI_DIR / "_indexes"

# Article subdirectories to scan — external vault has more folders
if _is_external_vault:
    ARTICLE_SUBDIRS = [CONCEPTS_DIR, GUIDES_DIR, COMPANY_DIR, LEARNING_DIR, QA_DIR]
else:
    ARTICLE_SUBDIRS = [CONCEPTS_DIR, CONNECTIONS_DIR, QA_DIR]

# ── Timezone ───────────────────────────────────────────────────────────
TIMEZONE = "America/Chicago"


def now_iso() -> str:
    """Current time in ISO 8601 format."""
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def today_iso() -> str:
    """Current date in ISO 8601 format."""
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
