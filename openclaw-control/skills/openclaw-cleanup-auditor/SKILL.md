---
name: openclaw-cleanup-auditor
description: Audit duplicate scripts, dead systemd units, drift between templates and deployed services, and cleanup candidates. Use before deleting or consolidating ops artifacts.
---

# OpenClaw Cleanup Auditor

- Inventory scripts, units, templates, and ownership.
- Mark items as keep, migrate, wrapper, or remove.
- Do not delete artifacts until replacements are validated.
- Prefer a smaller operator toolbelt over ad hoc helpers.
- Reference: `../references/operator-guidelines.md`
