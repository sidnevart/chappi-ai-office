import json
import os

AGENTS = [
    ("research-orchestrator", "medium", "Маршрутизатор исследовательских запросов. Принимает запрос от пользователя, проводит intake-интервью, выбирает нужного агента-исполнителя, отслеживает статус."),
    ("scout-monitor", "light", "Скаут и монитор источников. Сканирует TechCrunch, Crunchbase, Dealroom, Sifted, YC, VC портфели. Находит кандидатов на инвестиции и партнерства."),
    ("company-dossier-analyst", "heavy", "Аналитик компаний. Строит полное досье: бизнес-модель, продукт, команда, финансы, рынок, конкуренты, трекшн. Использует открытые источники."),
    ("russia-market-analyst", "heavy", "Аналитик российского рынка. Оценивает transferability бизнеса в РФ: регуляторика, аналоги, платежеспособность, логистика, нюансы локального рынка."),
    ("investor-lens", "medium", "Инвесторский взгляд. Оценивает привлекательность компании для инвестора: round dynamics, TAM, moat, team pedigree, signal. Выдает скор /100."),
    ("operator-lens", "medium", "Операторский взгляд. Оценивает привлекательность для оператора: сложность запуска, юнит-экономика, найм, юридические риски, time-to-market. Скор /100."),
    ("feature-brainstormer", "medium", "Генератор фич. На основе досье и анализа рынка генерирует killer features для российской адаптации продукта. Фокус на реальные боли пользователей."),
    ("deliverables-architect", "heavy", "Архитектор выходных артефактов. Создает polished outputs: мемо, презентации, брифы, спеки. Русский язык, бизнес-стиль, источники под каждым фактом."),
    ("memory-librarian", "light", "Библиотекарь памяти. Обновляет MEMORY.md, граф знаний, векторное хранилище. Следит за связями между компаниями, фондами, рынками, гипотезами."),
]

BASE = "/root/.openclaw"

for agent_id, model, desc in AGENTS:
    ws = f"{BASE}/workspaces/{agent_id}"
    os.makedirs(ws, exist_ok=True)
    os.makedirs(f"{ws}/memory", exist_ok=True)

    # IDENTITY.md
    with open(f"{ws}/IDENTITY.md", "w") as f:
        f.write(f"---\nname: {agent_id}\ndescription: {desc}\nmodel: {model}\n---\n\n# {agent_id}\n\n{desc}\n\n## Модель\n\nИспользует псевдоним `{model}`.\n")

    # AGENTS.md
    with open(f"{ws}/AGENTS.md", "w") as f:
        f.write(f"# Инструкции агента: {agent_id}\n\n{desc}\n\n## Принципы работы\n\n- Действуй методично и последовательно\n- Сохраняй все промежуточные результаты в файлы\n- Используй доступные инструменты (Read, Edit, Write, Bash, WebSearch, WebFetch)\n- При сомнениях — указывай это как открытый вопрос\n- Всегда приводи источники данных\n\n## Формат выхода\n\nРусский язык, бизнес-стиль, без воды и маркетинговой болтовни.\n")

    # SKILLS.md
    with open(f"{ws}/SKILLS.md", "w") as f:
        f.write(f"# Навыки агента: {agent_id}\n\n## Обязательные\n\n- startup-research — конвейер DISCOVER → ANALYZE → RELATE → REPORT\n- task-manage — управление задачами в БД\n- proactive-main — проактивное поведение\n\n## Опциональные\n\n- research-cog — структурированный ресерч\n- slides-cog — генерация презентаций\n- vector-memory-hack — векторная память\n- graphiti — граф знаний\n- ru-business-writing — русский бизнес-стиль\n")

print("Created", len(AGENTS), "agent workspaces")

# Update openclaw.json
with open(f"{BASE}/openclaw.json", "r") as f:
    cfg = json.load(f)

existing_ids = {a["id"] for a in cfg["agents"]["list"]}
for agent_id, model, desc in AGENTS:
    if agent_id in existing_ids:
        continue
    cfg["agents"]["list"].append({
        "id": agent_id,
        "name": agent_id,
        "workspace": f"/root/.openclaw/workspaces/{agent_id}",
        "agentDir": f"/root/.openclaw/agents/{agent_id}/agent",
        "model": model
    })

with open(f"{BASE}/openclaw.json", "w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

print("Registered in openclaw.json")
