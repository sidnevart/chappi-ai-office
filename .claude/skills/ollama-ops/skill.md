---
name: ollama-ops
description: >-
  Ollama model management for AI Office. Use when checking ollama status,
  signin state, pulling cloud models (qwen3.5:cloud, glm-5:cloud, kimi-k2.6:cloud),
  testing model tiers, troubleshooting ollama connectivity or API.
  Trigger phrases: "ollama", "pull model", "cloud models", "тир моделей",
  "протестируй модели", "ollama не запущен". 
  Do NOT use for: openclaw config (use openclaw-ops), general shell work.
tools: Bash, Read
model: sonnet
---

# Ollama Model Management

## 1. Check Service Status
```bash
curl -s http://localhost:11434/api/version && echo "" || echo "ollama API: not responding"
ollama list 2>/dev/null | head -20 || echo "ollama list failed"
```

## 2. Check Signin
```bash
ollama whoami 2>/dev/null || echo "Not signed in. Run: ollama signin"
```
If not signed in: cloud models will fail. Ask user to run `! ollama signin` in the terminal.

## 3. Pull Cloud Models (idempotent)
```bash
for model in "qwen3.5:cloud" "glm-5:cloud" "kimi-k2.6:cloud"; do
  if ollama list 2>/dev/null | grep -q "$model"; then
    echo "✅ $model already available"
  else
    echo "Pulling $model..."
    ollama pull "$model" && echo "✅ $model pulled" || echo "❌ $model pull failed"
  fi
done
```

## 4. Test All Tiers
```bash
echo "=== Testing Light Tier (qwen3.5:cloud) ==="
ollama run qwen3.5:cloud "Reply with exactly: OK-LIGHT" --nowordwrap 2>&1 | tail -3

echo "=== Testing Medium Tier (glm-5:cloud) ==="
ollama run glm-5:cloud "Reply with exactly: OK-MEDIUM" --nowordwrap 2>&1 | tail -3

echo "=== Testing Heavy Tier (kimi-k2.6:cloud) ==="
ollama run kimi-k2.6:cloud "Reply with exactly: OK-HEAVY" --nowordwrap 2>&1 | tail -3
```

## 5. Troubleshooting
- **Not running**: `ollama serve &` then retry
- **Port conflict**: `lsof -i:11434` to see what's using port
- **Signin required**: User must run `! ollama signin` (interactive)
- **Model not found**: Check `ollama list` and re-pull
- **Slow**: Cloud models need internet; check connectivity

## Output Format
After checks, report:
| Model | Status | Tier |
|-------|--------|------|
| qwen3.5:cloud | ✅/❌ | light |
| glm-5:cloud | ✅/❌ | medium |
| kimi-k2.6:cloud | ✅/❌ | heavy |
