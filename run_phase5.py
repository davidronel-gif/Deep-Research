# run_phase5.py — full pipeline test
from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
from graph import build_graph
from state import ResearchState

print("Building graph...")
graph = build_graph()

# ── Load test PDF if it exists ────────────────────────────────────────────────
pdf_path = Path("tests/Agentic-Design-Patterns.pdf")
pdf_bytes = pdf_path.read_bytes() if pdf_path.exists() else None

if pdf_bytes:
    print(f"PDF loaded: {pdf_path.name} ({len(pdf_bytes)//1024}kb)")
else:
    print("No PDF found — running web search only")

# ── State ─────────────────────────────────────────────────────────────────────
state: ResearchState = {
    "query": "What accuracy does GPT-4 achieve on the MMLU benchmark?",
    "pdf_bytes": pdf_bytes,
    "sources": [],
    "contradictions": [],
    "report_markdown": "",
    "status": "",
    "error": None,
}
# ── Stream ────────────────────────────────────────────────────────────────────
print("Running graph — streaming agent updates...\n")
for event in graph.stream(state, stream_mode="updates"):
    node, update = next(iter(event.items()))
    if update is None:
        print(f"[{node}] skipped — no output")
        continue
    print(f"[{node}] status={update.get('status')} | sources={len(update.get('sources', []))} | contradictions={len(update.get('contradictions', []))}")

# ── Final output ──────────────────────────────────────────────────────────────
print("\nInvoking graph for final output...")
final = graph.invoke(state)

print("\n--- REPORT PREVIEW ---")
print(final["report_markdown"][:500])

print("\n--- CONTRADICTIONS FOUND ---")
for c in final["contradictions"]:
    print(f"  [{c['confidence']:.0%}] {c['claim_a']} VS {c['claim_b']}")