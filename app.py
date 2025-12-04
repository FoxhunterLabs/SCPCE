# app.py
from __future__ import annotations

import sys
from typing import List

from pce import api


def _print_usage() -> None:
print("Persistent Context Engine CLI")
print("")
print("Usage:")
print(" python app.py save # enter a new interaction")
print(" python app.py load # print reconstructed context bundle")
print(" python app.py search <keyword> # search relevant memory")


def _read_block(label: str) -> str:
"""
Read a multi-line block from stdin, terminated by a single '.' line.
"""
print(f"Enter {label} (finish with a single '.' on its own line):")
lines: List[str] = []
while True:
try:
line = input()
except EOFError:
break
if line.strip() == ".":
break
lines.append(line)
return "\n".join(lines).strip()


def _cmd_save() -> None:
user_msg = _read_block("user message")
if not user_msg:
print("No user message entered.")
return

print("") # spacer
assistant_msg = _read_block("assistant message")
if not assistant_msg:
print("No assistant message entered.")
return

frame = api.save_context(user_msg, assistant_msg)
print("\nSaved frame:")
print(f" timestamp: {frame.timestamp}")
print(f" tags: {', '.join(frame.tags)}")
print(f" key_topics: {', '.join(frame.key_topics)}")
print(f" distilled_user_intent: {frame.distilled_user_intent}")
print(f" distilled_system_output: {frame.distilled_system_output}")


def _print_context_bundle(bundle) -> None:
print("=== Reconstructed Context ===")
print(f"Project summary : {bundle.project_summary}")
print(f"Active workstream : {bundle.active_workstream}")
print(f"Known constraints : {', '.join(bundle.known_constraints) if bundle.known_constraints else '(none)'}")
print(f"User style : {bundle.user_prefs.style or '(unspecified)'}")
print(f"User tone : {bundle.user_prefs.tone or '(unspecified)'}")
if bundle.user_prefs.constraints:
print("User constraints :")
for c in bundle.user_prefs.constraints:
print(f" - {c}")
if bundle.recommended_next_steps:
print("Recommended next steps:")
for step in bundle.recommended_next_steps:
print(f" - {step}")
print("")
print(f"Supporting frames: {len(bundle.supporting_frames)}")
for idx, frame in enumerate(bundle.supporting_frames, start=1):
print(f"--- Frame {idx} ---")
print(f"timestamp: {frame.timestamp}")
print(f"tags : {', '.join(frame.tags)}")
print(f"topics : {', '.join(frame.key_topics)}")
print(f"user : {frame.distilled_user_intent}")
print(f"assistant: {frame.distilled_system_output}")
print("")


def _cmd_load() -> None:
bundle = api.load_context()
_print_context_bundle(bundle)


def _cmd_search(query_tokens: List[str]) -> None:
query = " ".join(query_tokens)
if not query:
print("Provide a keyword to search.")
return
bundle = api.load_context(query=query)
_print_context_bundle(bundle)


def main(argv: List[str]) -> None:
if len(argv) < 2:
_print_usage()
return

cmd = argv[1].lower()
if cmd == "save":
_cmd_save()
elif cmd == "load":
_cmd_load()
elif cmd == "search":
_cmd_search(argv[2:])
else:
print(f"Unknown command: {cmd}")
_print_usage()


if __name__ == "__main__":
main(sys.argv)
