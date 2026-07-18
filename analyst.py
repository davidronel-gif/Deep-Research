# agents/analyst.py — Person A / Person B
# Summarises each source and extracts up to 5 falsifiable claims.

import os
import json
import anthropic
from state import ResearchState, Source

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

PROMPT = """You are a research analyst. Given the source text below, return JSON only — no preamble, no markdown fences.

{{
  "summary": "2-3 sentence factual summary",
  "claims": ["specific falsifiable claim 1", "specific falsifiable claim 2", ...]
}}

Rules:
- Extract up to 5 claims that are specific and falsifiable (numbers, dates, named results, direct assertions).
- Do not include vague statements like "researchers believe" or "some studies suggest".
- JSON only. Nothing else.

SOURCE TITLE: {title}
SOURCE TEXT:
{text}"""


def run_analyst(state: ResearchState) -> dict:
    updated_sources: list[Source] = []

    for src in state["sources"]:
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": PROMPT.format(title=src["title"], text=src["raw_text"]),
            }],
        )

        try:
            parsed = json.loads(msg.content[0].text)
        except json.JSONDecodeError:
            parsed = {"summary": msg.content[0].text, "claims": []}

        updated_sources.append({
            **src,
            "summary": parsed.get("summary", ""),
            "claims":  parsed.get("claims", []),
        })

    return {"sources": updated_sources, "status": "analyst"}
