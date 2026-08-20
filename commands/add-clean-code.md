---
description: Install the plugin's Clean Code Standards into the current project's CLAUDE.md without overwriting existing instructions.
allowed-tools: Bash(bash:*)
---

Run:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/add-clean-code.sh" "$PWD"
```

Report whether the standards were created, appended, already present, or blocked by a legacy section. If a legacy section is detected, do not overwrite it; explain that it needs a deliberate migration.
