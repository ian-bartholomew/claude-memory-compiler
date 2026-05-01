# LLM Personal Knowledge Base (Archived)

> **This project has been consolidated into [lyt-assistant](https://github.com/ian-bartholomew/lyt-assistant).**
>
> All scripts, hooks, and functionality from this repo now live in the lyt-assistant Claude Code plugin. Install the plugin and everything works automatically — no separate repo needed.

## Migration

```bash
# Install the consolidated plugin
claude plugin marketplace add github:ian-bartholomew/lyt-assistant
claude plugin install lyt-assistant@ian-bartholomew-lyt-assistant

# Migrate state files
mkdir -p ~/.local/share/lyt-assistant
cp scripts/state.json ~/.local/share/lyt-assistant/
cp scripts/vault-config.json ~/.local/share/lyt-assistant/

# Remove old hooks from ~/.claude/settings.json
# (SessionStart, SessionEnd, PreCompact entries referencing claude-memory-compiler)
```

See [lyt-assistant INSTALL.md](https://github.com/ian-bartholomew/lyt-assistant/blob/main/INSTALL.md) for full details.
