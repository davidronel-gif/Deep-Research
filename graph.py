# graph.py — LangGraph state machine
# Person A owns this. Build after state.py is agreed.

from langgraph.graph import StateGraph, END
from state import ResearchState
from agents.retriever import run_retriever
from agents.pdf_chunker import run_pdf_chunker
from agents.analyst import run_analyst
from agents.critic import run_critic
from agents.report_builder import run_report_builder


def build_graph():
    g = StateGraph(ResearchState)

    g.add_node("retriever",      run_retriever)
    g.add_node("pdf_chunker",    run_pdf_chunker)
    g.add_node("analyst",        run_analyst)
    g.add_node("critic",         run_critic)
    g.add_node("report_builder", run_report_builder)

    # Sequential flow — debuggable within 12hrs
    # Retriever and pdf_chunker both feed into analyst via merged source pool
    g.set_entry_point("retriever")
    g.add_edge("retriever",      "pdf_chunker")
    g.add_edge("pdf_chunker",    "analyst")
    g.add_edge("analyst",        "critic")
    g.add_edge("critic",         "report_builder")
    g.add_edge("report_builder", END)

    return g.compile()
