# pce/compression.py
from __future__ import annotations

import re
from collections import Counter
from typing import Iterable, List, Tuple

from .schema import RecapFrame

# A small, explicit list of common English stopwords used for keyword extraction.
_STOPWORDS = {
"the", "and", "a", "an", "of", "to", "in", "for", "on", "at",
"is", "are", "was", "were", "be", "been", "with", "as", "by",
"or", "if", "then", "so", "we", "i", "you", "it", "that", "this",
"but", "from", "our", "their", "they", "them", "my", "your",
}


def _tokenize(text: str) -> List[str]:
"""
Deterministic tokenizer: lowercase, split on non-word characters.
"""
text = text.lower()
tokens = re.split(r"[^a-z0-9_]+", text)
return [t for t in tokens if t]


def extract_keywords(texts: Iterable[str], max_keywords: int = 10) -> List[str]:
"""
Frequency-based keyword extractor.

- Tokenizes deterministically.
- Removes a small set of stopwords.
- Returns the most frequent terms, stable-sorted by frequency then alphabetically.
"""
counter: Counter = Counter()
for text in texts:
for tok in _tokenize(text):
if tok in _STOPWORDS:
continue
counter[tok] += 1

if not counter:
return []

# Sort by (-freq, token) to get deterministic ordering.
items: List[Tuple[str, int]] = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
return [token for token, _ in items[:max_keywords]]


def compress_text(text: str, max_chars: int = 600) -> str:
"""
Lightweight, fully deterministic compression:

- Strips excessive whitespace.
- Deduplicates sentences.
- Keeps sentences in original order.
- Enforces a max character length by truncation at a boundary.
"""
# Normalize whitespace.
cleaned = " ".join(text.strip().split())
if not cleaned:
return ""

# Split into sentences on '.', '?', '!'. Keep delimiters.
parts = re.split(r"([.!?])", cleaned)
sentences: List[str] = []
current = ""
for part in parts:
if not part:
continue
current += part
if part in ".!?":
sentence = current.strip()
if sentence:
sentences.append(sentence)
current = ""
if current:
sentences.append(current.strip())

# Deduplicate sentences while preserving order.
seen = set()
unique_sentences: List[str] = []
for s in sentences:
if s in seen:
continue
seen.add(s)
unique_sentences.append(s)

result = " ".join(unique_sentences)
if len(result) <= max_chars:
return result
# Truncate at last space before max_chars if possible.
cut = result.rfind(" ", 0, max_chars)
if cut == -1:
return result[:max_chars]
return result[:cut].rstrip()


def compress_frame(frame: RecapFrame, max_text_chars: int = 600) -> RecapFrame:
"""
Apply deterministic compression rules to a RecapFrame.

- Compresses textual fields.
- Refreshes key_topics from all text fields.
- Ensures tags are deduplicated and stable-sorted.
"""
# Compress primary text fields.
frame.distilled_user_intent = compress_text(frame.distilled_user_intent, max_chars=max_text_chars)
frame.distilled_system_output = compress_text(frame.distilled_system_output, max_chars=max_text_chars)
frame.raw_user_message = compress_text(frame.raw_user_message, max_chars=max_text_chars)
frame.raw_assistant_message = compress_text(frame.raw_assistant_message, max_chars=max_text_chars)

# Rebuild key_topics using frequency-based keyword extraction.
all_text = [
frame.distilled_user_intent,
frame.distilled_system_output,
frame.semantic.notes,
frame.project_state.summary,
frame.raw_user_message,
frame.raw_assistant_message,
]
frame.key_topics = extract_keywords(all_text, max_keywords=12)

# Deduplicate and stable sort tags.
seen = set()
deduped_tags: List[str] = []
for tag in frame.tags:
t = tag.strip().lower()
if not t or t in seen:
continue
seen.add(t)
deduped_tags.append(t)
frame.tags = sorted(deduped_tags)

# Deduplicate concepts, workflows, pending tasks, constraints.
def dedup_list(values: List[str]) -> List[str]:
seen_local = set()
result: List[str] = []
for v in values:
vv = v.strip()
if not vv or vv in seen_local:
continue
seen_local.add(vv)
result.append(vv)
return result

frame.semantic.concepts = dedup_list(frame.semantic.concepts)
frame.procedural.workflows = dedup_list(frame.procedural.workflows)
frame.procedural.checklists = dedup_list(frame.procedural.checklists)
frame.project_state.pending_tasks = dedup_list(frame.project_state.pending_tasks)
frame.project_state.constraints = dedup_list(frame.project_state.constraints)
frame.preferences.constraints = dedup_list(frame.preferences.constraints)

return frame
