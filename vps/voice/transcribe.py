#!/usr/bin/env python3
"""Транскрипция аудио через faster-whisper. Использование: python3 transcribe.py <audio_file>"""
import os
import sys
from faster_whisper import WhisperModel

model_name = os.environ.get("WHISPER_MODEL", "base")
model = WhisperModel(model_name, device="cpu", compute_type="int8")
segments, _ = model.transcribe(sys.argv[1])
print(" ".join(s.text for s in segments))
