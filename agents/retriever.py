# agents/retriever.py — Person A
# Pulls top 5 web results via Tavily for the user's query.

#import os
#from tavily import TavilyClient
#from state import ResearchState, Source
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Fix path so state.py is found when running standalone
if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

load_dotenv()

from tavily import TavilyClient
from state import ResearchState, Source

client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def run_retriever(state: ResearchState) -> dict:
    results = client.search(
        state["query"],
        max_results=5,
        include_raw_content=True,
    )

    sources: list[Source] = [
        Source(
            id=f"web_{i}",
            origin="web",
            url=r["url"],
            title=r["title"],
            #raw_text=r.get("raw_content", r["content"])[:4000],
            raw_text=(r.get("raw_content") or r.get("content") or "")[:4000],
            summary="",
            claims=[],
        )
        for i, r in enumerate(results["results"])
    ]

    return {"sources": sources, "status": "retriever"}

# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_state: ResearchState = {
        "query": "GPT-4 MMLU benchmark accuracy",
        "pdf_bytes": None,
        "sources": [],
        "contradictions": [],
        "report_markdown": "",
        "status": "",
        "error": None,
    }
    result = run_retriever(test_state)
    for s in result["sources"]:
        print(s["id"], "|", s["origin"], "|", s["title"][:60])