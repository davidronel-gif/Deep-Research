# agents/report_builder.py — Person B
# Compiles analyst summaries + critic findings into a structured markdown report.

import os
import anthropic
from state import ResearchState

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

REPORT_PROMPT = """You are a research report writer. Write a structured, cited report based on the sources and analysis below.

RESEARCH QUESTION: {query}

SOURCES AND SUMMARIES:
{sources_block}

CONTRADICTIONS DETECTED:
{contradictions_block}

Write the report using exactly these markdown sections:

## Summary
A concise 3-4 sentence answer to the research question.

## Key findings
Bullet points of the most important findings, citing sources as [web_0], [pdf_1] etc.

## Contradictions & conflicts
List each detected contradiction clearly, naming the sources that disagree and what the disagreement is.
If none were detected, state that explicitly.

## Sources
Numbered list of all sources with title and URL.

Be precise, factual, and neutral. Do not add findings not present in the sources."""


def run_report_builder(state: ResearchState) -> dict:
    sources_block = "\n\n".join(
        f"[{s['id']}] {s['title']} ({s['url']})\n{s['summary']}"
        for s in state["sources"]
    )

    if state["contradictions"]:
        contradictions_block = "\n".join(
            f"- CONFLICT (confidence {c['confidence']:.0%}): "
            f"\"{c['claim_a']}\" [{c['source_a_id']}] vs "
            f"\"{c['claim_b']}\" [{c['source_b_id']}] — {c['explanation']}"
            for c in state["contradictions"]
        )
    else:
        contradictions_block = "No direct factual contradictions detected across sources."

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": REPORT_PROMPT.format(
                query=state["query"],
                sources_block=sources_block,
                contradictions_block=contradictions_block,
            ),
        }],
    )

    return {"report_markdown": msg.content[0].text, "status": "complete"}
