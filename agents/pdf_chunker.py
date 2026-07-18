# agents/pdf_chunker.py — Person A
# Chunks an uploaded PDF into sources and merges with web results.
# Skips silently if no PDF was uploaded.

import sys
from pathlib import Path
if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

import fitz  # PyMuPDF  # type: ignore[import]
from state import ResearchState, Source


CHUNK_SIZE = 3000    # characters per chunk
MAX_CHARS  = 12000   # cap total PDF text to keep latency low


def run_pdf_chunker(state: ResearchState) -> dict:
    if not state.get("pdf_bytes"):
        #return {}  # no PDF — skip silently, sources unchanged
        if not state.get("pdf_bytes"):
            return {"sources": state["sources"], "status": "pdf_chunker"}

    doc = fitz.open(stream=state["pdf_bytes"], filetype="pdf")
    full_text = "\n".join(page.get_text() for page in doc)
    capped     = full_text[:MAX_CHARS]

    chunks = [capped[i:i + CHUNK_SIZE] for i in range(0, len(capped), CHUNK_SIZE)]

    pdf_sources: list[Source] = [
        Source(
            id=f"pdf_{i}",
            origin="pdf",
            url="uploaded.pdf",
            title=f"Uploaded PDF — chunk {i + 1}",
            raw_text=chunk,
            summary="",
            claims=[],
        )
        for i, chunk in enumerate(chunks)
    ]

    # Treat web and PDF sources as equals in the merged pool
    return {
        "sources": state["sources"] + pdf_sources,
        "status": "pdf_chunker",
    }
