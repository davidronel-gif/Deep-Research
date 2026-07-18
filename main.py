# main.py — Person A, build at hour 4
# Single FastAPI endpoint that streams agent status via SSE.

import json
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from graph import build_graph
from state import ResearchState

app = FastAPI(title="Deep Researcher API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()


@app.post("/research")
async def research(
    query: str = Form(...),
    pdf: UploadFile | None = File(None),
):
    pdf_bytes = await pdf.read() if pdf else None

    initial: ResearchState = {
        "query": query,
        "pdf_bytes": pdf_bytes,
        "sources": [],
        "contradictions": [],
        "report_markdown": "",
        "status": "starting",
        "error": None,
    }

    #def stream():
     #   try:
      #      for event in graph.stream(initial, stream_mode="updates"):
       #         node, state_update = next(iter(event.items()))
        #        # Don't stream raw_text — too large
         #       safe_update = {k: v for k, v in state_update.items() if k != "pdf_bytes"}
          #      if "sources" in safe_update:
           #         safe_update["sources"] = [
            #            {k: v for k, v in s.items() if k != "raw_text"}
             #           for s in safe_update["sources"]
              #      ]
               # yield f"data: {json.dumps({'status': node, 'state': safe_update})}\n\n"
       # except Exception as e:
        #    yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"
    def stream():
        try:
            for event in graph.stream(initial, stream_mode="updates"):
                node, state_update = next(iter(event.items()))
                safe_update = {k: v for k, v in state_update.items() if k != "pdf_bytes"}
                if "sources" in safe_update:
                    safe_update["sources"] = [
                        {k: v for k, v in s.items() if k != "raw_text"}
                        for s in safe_update["sources"]
                    ]
                yield f"data: {json.dumps({'status': node, 'state': safe_update})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/health")
def health():
    return {"status": "ok"}


# Run with: uvicorn main:app --reload --port 8000
