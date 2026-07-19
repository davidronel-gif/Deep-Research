# Deep-Research
Deep Research Multi agent
# 🔎 Multi-Agent Deep Researcher

> An AI-powered multi-agent research system that autonomously searches the web, analyzes evidence, cross-checks facts, detects contradictions, and generates a fully cited research report with PDF export.


---

## Overview

Traditional AI assistants generate answers from a single prompt.

This project goes several steps further.

**Multi-Agent Deep Researcher** orchestrates five specialized AI agents that collaborate to perform end-to-end research similar to how a human research team would operate.

Instead of relying on one LLM call, the system:

- Searches authoritative web sources
- Incorporates uploaded research papers
- Extracts key findings
- Detects contradictory information
- Estimates confidence levels
- Produces a structured research report
- Exports the report as PDF

The result is a significantly more transparent and explainable research workflow.

---

# Features

### 🌐 Intelligent Web Research

Searches trusted web sources using Tavily Search API.

---

### 📄 PDF Knowledge Integration

Upload your own research papers.

The uploaded documents become part of the research context and are analyzed alongside online sources.

---

### 🤖 Multi-Agent Architecture

Instead of one AI doing everything, five specialized agents work together.

- Retriever
- PDF Chunker
- Analyst
- Critic
- Report Builder

Each agent has a clearly defined responsibility.

---

### 📊 Research Dashboard

Real-time visualization of:

- Current pipeline stage
- Number of sources analyzed
- Confidence score
- Contradictions found
- Time taken
- Research progress

---

### 📚 Evidence-Based Findings

Every major claim is backed by citations.

The report includes:

- Executive Summary
- Key Findings
- Evidence
- References

---

### ⚠ Contradiction Detection

The Critic Agent cross-checks extracted claims and surfaces conflicting information before the final report is generated.

---

### 📈 Confidence Scoring

The system estimates an overall confidence score based on evidence consistency and research completeness.

---

### 📄 PDF Export

Generate a professional research report that can be downloaded and shared.

---

# Demo

## Research Question

> What is LangGraph?

Pipeline execution:

```
Retriever
      ↓
PDF Chunker
      ↓
Analyst
      ↓
Critic
      ↓
Report Builder
```

Output:

- Summary
- Key Findings
- Sources
- Confidence Score
- Contradictions
- Final PDF

---

# Architecture

```
                    User Query
                         │
                         ▼
            ┌────────────────────────┐
            │     LangGraph Flow     │
            └────────────────────────┘
                         │
     ┌───────────────────┼───────────────────┐
     ▼                   ▼                   ▼

 Retriever         PDF Chunker         Uploaded PDFs
     │                   │
     └──────────────┬────┘
                    ▼
              Combined Context
                    │
                    ▼
             Analyst Agent
                    │
                    ▼
              Structured Claims
                    │
                    ▼
              Critic Agent
                    │
                    ▼
          Validated Research Data
                    │
                    ▼
          Report Builder Agent
                    │
                    ▼
     Markdown Report + PDF Export
```

---

# Multi-Agent Workflow

## 1. Retriever Agent

**Purpose**

Searches the web for authoritative information.

Responsibilities

- Query Tavily
- Retrieve relevant webpages
- Rank search results
- Collect citations

Output

```
List of trusted sources
```

---

## 2. PDF Chunker Agent

**Purpose**

Processes uploaded research papers.

Responsibilities

- Read PDF
- Split into chunks
- Prepare document context
- Merge with web research

Output

```
Document chunks
```

---

## 3. Analyst Agent

**Purpose**

Transforms raw information into structured knowledge.

Responsibilities

- Read all retrieved evidence
- Extract claims
- Summarize findings
- Produce key insights

Output

```
Summary
Key Findings
Evidence
```

---

## 4. Critic Agent

**Purpose**

Acts as a quality assurance reviewer.

Responsibilities

- Verify extracted claims
- Detect contradictions
- Cross-check evidence
- Estimate confidence

Output

```
Validated Findings

Confidence Score

Contradictions
```

---

## 5. Report Builder Agent

**Purpose**

Produces the final report.

Responsibilities

- Combine outputs from all agents
- Format report
- Generate citations
- Export PDF

Output

```
Markdown Report

PDF Report
```

---

# Project Structure

```
Deep-Research/

│
├── agents/
│   ├── retriever.py
│   ├── pdf_chunker.py
│   ├── analyst.py
│   ├── critic.py
│   └── report_builder.py
│
├── app.py
├── requirements.txt
├── README.md
│
├── assets/
│
├── reports/
│
└── ...
```

---

# Technology Stack

| Component | Technology |
|------------|------------|
| Language | Python |
| LLM | Claude |
| Orchestration | LangGraph |
| Search | Tavily |
| UI | Streamlit |
| PDF Processing | PyPDF / LangChain |
| Report Generation | Markdown + PDF |

---

# Research Pipeline

```
User Question

↓

Retriever searches web

↓

PDF Chunker processes uploaded papers

↓

Context merged

↓

Analyst extracts findings

↓

Critic validates findings

↓

Confidence calculated

↓

Report generated

↓

PDF exported
```

---

# User Interface

The application provides a clean research dashboard consisting of:

### Left Sidebar

- Research Question
- PDF Upload
- Run Research Button
- Pipeline Status
- Download Report

---

### Main Panel

Displays

- Agent progress
- Confidence
- Sources analyzed
- Contradictions
- Time taken
- Research Report

---

# Example Output

```
Confidence

100%

Sources Analyzed

9

Contradictions

0

Time

258 seconds
```

---

# Installation

Clone the repository

```bash
git clone https://github.com/username/Deep-Research.git

cd Deep-Research
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create

```
.env
```

Example

```
ANTHROPIC_API_KEY=

TAVILY_API_KEY=
```

---

# Running

```bash
streamlit run app.py
```

---

# Example Workflow

1. Enter a research question.

2. Optionally upload a PDF.

3. Click **Run Research**.

4. Watch each agent complete its task.

5. Review findings.

6. Download the PDF report.

---

# Why Multi-Agent?

Instead of relying on a single LLM prompt, this project separates research into specialized responsibilities.

Benefits include:

- Better reasoning
- Modular architecture
- Easier debugging
- Explainable workflow
- Improved maintainability
- Higher research quality

---

# Current Capabilities

✅ Multi-agent orchestration

✅ Web search

✅ PDF ingestion

✅ Research synthesis

✅ Confidence scoring

✅ Contradiction detection

✅ Citation generation

✅ PDF export

---

# Future Improvements

- Multi-source search providers
- Parallel agent execution
- Citation verification
- Knowledge graph generation
- Interactive source explorer
- Human-in-the-loop approval
- Streaming intermediate outputs
- Multi-language support
- RAG memory layer
- Research history

---

# Learning Objectives

This project demonstrates practical implementation of:

- Agentic AI Systems
- LangGraph Workflows
- LLM Orchestration
- AI Research Pipelines
- Retrieval-Augmented Generation (RAG)
- Multi-Agent Collaboration
- Evidence-Based AI
- Explainable AI Workflows

---

# Acknowledgements

Built using:

- LangGraph
- Claude
- Tavily Search
- Streamlit
- Python

---

# License

MIT License

Feel free to fork, improve, and build upon this project.