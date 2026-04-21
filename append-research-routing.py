import os

path = "/root/.openclaw/workspace/AGENTS.md"

text = """
---

## 🔬 Research Pipeline Routing

When the user asks anything related to research, company analysis, startup discovery, market intelligence, or due diligence, you MUST spawn the **research-orchestrator** subagent using the Agent tool.

**Trigger phrases (spawn research-orchestrator):**
- "/research" or "хочу провести ресерч"
- "проанализируй компанию" or "досье на"
- "найди стартапы" or "founder research"
- "cron ресерч" or "запусти founder cron"
- "квартира" or "apartment search" (routes to apartment-cron path within orchestrator)
- Any research request with explicit company name or sector

**How to spawn:**
Use the Agent tool with subagent_type="general-purpose", to="research-orchestrator".

**Available research subagents (spawned by orchestrator, not by you directly):**
- scout-monitor — scans sources for candidates
- company-dossier-analyst — builds full dossiers
- russia-market-analyst — evaluates Russia market fit
- investor-lens — scores investor attractiveness /100
- operator-lens — scores operator attractiveness /100
- feature-brainstormer — generates killer features
- deliverables-architect — produces polished outputs
- memory-librarian — updates memory and knowledge graph

**Do NOT spawn these directly from main.** Always route through research-orchestrator.

**After research-orchestrator completes:**
- Read its output
- Summarize to user in Telegram
- Post digest to @chappi_ai_office_digest if it is a founder cron or significant finding
"""

with open(path, "a") as f:
    f.write(text)

print("Appended research routing to AGENTS.md")
