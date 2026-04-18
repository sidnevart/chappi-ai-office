---
name: ai-office-discovery
description: >-
  AI Office environment discovery. Use at the start of any deployment session,
  when the user says "check what's installed", "start from scratch", "verify the
  environment", "что установлено", "начни с нуля", "проверь среду", or before
  any Phase 1-7 work. Runs systematic inspection of all components: binaries
  (openclaw/clawdbot), ollama status + signin, docker, postgres, node, open
  ports, existing configs. Never skip this step before deployment work.
  Do NOT use for: general Q&A, code editing, non-infra tasks.
tools: Bash, Read, Glob
model: sonnet
---

# AI Office — Environment Discovery

Run each group in order. Show results after each. Never skip groups.

## 1. OS & Shell
```bash
uname -a && sw_vers 2>/dev/null || cat /etc/os-release 2>/dev/null
echo "Shell: $SHELL"
```

## 2. Core Binaries
```bash
for bin in openclaw clawdbot ollama docker node psql python3 git curl; do
  path=$(which $bin 2>/dev/null)
  if [ -n "$path" ]; then
    ver=$($bin --version 2>/dev/null | head -1 || echo "?")
    echo "✅ $bin: $path | $ver"
  else
    echo "❌ $bin: not found"
  fi
done
```

## 3. Ollama Status
```bash
curl -s http://localhost:11434/api/version 2>/dev/null || echo "ollama API: not responding"
ollama list 2>/dev/null || echo "ollama list: failed (not running or not signed in)"
ollama whoami 2>/dev/null || echo "ollama: not signed in"
```

## 4. Config Directories
```bash
for dir in ~/.openclaw ~/.clawdbot ~/.ollama; do
  [ -d "$dir" ] && echo "✅ $dir exists:" && ls "$dir" | head -5 || echo "❌ $dir: not found"
done
```

## 5. Open Ports (relevant)
```bash
lsof -iTCP -sTCP:LISTEN -nP 2>/dev/null | grep -E ":(11434|8080|5432|3000|8443|4000) " || echo "none of interest found"
```

## 6. Docker
```bash
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "docker: not available"
```

## 7. Existing Project Files
```bash
ls -la /Users/artemsidnev/Documents/Projects/ai_office/
```

---

## Output Format

После всех проверок выдай сводную таблицу:

| Component | Status | Version / Notes |
|-----------|--------|-----------------|
| openclaw/clawdbot | ✅/❌ | ... |
| ollama | ✅/❌ | ... |
| ollama signin | ✅/❌ | ... |
| docker | ✅/❌ | ... |
| postgres | ✅/❌ | ... |
| node | ✅/❌ | ... |

Затем: **Execution Plan** — предложи следующий шаг по фазам (Phase 1, 2, ...) с учётом того что уже готово.
