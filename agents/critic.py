# agents/critic.py — Person B  ← start here at hour 1
# LLM-as-judge contradiction detector.
# Strict mode: only surfaces conflicts where claims cannot both be factually correct.
# Test this standalone before wiring into the graph.

import os
import sys
import json
import itertools
import anthropic
from pathlib import Path

from dotenv import load_dotenv

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

load_dotenv()

from llm_provider import create_chat_completion
from state import ResearchState, Contradiction

CONFIDENCE_THRESHOLD = 0.75  # raise to 0.85 if too many false positives
MAX_SOURCES = 4                 # keep the judge workload bounded
MAX_CLAIMS_PER_SOURCE = 2       # compare only the strongest top-2 claims per source

JUDGE_PROMPT = """You are a strict fact-checker comparing two claims from different research sources.

Determine ONLY if these two claims are in direct factual contradiction — meaning both cannot be true at the same time as stated.

Do NOT mark as contradiction if:
- They discuss different aspects of the same topic
- One is more specific than the other
- They reflect different time periods or contexts
- They represent legitimate scientific disagreement or uncertainty

CLAIM A (from "{title_a}"): {claim_a}
CLAIM B (from "{title_b}"): {claim_b}

Return JSON only — no preamble:
{{
  "is_contradiction": true or false,
  "confidence": 0.0 to 1.0,
  "explanation": "one sentence explaining the conflict or why it is not one"
}}"""


def run_critic(state: ResearchState) -> dict:
    contradictions: list[Contradiction] = []
    sources = state["sources"][:MAX_SOURCES]

    for src_a, src_b in itertools.combinations(sources, 2):
        claims_a = src_a["claims"][:MAX_CLAIMS_PER_SOURCE]
        claims_b = src_b["claims"][:MAX_CLAIMS_PER_SOURCE]

        for claim_a in claims_a:
            for claim_b in claims_b:
                msg = create_chat_completion(
                    model=os.getenv("CRITIC_MODEL", "anthropic/claude-haiku-4-5"),
                    max_tokens=200,
                    messages=[{
                        "role": "user",
                        "content": JUDGE_PROMPT.format(
                            title_a=src_a["title"], claim_a=claim_a,
                            title_b=src_b["title"], claim_b=claim_b,
                        ),
                    }],
                )

                #try:
                 #   result = json.loads(msg.content[0].text)
                  #  print(f"DEBUG: {result}")   # ← add this line temporarily
                #except json.JSONDecodeError:
                    #continue
                #except json.JSONDecodeError as e:
                 #   print(f"JSON ERROR: {e} — raw: {msg.content[0].text}")  # ← and this
                  #  continue
                try:
                    raw = msg.content[0].text.strip()
                    #print(f"RAW RESPONSE: '{raw[:100]}'")   # show first 100 chars
                    if raw.startswith("```"):
                        raw = raw.split("```")[1]
                        if raw.startswith("json"):
                            raw = raw[4:]
                    raw = raw.strip()
                    #print(f"CLEANED: '{raw[:100]}'")        # show what we're trying to parse
                    result = json.loads(raw)
                    #print(f"PARSED OK: {result}")
                    #print(f"CONFIDENCE: {result.get('confidence')} THRESHOLD: {CONFIDENCE_THRESHOLD}")
                except json.JSONDecodeError as e:
                    print(f"JSON ERROR: {e}")
                    print(f"FULL RAW: {msg.content[0].text}")
                    continue
           
                if result.get("is_contradiction") and result.get("confidence", 0) >= CONFIDENCE_THRESHOLD:
                    contradictions.append(Contradiction(
                        source_a_id=src_a["id"],
                        source_b_id=src_b["id"],
                        claim_a=claim_a,
                        claim_b=claim_b,
                        confidence=result["confidence"],
                        explanation=result["explanation"],
                    ))

    return {"contradictions": contradictions, "status": "critic"}


# ── Standalone test — run this at hour 2 to validate the judge prompt ─────────
if __name__ == "__main__":
    test_state: ResearchState = {
        "query": "test",
        "pdf_bytes": None,
        "sources": [
            {
                "id": "web_0", "origin": "web", "url": "https://a.com",
                "title": "Paper A", "raw_text": "",
                "summary": "",
                "claims": ["GPT-4 achieves 90% accuracy on the MMLU benchmark"],
            },
            {
                "id": "web_1", "origin": "web", "url": "https://b.com",
                "title": "Paper B", "raw_text": "",
                "summary": "",
                "claims": ["GPT-4 achieves 86.4% accuracy on the MMLU benchmark"],
            },
        ],
        "contradictions": [],
        "report_markdown": "",
        "status": "test",
        "error": None,
    }
    result = run_critic(test_state)
    print(json.dumps(result["contradictions"], indent=2))