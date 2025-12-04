# pce/api.py
from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from .schema import (
RecapFrame,
SemanticMemory,
ProceduralMemory,
ProjectState,
Preferences,
ContextBundle,
)
from .compression import compress_frame, extract_keywords, compress_text
from .storage import write_frame
from .retrieval import reconstruct_state


def _classify_tags(user_msg: str, assistant_msg: str) -> List[str]:
"""
Rule-based tagging of the interaction.

Rules:
- if technical → 'tech'
- if planning → 'plan'
- if reflective/meta → 'meta'
"""
text = f"{user_msg} {assistant_msg}".lower()
tags: List[str] = []
if any(k in text for k in ["code", "api", "schema", "algorithm", "implementation", "stack", "bug"]):
tags.append("tech")
if any(k in text for k in ["plan", "roadmap", "milestone", "schedule", "timeline", "next steps"]):
tags.append("plan")
if any(k in text for k in ["think", "reflect", "meta", "why", "philosophy", "epistemology"]):
tags.append("meta")
if not tags:
tags.append("general")
return tags


def _distill_intent(user_msg: str) -> str:
"""
Deterministic intent distillation: compress user message.
"""
return compress_text(user_msg, max_chars=400)


def _distill_output(assistant_msg: str) -> str:
"""
Deterministic system-output distillation.
"""
return compress_text(assistant_msg, max_chars=400)


def _extract_semantic(user_msg: str, assistant_msg: str) -> SemanticMemory:
"""
Lightweight semantic extraction: treat the assistant response as notes,
keyed by high-signal topics.
"""
notes = compress_text(assistant_msg, max_chars=400)
topics = extract_keywords([user_msg, assistant_msg], max_keywords=8)
return SemanticMemory(concepts=topics, notes=notes)


def _extract_procedural(user_msg: str, assistant_msg: str) -> ProceduralMemory:
"""
Extract simple procedural hints by looking for bullet-like patterns or
step keywords; intentionally basic and deterministic.
"""
combined = f"{user_msg}\n{assistant_msg}"
lines = [ln.strip("-*• \t") for ln in combined.splitlines()]
workflows: List[str] = []
for ln in lines:
lower = ln.lower()
if any(lower.startswith(prefix) for prefix in ("step ", "1.", "2.", "3.", "first", "second", "third")):
workflows.append(ln)
return ProceduralMemory(workflows=workflows, checklists=[])


def _extract_project_state(user_msg: str, assistant_msg: str) -> ProjectState:
"""
Simple project-state extractor.

- Project name is guessed from explicit 'project:' or 'project name:' markers,
otherwise left empty and filled later by context reconstruction.
- Summary is the compressed user intent.
- Active workstream is estimated from user language like 'currently', 'right now'.
"""
text = f"{user_msg}\n{assistant_msg}"
project_name = ""
for line in text.splitlines():
lower = line.lower()
if "project:" in lower:
after = line.split("project:", 1)[1].strip()
if after:
project_name = after
break
if "project name:" in lower:
after = line.split("project name:", 1)[1].strip()
if after:
project_name = after
break

summary = _distill_intent(user_msg)

active_workstream = ""
if "currently" in user_msg.lower() or "right now" in user_msg.lower():
# Simple heuristic: take the sentence containing 'currently' or 'right now'.
active_workstream = summary

return ProjectState(
project_name=project_name,
summary=summary,
active_workstream=active_workstream,
pending_tasks=[],
constraints=[],
)


def _extract_preferences(user_msg: str, assistant_msg: str) -> Preferences:
"""
Extract obvious, stable user preferences from the interaction text.
This is intentionally shallow and deterministic.
"""
text = f"{user_msg} {assistant_msg}".lower()
style = ""
tone = ""
constraints: List[str] = []
other: Dict[str, str] = {}

if "concise" in text or "short answer" in text:
style = "concise"
if "detailed" in text or "step-by-step" in text:
style = "detailed"
if "casual" in text:
tone = "casual"
if "formal" in text:
tone = "formal"

if "no code" in text:
constraints.append("avoid code unless requested")
if "no examples" in text:
constraints.append("avoid examples unless requested")

return Preferences(style=style, tone=tone, constraints=constraints, other=other)


def save_context(raw_user_msg: str, raw_assistant_msg: str) -> RecapFrame:
"""
Public API: create a RecapFrame from raw messages, compress it, and store it.

Returns the compressed frame for inspection.
"""
timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"

distilled_intent = _distill_intent(raw_user_msg)
distilled_output = _distill_output(raw_assistant_msg)
tags = _classify_tags(raw_user_msg, raw_assistant_msg)
semantic = _extract_semantic(raw_user_msg, raw_assistant_msg)
procedural = _extract_procedural(raw_user_msg, raw_assistant_msg)
project_state = _extract_project_state(raw_user_msg, raw_assistant_msg)
preferences = _extract_preferences(raw_user_msg, raw_assistant_msg)

key_topics = extract_keywords(
[raw_user_msg, raw_assistant_msg, semantic.notes, project_state.summary],
max_keywords=12,
)

frame = RecapFrame(
timestamp=timestamp,
key_topics=key_topics,
distilled_user_intent=distilled_intent,
distilled_system_output=distilled_output,
tags=tags,
semantic=semantic,
procedural=procedural,
project_state=project_state,
preferences=preferences,
raw_user_message=raw_user_msg,
raw_assistant_message=raw_assistant_msg,
)

compressed = compress_frame(frame)
write_frame(compressed)
return compressed


def load_context(query: str = "") -> ContextBundle:
"""
Public API: retrieve and reconstruct a context bundle for an optional query.
"""
return reconstruct_state(query=query, max_frames=12)


def summarize() -> ContextBundle:
"""
Public API: summarize the whole project history into a context bundle.
"""
return reconstruct_state(query="", max_frames=20)
