Persistent Context Engine (PCE)


A deterministic, auditable memory system for long-running reasoning workflows.

🚧 Overview


The Persistent Context Engine (PCE) is a small, dependency-free Python subsystem that maintains reasoning continuity across long projects.

Unlike typical “AI memory” layers, PCE is:

100% deterministic

Fully auditable

Reversible

Embeddings-free

ML-free

Inspectable with a text editor



It stores interaction frames, compresses them with rule-based logic, and reconstructs a consistent “reasoning state” on demand.

Think SQLite for cognition — small, reliable, predictable.

✨ Features


Deterministic Memory Pipeline
Rule-based keyword extraction

Keyword frequency analysis

Sentence dedupe + compression

Append-only JSONL log

Recency-weighted retrieval

Stable scoring (no randomness)



Structured Memory Types
SemanticMemory — concepts, definitions, domain facts

ProceduralMemory — workflows, checklists, how-to steps

ProjectState — workstreams, constraints, pending tasks

Preferences — tone, style, user constraints

RecapFrame — timestamped interaction snapshot



Reasoning Reconstruction


PCE builds a unified context bundle including:

Project summary

Active workstream

User preferences

Known constraints

Recommended next steps

Supporting memory frames

📁 Project Structure
SCPE/
│
├── app.py                   # CLI interface
│
└── pce/
    ├── __init__.py
    ├── api.py               # Public façade
    ├── compression.py        # Deterministic text compression
    ├── retrieval.py          # Keyword retrieval + recency scoring
    ├── schema.py             # Memory dataclasses
    └── storage.py            # Append-only JSONL store


📦 Installation


Clone the repository:

git clone https://github.com/FoxhunterLabs/SCPE.git
cd SCPE
No external dependencies — runs on pure Python 3.8+.

🧪 CLI Usage


Run the CLI:

python app.py
Save a new interaction
python app.py save
You will be prompted to enter:

User message

Assistant/system message



End each with a . on its own line.



Load reconstructed context
python app.py load
Prints:

Project summary

Active workstream

User prefs

Constraints

Recommended next steps

Supporting frames



Search memory by keyword
python app.py search <keyword>


🧠 How It Works


1. Input → RecapFrame


Every interaction is distilled into a structured frame containing:

timestamp

key topics

distilled user intent

distilled system output

semantic + procedural memory

project state snapshot

user preferences

tags (tech, plan, meta, etc.)



2. Compression


Each frame is aggressively but deterministically compressed:

whitespace normalization

sentence dedupe

keyword extraction

max-length enforcement

list deduplication



3. Storage


Stored as append-only JSONL:

./memory/context.jsonl
Automatic pruning keeps last 300 frames.



4. Retrieval


Query pipeline:

tokenize query

keyword match

recency weighting

stable sort by score

return top N frames



5. Reconstruction


Frames are merged into a ContextBundle:

{
  "project_summary": "...",
  "active_workstream": "...",
  "user_prefs": {...},
  "known_constraints": [...],
  "recommended_next_steps": [...]
}
This serves as the “reasoning state” for a new session.

🛡 Philosophy


This engine is built for engineers who need:

predictable behavior

low-risk state persistence

autopsy-friendly logs

minimal complexity

no hidden probabilistic layers



It is not an LLM memory gimmick.

It is infrastructure.

🗺 Roadmap (optional)
HTTP microservice wrapper

Test harness for determinism

Optional export/import tools

Optional encryption at rest

📜 License


MIT
