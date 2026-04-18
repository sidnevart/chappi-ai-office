---
sidebar_position: 7
title: Голосовые сообщения
---

# Настройка голосовых сообщений

## Установка faster-whisper на сервере

```bash
ssh root@ВАШ_IP

# Установить в существующее виртуальное окружение
/opt/ai-office/mempalace-venv/bin/pip install faster-whisper

# Создать папку
mkdir -p /opt/ai-office/voice
```

## Скрипт расшифровки

Создайте `/opt/ai-office/voice/transcribe.py`:

```python
#!/usr/bin/env python3
import sys
import os
from faster_whisper import WhisperModel

if len(sys.argv) < 2:
    print("Использование: transcribe.py <аудиофайл>", file=sys.stderr)
    sys.exit(1)

audio_file = sys.argv[1]
model_size = os.getenv("WHISPER_MODEL", "base")

model = WhisperModel(model_size, device="cpu", compute_type="int8")
segments, info = model.transcribe(audio_file, beam_size=5)
text = " ".join(s.text.strip() for s in segments).strip()
print(text)
```

```bash
chmod +x /opt/ai-office/voice/transcribe.py
```

## Тестирование

```bash
# Скачать тестовый аудиофайл и проверить
/opt/ai-office/mempalace-venv/bin/python3 /opt/ai-office/voice/transcribe.py /tmp/test.ogg
```

## Настройка в AGENTS.md

Инструкции для агента по обработке голосовых сообщений уже включены в шаблон `AGENTS.md` из этого репозитория. Скопируйте его на сервер согласно разделу «Настройка OpenClaw».

## Модели расшифровки

| Модель | Размер | Скорость | Точность |
|--------|--------|---------|---------|
| tiny | ~75 МБ | Очень быстро | Базовая |
| base | ~150 МБ | Быстро | Хорошая |
| small | ~500 МБ | Умеренно | Отличная |
| large-v3 | ~3 ГБ | Медленно | Наилучшая |

По умолчанию используется `base` — оптимальный баланс скорости и точности для обычных голосовых сообщений.
