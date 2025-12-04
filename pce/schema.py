# pce/schema.py
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class SemanticMemory:
"""
Long-lived conceptual information extracted from interactions.

Example: important definitions, problem statements, domain facts.
"""
concepts: List[str] = field(default_factory=list)
notes: str = ""

def to_dict(self) -> Dict[str, Any]:
return asdict(self)

@staticmethod
def from_dict(data: Optional[Dict[str, Any]]) -> "SemanticMemory":
if not data:
return SemanticMemory()
return SemanticMemory(
concepts=list(data.get("concepts", [])),
notes=str(data.get("notes", "")),
)


@dataclass
class ProceduralMemory:
"""
Stable "how-to" knowledge: workflows, checklists, repeatable steps.
"""
workflows: List[str] = field(default_factory=list)
checklists: List[str] = field(default_factory=list)

def to_dict(self) -> Dict[str, Any]:
return asdict(self)

@staticmethod
def from_dict(data: Optional[Dict[str, Any]]) -> "ProceduralMemory":
if not data:
return ProceduralMemory()
return ProceduralMemory(
workflows=list(data.get("workflows", [])),
checklists=list(data.get("checklists", [])),
)


@dataclass
class ProjectState:
"""
Snapshot of the current project and active work.

This is deliberately compact so it can be reconstructed deterministically
from past frames without any ML.
"""
project_name: str = ""
summary: str = ""
active_workstream: str = ""
pending_tasks: List[str] = field(default_factory=list)
constraints: List[str] = field(default_factory=list)

def to_dict(self) -> Dict[str, Any]:
return asdict(self)

@staticmethod
def from_dict(data: Optional[Dict[str, Any]]) -> "ProjectState":
if not data:
return ProjectState()
return ProjectState(
project_name=str(data.get("project_name", "")),
summary=str(data.get("summary", "")),
active_workstream=str(data.get("active_workstream", "")),
pending_tasks=list(data.get("pending_tasks", [])),
constraints=list(data.get("constraints", [])),
)


@dataclass
class Preferences:
"""
User preferences that should persist across sessions.
"""
style: str = ""
tone: str = ""
constraints: List[str] = field(default_factory=list)
other: Dict[str, str] = field(default_factory=dict)

def to_dict(self) -> Dict[str, Any]:
return asdict(self)

@staticmethod
def from_dict(data: Optional[Dict[str, Any]]) -> "Preferences":
if not data:
return Preferences()
return Preferences(
style=str(data.get("style", "")),
tone=str(data.get("tone", "")),
constraints=list(data.get("constraints", [])),
other=dict(data.get("other", {})),
)


@dataclass
class RecapFrame:
"""
A single interaction recap that gets written to persistent storage.

This is the atomic unit of memory: one user+assistant exchange that has
already been compressed and tagged.
"""
timestamp: str
key_topics: List[str]
distilled_user_intent: str
distilled_system_output: str
tags: List[str]
semantic: SemanticMemory = field(default_factory=SemanticMemory)
procedural: ProceduralMemory = field(default_factory=ProceduralMemory)
project_state: ProjectState = field(default_factory=ProjectState)
preferences: Preferences = field(default_factory=Preferences)
# Keep original text around for auditability, but they may be truncated.
raw_user_message: str = ""
raw_assistant_message: str = ""

def to_dict(self) -> Dict[str, Any]:
"""
Serialize to a JSON-serializable dict.
"""
return {
"timestamp": self.timestamp,
"key_topics": list(self.key_topics),
"distilled_user_intent": self.distilled_user_intent,
"distilled_system_output": self.distilled_system_output,
"tags": list(self.tags),
"semantic": self.semantic.to_dict(),
"procedural": self.procedural.to_dict(),
"project_state": self.project_state.to_dict(),
"preferences": self.preferences.to_dict(),
"raw_user_message": self.raw_user_message,
"raw_assistant_message": self.raw_assistant_message,
}

@staticmethod
def from_dict(data: Dict[str, Any]) -> "RecapFrame":
"""
Reconstruct a RecapFrame from a dict that was produced by to_dict().
"""
return RecapFrame(
timestamp=str(data.get("timestamp", "")),
key_topics=list(data.get("key_topics", [])),
distilled_user_intent=str(data.get("distilled_user_intent", "")),
distilled_system_output=str(data.get("distilled_system_output", "")),
tags=list(data.get("tags", [])),
semantic=SemanticMemory.from_dict(data.get("semantic")),
procedural=ProceduralMemory.from_dict(data.get("procedural")),
project_state=ProjectState.from_dict(data.get("project_state")),
preferences=Preferences.from_dict(data.get("preferences")),
raw_user_message=str(data.get("raw_user_message", "")),
raw_assistant_message=str(data.get("raw_assistant_message", "")),
)


@dataclass
class ContextBundle:
"""
Unified reconstructed context used by the next session.

This is derived deterministically from stored RecapFrames.
"""
project_summary: str
active_workstream: str
user_prefs: Preferences
known_constraints: List[str]
recommended_next_steps: List[str]
supporting_frames: List[RecapFrame]

def to_dict(self) -> Dict[str, Any]:
return {
"project_summary": self.project_summary,
"active_workstream": self.active_workstream,
"user_prefs": self.user_prefs.to_dict(),
"known_constraints": list(self.known_constraints),
"recommended_next_steps": list(self.recommended_next_steps),
"supporting_frames": [f.to_dict() for f in self.supporting_frames],
}
