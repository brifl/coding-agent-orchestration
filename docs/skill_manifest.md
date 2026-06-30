# Skill manifest format

Codex skills use `SKILL.md` with exactly two frontmatter fields:

- `name`: unique skill identifier
- `description`: concise trigger scope describing what the skill does and when to use it

Keep workflow instructions in the Markdown body. Put Codex UI metadata and tool
dependencies in `agents/openai.yaml`; keep bundle/version coordination in skill-set
or release metadata rather than expanding every skill manifest.

```markdown
---
name: vibe-loop
description: Run one deterministic Vibe dispatcher step and print the selected prompt body.
---

# Vibe Loop

Follow the workflow instructions here.
```
