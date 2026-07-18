# state.py — shared by all agents
# Agree this schema before splitting work. Do not change field names mid-build.

from typing import TypedDict


class Source(TypedDict):
    id: str           # "web_0", "pdf_1" etc.
    origin: str       # "web" | "pdf"
    url: str          # URL or filename
    title: str
    raw_text: str
    summary: str      # filled by Analyst
    claims: list[str] # filled by Analyst


class Contradiction(TypedDict):
    source_a_id: str
    source_b_id: str
    claim_a: str
    claim_b: str
    confidence: float  # 0.0–1.0 from LLM judge
    explanation: str


class ResearchState(TypedDict):
    query: str
    pdf_bytes: bytes | None          # raw upload, None if no PDF
    sources: list[Source]            # populated by Retriever + PDF chunker
    contradictions: list[Contradiction]  # populated by Critic
    report_markdown: str             # populated by Report Builder
    status: str                      # current agent name — drives UI progress
    error: str | None
