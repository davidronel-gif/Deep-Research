# app.py — Person C
# Streamlit UI with live agent status and contradiction view.
# Start with MOCK_MODE = True so you don't wait for backend.

import json
import streamlit as st
import requests
import sseclient

API_URL   = "http://localhost:8000/research"
MOCK_MODE = False  # set True at hour 0, flip to False at hour 5

AGENTS = ["retriever", "pdf_chunker", "analyst", "critic", "report_builder"]

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

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Deep Researcher", page_icon="🔬", layout="wide")
st.title("🔬 Multi-Agent Deep Researcher")
st.caption("AI/ML research · powered by Claude + Tavily · built with LangGraph")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Research input")
    query = st.text_area(
        "Research question",
        placeholder="e.g. What are the accuracy benchmarks of GPT-4 vs Claude on MMLU?",
        height=100,
    )
    pdf = st.file_uploader("Upload a paper (optional)", type="pdf")
    run = st.button("Run research", type="primary", use_container_width=True)
    st.divider()
    st.caption("Agents: Retriever → PDF chunker → Analyst → Critic → Report builder")

# ── Main area ─────────────────────────────────────────────────────────────────
if run and query:
    col_status, col_report = st.columns([1, 2])

    with col_status:
        st.subheader("Agent progress")
        step_slots = {a: st.empty() for a in AGENTS}
        for a in AGENTS:
            step_slots[a].markdown(f"⬜ `{a}`")

    with col_report:
        st.subheader("Report")
        report_slot       = st.empty()
        contradiction_slot = st.empty()

    def render_contradictions(contradictions):
        if not contradictions:
            return
        contradiction_slot.markdown("---")
        with contradiction_slot.container():
            st.markdown("### Contradictions detected")
            for c in contradictions:
                conf = int(c["confidence"] * 100)
                with st.expander(f"⚡ Conflict — confidence {conf}%"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.error(f"**[{c['source_a_id']}]**\n\n{c['claim_a']}")
                    with c2:
                        st.warning(f"**[{c['source_b_id']}]**\n\n{c['claim_b']}")
                    st.caption(c["explanation"])

    if MOCK_MODE:
        import time
        for i, agent in enumerate(AGENTS):
            for j, a in enumerate(AGENTS):
                icon = "✅" if j < i else ("🔄" if j == i else "⬜")
                step_slots[a].markdown(f"{icon} `{a}`")
            time.sleep(0.6)
        for a in AGENTS:
            step_slots[a].markdown(f"✅ `{a}`")
        report_slot.markdown(MOCK_RESULT["report_markdown"])
        render_contradictions(MOCK_RESULT["contradictions"])

    else:
        data   = {"query": query}
        files  = {"pdf": pdf.getvalue()} if pdf else {}
        final_contradictions = []

        with requests.post(API_URL, data=data, files=files, stream=True) as r:
            client = sseclient.SSEClient(r)
            for event in client.events():
                payload = json.loads(event.data)
                current = payload.get("status", "")
                state   = payload.get("state", {})

                for a in AGENTS:
                    done = AGENTS.index(a) < AGENTS.index(current) if current in AGENTS else False
                    icon = "✅" if done else ("🔄" if a == current else "⬜")
                    step_slots[a].markdown(f"{icon} `{a}`")

                if current == "complete" or "report_markdown" in state:
                    report_slot.markdown(state.get("report_markdown", ""))

                if "contradictions" in state:
                    final_contradictions = state["contradictions"]

                if current in ("complete", "error"):
                    for a in AGENTS:
                        step_slots[a].markdown(f"✅ `{a}`")
                    break

        render_contradictions(final_contradictions)

# Run with: streamlit run app.py
