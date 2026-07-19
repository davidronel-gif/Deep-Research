# agents/report_builder.py — Person B
# Compiles analyst summaries + critic findings into a structured markdown report.

import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from llm_provider import create_chat_completion
from state import ResearchState

load_dotenv()

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
Each claim must cite the specific source id(s) that support it — do not cite a source
for a claim it doesn't contain.

## Contradictions & conflicts
List each detected contradiction clearly, naming the sources that disagree and what the disagreement is.
If none were detected, state that explicitly.

Be precise, factual, and neutral. Do not add findings not present in the sources.
Do NOT write a "## Sources" section — it will be appended automatically."""


def _build_sources_section(sources: list[dict]) -> tuple[str, dict[str, str]]:
    """Deterministically render the Sources list from state, and map each
    source id to its 1-based footnote number so inline [id] tags can be
    turned into real links. Built from state, not the model's prose, so a
    citation always resolves to the exact source it names.

    PDF chunks share one underlying file, so they're collapsed into a single
    line (grouped by url) instead of one row per chunk — a reader only
    needs to know which file to open, not which internal chunk."""
    lines = ["## Sources"]
    id_to_number = {}
    seen_urls: dict[str, str] = {}  # url -> number, for collapsing pdf chunks
    number = 0
    for s in sources:
        if s["origin"] == "pdf" and s["url"] in seen_urls:
            id_to_number[s["id"]] = seen_urls[s["url"]]
            continue
        number += 1
        id_to_number[s["id"]] = str(number)
        anchor = f'<a id="src-{number}"></a>'
        if s["origin"] == "pdf":
            seen_urls[s["url"]] = str(number)
            lines.append(f"{number}. {anchor}{s['title']} (uploaded PDF)")
        else:
            lines.append(f"{number}. {anchor}{s['title']} — {s['url']}")
    return "\n".join(lines), id_to_number


def _linkify_citations(text: str, sources_by_id: dict[str, dict], id_to_number: dict[str, str]) -> str:
    """Turn every [web_0] / [pdf_1, web_2] tag the model wrote into a
    clickable link: web sources link straight to their URL, PDF sources
    (no browsable URL) link to their numbered entry in the Sources list
    instead. Unknown ids (hallucinated by the model) are left as plain
    text rather than linked, so a broken citation is visible instead of
    silently trusted."""

    def replace(match: re.Match) -> str:
        ids = [x.strip() for x in match.group(1).split(",")]
        rendered = []
        for sid in ids:
            src = sources_by_id.get(sid)
            number = id_to_number.get(sid)
            if not src or not number:
                rendered.append(f"[{sid}]")
            elif src["origin"] == "web":
                # Bold, bracketed Sources-list number, not the raw id —
                # readers know sources as "6.", not as "web_0".
                rendered.append(f"[**\\[{number}\\]**]({src['url']})")
            else:
                rendered.append(f"[**\\[{number}\\]**](#src-{number})")
        return ", ".join(rendered)

    return re.sub(r"\[([\w, ]+?)\]", replace, text)


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

    msg = create_chat_completion(
        model=os.getenv("REPORT_MODEL", "anthropic/claude-haiku-4-5"),
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

    body = msg.content[0].text
    # Drop any "## Sources" section the model wrote anyway — it's rebuilt
    # from state below so citations always resolve to the real source.
    body = re.split(r"\n##\s*Sources\b", body)[0].rstrip()

    sources_section, id_to_number = _build_sources_section(state["sources"])
    sources_by_id = {s["id"]: s for s in state["sources"]}
    body = _linkify_citations(body, sources_by_id, id_to_number)

    report_markdown = f"{body}\n\n{sources_section}\n"

    return {"report_markdown": report_markdown, "status": "complete"}
