# AGENTS.md — Рабочее пространство AI Office

This folder is home. Treat it that way.

## Every Session

Before doing anything else:

1. Read `SOUL.md` — this is who you are
2. Read `USER.md` — this is who you're helping
3. Read `memory/YYYY-MM-DD.md` (today + yesterday) for recent context
4. **If in MAIN SESSION** (direct chat with your human): Also read `MEMORY.md`

Don't ask permission. Just do it.

## Memory

You wake up fresh each session. These files are your continuity:

- **Daily notes:** `memory/YYYY-MM-DD.md` — raw logs of what happened
- **Long-term:** `MEMORY.md` — your curated memories, like a human's long-term memory

Write what matters. Decisions, context, things to remember.

### Memory Rules

- **ONLY load MEMORY.md in main session** (direct chats with your human)
- **DO NOT load in shared contexts** (group chats, sessions with other people)
- If you want to remember something → WRITE IT TO A FILE (mental notes don't survive restarts)

## Safety

- Don't exfiltrate private data. Ever.
- Don't run destructive commands without asking.
- When in doubt, ask.

## External vs Internal

**Safe to do freely:**
- Read files, explore, organize, learn
- Search the web, check calendars
- Work within this workspace

**Ask first:**
- Sending emails, public posts
- Anything that leaves the machine

## Group Chats

In group chats: participate, don't dominate. Respond when directly asked or when you add genuine value. Stay silent otherwise.

---

## Knowledge Base (Postgres)

You have a persistent structured KB on the VPS.

**Connection:**
```bash
PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST:-localhost} -p 5432 -U postgres -d ai_office
```

**When to save to KB:**

| Save when... | Table |
|--------------|-------|
| User states a fact about themselves | `profile_memory` |
| User says "запомни", "сохрани" | `notes` |
| User shares a URL | `links` |
| Research report complete | `research_reports` |
| Task created/completed | `tasks` |
| Repo analyzed | `repo_context` |

**Quick save (use exec tool):**

```bash
# Save note
PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST:-localhost} -p 5432 -U postgres -d ai_office -c \
  "INSERT INTO notes (content, tags, source) VALUES ('<content>', ARRAY['<tag>'], 'telegram');"

# Save task
PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST:-localhost} -p 5432 -U postgres -d ai_office -c \
  "INSERT INTO tasks (title, priority) VALUES ('<title>', 'normal');"

# Query KB
PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST:-localhost} -p 5432 -U postgres -d ai_office -c \
  "SELECT content, created_at FROM notes ORDER BY created_at DESC LIMIT 5;"
```

---

## Mac Files Access (VPS → Mac)

When you need to read files from the user's Mac:

**File server URL:** `${MAC_FILES_URL}` (cloudflared tunnel; rotate on restart)
**Token:** stored in `MAC_FILESERVER_TOKEN` env var

```bash
# List projects
curl -s -H "X-Token: $MAC_FILESERVER_TOKEN" "${MAC_FILES_URL}/"

# Read a specific file
curl -s -H "X-Token: $MAC_FILESERVER_TOKEN" "${MAC_FILES_URL}/ai_office/plan.md"
```

**Note:** If 530 error, user must restart tunnel and update MAC_FILES_URL in /root/.env.

---

## MemPalace Long-Term Memory

MemPalace indexes the workspace for semantic search.

```bash
mempalace wake-up
mempalace search "<query>"
mempalace mine /root/.openclaw/workspace
mempalace status
```

Run `mempalace wake-up` at start of meaningful sessions. After workspace changes, run `mempalace mine`.

---

## Star Office UI — State Push

Push your current state to the observability dashboard:

```bash
# Starting a task
curl -s -X POST http://localhost:3000/set_state \
  -H 'Content-Type: application/json' \
  -d '{"state":"researching","detail":"<brief description>"}'

# Writing/editing
curl -s -X POST http://localhost:3000/set_state \
  -H 'Content-Type: application/json' \
  -d '{"state":"writing","detail":"<what you are writing>"}'

# Running commands
curl -s -X POST http://localhost:3000/set_state \
  -H 'Content-Type: application/json' \
  -d '{"state":"executing","detail":"<command>"}'

# Done / idle
curl -s -X POST http://localhost:3000/set_state \
  -H 'Content-Type: application/json' \
  -d '{"state":"idle","detail":"Ready"}'
```

Observability dashboard: http://${SERVER_IP}:3000

---

## Voice Messages (Telegram → Whisper → Text)

When a user sends a voice message in Telegram:

```bash
# Transcribe the audio file:
/opt/ai-office/mempalace-venv/bin/python3 /opt/ai-office/voice/transcribe.py <path_to_audio_file>
# Then process transcribed text as normal message
```

After transcription, confirm: `"🎙️ Понял: «<transcribed text>»"`

---

## Notifications

After completing or failing any significant task:

```bash
# Success
python3 /opt/ai-office/notify/notify.py success "Задача выполнена: <summary>"

# Failure
python3 /opt/ai-office/notify/notify.py failure "Ошибка: <what failed>"

# Info update
python3 /opt/ai-office/notify/notify.py info "Статус: <brief update>"
```

---

## Tools

Skills provide your tools. When you need one, check its `SKILL.md`. Keep local notes in `TOOLS.md`.

## Make It Yours

This is a starting point. Add your own conventions and rules as you figure out what works.
