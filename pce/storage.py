# pce/storage.py
from __future__ import annotations

import json
import os
from typing import List

from .schema import RecapFrame

MEMORY_DIR = os.path.join(".", "memory")
MEMORY_FILE = os.path.join(MEMORY_DIR, "context.jsonl")
MAX_FRAMES = 300


def _ensure_memory_dir() -> None:
"""
Ensure the memory directory exists.
"""
os.makedirs(MEMORY_DIR, exist_ok=True)


def write_frame(frame: RecapFrame) -> None:
"""
Append a single RecapFrame to the JSONL log and prune if necessary.

The log is append-only under normal operation; pruning rewrites the file
keeping only the most recent MAX_FRAMES frames.
"""
_ensure_memory_dir()
line = json.dumps(frame.to_dict(), sort_keys=True)
with open(MEMORY_FILE, "a", encoding="utf-8") as f:
f.write(line + "\n")

_prune_if_needed()


def load_all() -> List[RecapFrame]:
"""
Load all frames from the JSONL log, in chronological order.
"""
if not os.path.exists(MEMORY_FILE):
return []

frames: List[RecapFrame] = []
with open(MEMORY_FILE, "r", encoding="utf-8") as f:
for line in f:
line = line.strip()
if not line:
continue
try:
data = json.loads(line)
frames.append(RecapFrame.from_dict(data))
except json.JSONDecodeError:
# Corrupted line; skip but keep the rest.
continue
return frames


def _prune_if_needed() -> None:
"""
If the log has grown beyond MAX_FRAMES, keep only the most recent frames.

This is done by rewriting the file with the last MAX_FRAMES entries.
"""
frames = load_all()
if len(frames) <= MAX_FRAMES:
return

# Keep only the most recent MAX_FRAMES.
frames = frames[-MAX_FRAMES:]
_ensure_memory_dir()
with open(MEMORY_FILE, "w", encoding="utf-8") as f:
for frame in frames:
line = json.dumps(frame.to_dict(), sort_keys=True)
f.write(line + "\n")
