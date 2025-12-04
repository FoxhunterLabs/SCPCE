# pce/retrieval.py
from __future__ import annotations

import re
from typing import List, Tuple

from .schema import ContextBundle, Preferences, RecapFrame, ProjectState
from .storage import load_all
from .compression import _tokenize # reuse deterministic tokenizer


def _score_frame(query_tokens: List[str], frame: RecapFrame, index: int, total: int) -> float:
"""
Deterministic scoring function combining keyword overlap and recency.

- query_tokens: normalized tokens from the query.
- index: position of the frame in chronological list.
- total: total number of frames.
"""
if not query_tokens:
# If there is no query, just score by recency.
recency_weight = 1.0 + (index / max(total - 1, 1))
return recency_weight

text = " ".join([
" ".join(frame.key_topics),
frame.distilled_user_intent,
frame.distilled_system_output,
frame.project_state.summary,
frame.raw_user_message,
]).lower()

# Keyword match count.
match_count = 0
for tok in query_tokens:
if not tok:
continue
if re.search(r"\b" + re.escape(tok) + r"\b", text):
match_count += 1

if match_count == 0:
return 0.0

# Recency factor: newer frames get slightly higher weight.
recency_weight = 1.0 + (index / max(total - 1, 1))
return match_count * recency_weight


def retrieve_relevant_frames(query: str = "", max_results: int = 12) -> List[RecapFrame]:
"""
Retrieve the most relevant frames for a query using deterministic scoring.
"""
frames = load_all()
if not frames:
return []

query_tokens = _tokenize(query) if query else []

scored: List[Tuple[float, RecapFrame]] = []
total = len(frames)
for idx, frame in enumerate(frames):
score = _score_frame(query_tokens, frame, idx, total)
if score <= 0.0 and query_tokens:
continue
scored.append((score, frame))

# Sort by score descending, then by timestamp (string compare is fine for ISO)
scored.sort(key=lambda sf: (-sf[0], sf[1].timestamp))

return [frame for score, frame in scored[:max_results] if score > 0.0 or not query_tokens]


def reconstruct_state(query: str = "", max_frames: int = 12) -> ContextBundle:
"""
Reconstruct a unified context bundle from the most relevant frames.
"""
frames = retrieve_relevant_frames(query=query, max_results=max_frames)
# If no frames match the query, fall back to the most recent few.
if not frames:
all_frames = load_all()
frames = all_frames[-max_frames:]

if not frames:
# Empty bundle.
empty_prefs = Preferences()
return ContextBundle(
project_summary="",
active_workstream="",
user_prefs=empty_prefs,
known_constraints=[],
recommended_next_steps=[],
supporting_frames=[],
)

# Use the most recent frame as the primary anchor.
primary = frames[-1]

# Project summary: prefer the latest non-empty project_state.summary,
# otherwise build one from key topics and distilled intent.
project_summary = ""
active_workstream = ""
pending_tasks: List[str] = []
constraints: List[str] = []
# Aggregate preferences.
style = ""
tone = ""
pref_constraints: List[str] = []
other_prefs = {}

for frame in frames:
ps: ProjectState = frame.project_state
if ps.summary:
project_summary = ps.summary
if ps.active_workstream:
active_workstream = ps.active_workstream
pending_tasks.extend(ps.pending_tasks)
constraints.extend(ps.constraints)

if frame.preferences.style:
style = frame.preferences.style
if frame.preferences.tone:
tone = frame.preferences.tone
pref_constraints.extend(frame.preferences.constraints)
for k, v in frame.preferences.other.items():
other_prefs[k] = v

if not project_summary:
# Fallback: synthesize from primary frame.
project_summary = primary.distilled_user_intent or " | ".join(primary.key_topics)

if not active_workstream:
active_workstream = primary.project_state.active_workstream

# Deduplicate lists while preserving order.
def dedup(values: List[str]) -> List[str]:
seen = set()
result: List[str] = []
for v in values:
vv = v.strip()
if not vv or vv in seen:
continue
seen.add(vv)
result.append(vv)
return result

pending_tasks = dedup(pending_tasks)
constraints = dedup(constraints)
pref_constraints = dedup(pref_constraints)

# Simple recommended-next-steps heuristic:
# - If we have pending_tasks, use the first few.
# - Otherwise, suggest continuing the active_workstream.
if pending_tasks:
recommended_next_steps = pending_tasks[:5]
else:
base = active_workstream or project_summary
if base:
recommended_next_steps = [f"Continue: {base}"]
else:
recommended_next_steps = []

user_prefs = Preferences(
style=style,
tone=tone,
constraints=pref_constraints,
other=other_prefs,
)

return ContextBundle(
project_summary=project_summary,
active_workstream=active_workstream,
user_prefs=user_prefs,
known_constraints=constraints,
recommended_next_steps=recommended_next_steps,
supporting_frames=frames,
)
