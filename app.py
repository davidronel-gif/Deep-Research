# app.py — Person C
# Streamlit UI with live agent status and contradiction view.
# Start with MOCK_MODE = True so you don't wait for backend.

import json
import time
import streamlit as st
import requests
import importlib
from types import ModuleType

from pdf_export import markdown_report_to_pdf

# sseclient can be installed as `sseclient-py`. Try to import it dynamically
# and fall back to None so static analyzers don't error at runtime.
try:
    sseclient = importlib.import_module("sseclient")  # type: ModuleType
except Exception:
    sseclient = None

API_URL   = "https://deep-research-backend-6p6m.onrender.com"
#API_URL   = "http://localhost:8000/research"
MOCK_MODE = False  # set True at hour 0, flip to False at hour 5

AGENTS = ["retriever", "pdf_chunker", "analyst", "critic", "report_builder"]
AGENT_META = {
    "retriever":      {"label": "Retriever",      "icon": ":material/travel_explore:", "detail": "Searching the web via Tavily"},
    "pdf_chunker":     {"label": "PDF chunker",    "icon": ":material/picture_as_pdf:", "detail": "Merging uploaded document sources"},
    "analyst":        {"label": "Analyst",        "icon": ":material/analytics:",      "detail": "Summarizing sources & extracting claims"},
    "critic":         {"label": "Critic",         "icon": ":material/fact_check:",     "detail": "Cross-checking claims for contradictions"},
    "report_builder": {"label": "Report builder", "icon": ":material/description:",    "detail": "Compiling the cited markdown report"},
}

MOCK_RESULT = {
    "report_markdown": """## Summary
Large language models trained with RLHF show strong performance on reasoning benchmarks,
but published accuracy figures vary significantly between papers.

## Key findings
- GPT-4 achieves between 86.4% and 90% on MMLU depending on evaluation setup [web_0, web_1]
- Chain-of-thought prompting improves performance by 10-15% on multi-step tasks [web_2]

## Contradictions & conflicts
- CONFLICT (confidence 85%): "GPT-4 achieves 90% on MMLU" [web_0] vs
  "GPT-4 achieves 86.4% on MMLU" [web_1] — Different evaluation protocols
  produce significantly different benchmark scores.

## Sources
1. [web_0] OpenAI GPT-4 Technical Report — https://openai.com/research/gpt-4
2. [web_1] Independent GPT-4 Evaluation — https://arxiv.org/abs/2303.12528
""",
    "sources": [
        {"id": "web_0", "origin": "web", "title": "OpenAI GPT-4 Technical Report", "url": "https://openai.com/research/gpt-4"},
        {"id": "web_1", "origin": "web", "title": "Independent GPT-4 Evaluation", "url": "https://arxiv.org/abs/2303.12528"},
    ],
    "contradictions": [
        {
            "source_a_id": "web_0",
            "source_b_id": "web_1",
            "claim_a": "GPT-4 achieves 90% accuracy on the MMLU benchmark",
            "claim_b": "GPT-4 achieves 86.4% accuracy on the MMLU benchmark",
            "confidence": 0.85,
            "explanation": "Different evaluation protocols produce significantly different scores.",
        }
    ],
}

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Deep Researcher",
    page_icon=":material/network_intelligence:",
    layout="wide",
)

# ── Session state ────────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None  # holds {report_markdown, sources, contradictions, elapsed}

# ── Sidebar — control panel ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### :material/network_intelligence: Deep Researcher")
    st.caption("Multi-agent research console")

    st.markdown("#### Research input")
    query = st.text_area(
        "Research question",
        placeholder="e.g. What are the accuracy benchmarks of GPT-4 vs Claude on MMLU?",
        height=110,
        label_visibility="collapsed",
    )
    pdf = st.file_uploader("Upload a paper (optional)", type="pdf")
    run = st.button("Run research", icon=":material/play_arrow:", type="primary", width="stretch")

    st.markdown("#### Pipeline")
    for a in AGENTS:
        meta = AGENT_META[a]
        st.markdown(f"{meta['icon']} &nbsp; {meta['label']}")

        if a == "report_builder":
            report_markdown = (st.session_state.get("result") or {}).get("report_markdown", "")
            st.download_button(
                "Download report",
                data=markdown_report_to_pdf(report_markdown) if report_markdown else b"",
                file_name="deep_researcher_report.pdf",
                mime="application/pdf",
                icon=":material/download:",
                disabled=not report_markdown,
                width="stretch",
            )

    st.caption("Powered by Claude · Tavily · LangGraph")

# ── Header / hero ────────────────────────────────────────────────────────────
st.markdown(
    '<h1 style="font-size: 3.375rem; font-weight: 700; margin: 0;">Multi-agent deep researcher</h1>',
    unsafe_allow_html=True,
)
st.caption("Ask a research question. Five specialized agents retrieve sources, extract claims, surface contradictions, and compile a cited report.")

status_row = st.empty()


def render_pipeline_row(active: str | None, done: set):
    """Draw the horizontal agent pipeline as status cards.

    Uses a single st.empty() placeholder so each redraw replaces the
    previous one instead of stacking new columns on top of old ones.
    """
    with status_row.container(horizontal=True):
        cols = st.columns(len(AGENTS))
        for col, a in zip(cols, AGENTS):
            meta = AGENT_META[a]
            with col:
                with st.container(border=True):
                    if a in done:
                        st.badge(meta["label"], icon=":material/check_circle:", color="green")
                    elif a == active:
                        st.badge(meta["label"], icon=":material/autorenew:", color="blue")
                    else:
                        st.badge(meta["label"], icon=":material/schedule:", color="gray")
                    st.caption(meta["detail"])

