# agents/analyst.py — Person A / Person B
# Summarises each source and extracts up to 5 falsifiable claims.

import os
import re
import sys
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

load_dotenv()

from llm_provider import create_chat_completion
from state import ResearchState



PROMPT = """You are a research analyst. Given the source text below, return JSON only — no preamble, no markdown fences.

{{
  "summary": "2-3 sentence factual summary",
  "claims": ["specific falsifiable claim 1", "specific falsifiable claim 2"]
}}

Rules:
- Extract up to 3 claims that are specific and falsifiable (numbers, dates, named results, direct assertions).
- Do not include vague statements like "researchers believe" or "some studies suggest".
- JSON only. Nothing else.

SOURCE TITLE: {title}
SOURCE TEXT:
{text}"""


def _analyse_source(src: dict) -> dict:
    print(f"  Analysing: {src['id']} — {src['title'][:50]}")
    msg = create_chat_completion(
        model=os.getenv("ANALYST_MODEL", "anthropic/claude-haiku-4-5"),
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": PROMPT.format(
                title=src["title"],
                text=src["raw_text"]
            ),
        }],
    )

    try:
        raw = msg.content[0].text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        parsed = json.loads(raw.strip())
    except json.JSONDecodeError:
        print(f"  JSON parse failed for {src['id']} — using fallback")
        parsed = {"summary": msg.content[0].text, "claims": []}

    print(f"  Done: {src['id']} — {len(parsed.get('claims', []))} claims extracted")
    return {
        **src,
        "summary": parsed.get("summary", ""),
        "claims": parsed.get("claims", []),
    }


def run_analyst(state: ResearchState) -> dict:
    sources = state["sources"]

    # Each source is an independent, blocking LLM call — run them concurrently
    # instead of one at a time so wall-clock time stops scaling with source
    # count. Same model/prompt/tokens per source, so output quality is unchanged.
    with ThreadPoolExecutor(max_workers=min(8, len(sources) or 1)) as pool:
        updated_sources = list(pool.map(_analyse_source, sources))

    print(f"Analyst complete — {len(updated_sources)} sources processed")

    return {"sources": updated_sources, "status": "analyst"}
