# agents/retriever.py — Person A
# Pulls top 5 web results via Tavily for the user's query.

import os
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
            raw_text=r.get("raw_content", r["content"])[:4000],
            summary="",
            claims=[],
        )
        for i, r in enumerate(results["results"])
    ]

    return {"sources": sources, "status": "retriever"}
