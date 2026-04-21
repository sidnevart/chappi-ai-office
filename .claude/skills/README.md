# Claude Skills

This directory is a merged runtime skill set for this project:

- `superpowers` foundation skills from `obra/superpowers`
- local AI Office / OpenClaw control-plane skills

Sync sources with:

```bash
bash openclaw-control/scripts/oc-sync-claude-skills
```

The sync rule is:

- upstream `SKILL.md` becomes local `skill.md`
- sidecar markdown and helper files stay in the same skill directory
- local AI Office skill directories override same-named upstream directories