render_pipeline_row(
    active=None,
    done=set(AGENTS) if st.session_state.result else set(),
)

kpi_container = st.container()
report_container = st.container()
contradiction_container = st.container()


def render_report(result: dict):
    with report_container:
        st.markdown("#### Report")
        with st.container(border=True):
            st.markdown(
                result.get("report_markdown", "") or "_No report generated._",
                unsafe_allow_html=True,  # report includes our own <a id="src-N"> anchors for PDF citation jump-links
            )


def render_contradictions(contradictions: list):
    with contradiction_container:
        if not contradictions:
            return
        st.markdown("#### Contradictions detected")
        for c in contradictions:
            conf = int(c["confidence"] * 100)
            with st.expander(f"Conflict — confidence {conf}%", icon=":material/report:"):
                c1, c2 = st.columns(2)
                with c1:
                    st.error(f"**[{c['source_a_id']}]**\n\n{c['claim_a']}", icon=":material/article:")
                with c2:
                    st.warning(f"**[{c['source_b_id']}]**\n\n{c['claim_b']}", icon=":material/article:")
                st.caption(c["explanation"])


def render_kpis(sources: list, contradictions: list, elapsed: float):
    top_confidence = max((c["confidence"] for c in contradictions), default=None)
    with kpi_container:
        kpi_cols = st.columns(4)
        kpi_cols[0].metric("Confidence", f"{top_confidence:.0%}" if top_confidence is not None else "100%")
        kpi_cols[1].metric("Sources analyzed", len(sources))
        kpi_cols[2].metric("Contradictions found", len(contradictions))
        kpi_cols[3].metric("Time to report", f"{elapsed:.1f}s")


# ── Run research ──────────────────────────────────────────────────────────────
if run and query:
    start_time = time.time()

    if MOCK_MODE:
        for i, agent in enumerate(AGENTS):
            done = set(AGENTS[:i])
            render_pipeline_row(active=agent, done=done)
            time.sleep(0.6)
        render_pipeline_row(active=None, done=set(AGENTS))

        st.session_state.result = {
            "report_markdown": MOCK_RESULT["report_markdown"],
            "sources": MOCK_RESULT["sources"],
            "contradictions": MOCK_RESULT["contradictions"],
            "elapsed": time.time() - start_time,
        }

    else:
        if sseclient is None:
            st.error(
                "Missing dependency: please install sseclient (pip install sseclient-py) to stream events from the API.",
                icon=":material/error:",
            )
            render_pipeline_row(active=None, done=set())
            st.stop()

        data = {"query": query}
        files = {"pdf": (pdf.name, pdf.getvalue())} if pdf else {}
        final_sources = []
        final_contradictions = []
        final_report = ""

        with st.spinner("Running the research pipeline…"):
            with requests.post(API_URL, data=data, files=files, stream=True, timeout=300) as r:
                client = sseclient.SSEClient(r)
                for event in client.events():
                    payload = json.loads(event.data)
                    current = payload.get("status", "")
                    state = payload.get("state", {})

                    done = set(AGENTS[: AGENTS.index(current)]) if current in AGENTS else set()
                    render_pipeline_row(active=current if current in AGENTS else None, done=done)

                    if "sources" in state:
                        final_sources = state["sources"]
                    if "contradictions" in state:
                        final_contradictions = state["contradictions"]
                    if state.get("report_markdown"):
                        final_report = state["report_markdown"]

                    # "complete" is set inside the merged state's own status
                    # field (by report_builder), not the SSE top-level status
                    # (which is always the graph node name, e.g. "report_builder").
                    # Top-level "error" is the one literal exception from main.py.
                    if current == "error" or state.get("status") == "complete":
                        render_pipeline_row(active=None, done=set(AGENTS))
                        break

        st.session_state.result = {
            "report_markdown": final_report,
            "sources": final_sources,
            "contradictions": final_contradictions,
            "elapsed": time.time() - start_time,
        }

    # Sidebar (incl. the download button) is drawn before this block runs each
    # script pass, so it's rendering stale session_state. Rerun once now that
    # the result is stored so the sidebar redraws with the button enabled.
    st.rerun()

# ── Render last result (persists across reruns) ──────────────────────────────
if st.session_state.result:
    result = st.session_state.result
    render_kpis(result["sources"], result["contradictions"], result["elapsed"])
    render_report(result)
    render_contradictions(result["contradictions"])

# ── Eval summary — reads eval_results.json produced by run_evals.py ──────────
try:
    with open("eval_results.json") as f:
        eval_data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    eval_data = None

if not eval_data or not eval_data.get("cases"):
    st.markdown("#### Evaluation summary")
    st.caption("No eval results yet — run `python run_evals.py` to generate a score.")
else:
    total, maximum, pct = eval_data["total"], eval_data["maximum"], eval_data["percentage"]
    passed = pct >= 70
    status_label = "Pass" if passed else "Needs work"

    with st.expander(
        f"Evaluation summary — {total}/{maximum} ({pct:.0f}%) · "
        f"{':green' if passed else ':red'}[{status_label}]",
        icon=":material/check_circle:" if passed else ":material/error:",
    ):
        for case in eval_data["cases"]:
            score, max_score = case["score"], case["max"]
            c1, c2 = st.columns([4, 1])
            with c1:
                st.progress(
                    score / max_score if max_score else 0,
                    text=f"{case['id']} — {case['query']}",
                )
            with c2:
                st.markdown(f"**{score}/{max_score}** &nbsp;·&nbsp; {case['elapsed']}s")

# Run with: streamlit run app.py
