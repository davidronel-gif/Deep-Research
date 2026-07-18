# run_evals.py — evaluation harness
from dotenv import load_dotenv
load_dotenv()

import json
import time
import requests

# ── Load test cases ───────────────────────────────────────────────────────────
with open("test_cases.json") as f:
    cases = json.load(f)["test_cases"]

# ── Only run the 3 marked as good_demo to save time ──────────────────────────
demo_cases = [tc for tc in cases if tc.get("good_demo")]
print(f"Running {len(demo_cases)} eval cases...\n")

results = []

for tc in demo_cases:
    print(f"{'='*50}")
    print(f"Test: {tc['id']}")
    print(f"Query: {tc['query']}")
    print(f"Expecting contradiction: {tc['expected']['expect_contradiction']}")
    print()

    start = time.time()

    try:
        r = requests.post(
            "http://localhost:8000/research",
            data={"query": tc["query"]},
            stream=True,
            timeout=120,
        )

        final_state = {}
        for line in r.iter_lines():
            if line and line.startswith(b"data:"):
                try:
                    payload = json.loads(line[5:])
                    current_status = payload.get("status", "")
                    state = payload.get("state", {})
                    print(f"  [{current_status}] ", end="", flush=True)
                    if current_status in ("complete", "report_builder"):
                        final_state = state
                except json.JSONDecodeError:
                    continue

        elapsed = round(time.time() - start, 1)
        print(f"\n  Completed in {elapsed}s\n")

        # ── Score this test case ──────────────────────────────────────────────
        score = 0
        max_score = 3
        breakdown = []

        # 1. Source coverage
        src_count = len(final_state.get("sources", []))
        min_src   = tc["expected"]["min_sources"]
        if src_count >= min_src:
            score += 1
            breakdown.append(f"  ✅ Source coverage: {src_count} sources (needed {min_src})")
        else:
            breakdown.append(f"  ❌ Source coverage: {src_count} sources (needed {min_src})")

        # 2. Key terms in claims
        all_claims = " ".join(
            claim
            for src in final_state.get("sources", [])
            for claim in src.get("claims", [])
        ).lower()
        must_contain = tc["expected"]["must_contain_claims"]
        terms_found  = [t for t in must_contain if t.lower() in all_claims]
        if len(terms_found) >= len(must_contain) * 0.6:
            score += 1
            breakdown.append(f"  ✅ Key terms found: {terms_found}")
        else:
            missing = [t for t in must_contain if t.lower() not in all_claims]
            breakdown.append(f"  ❌ Missing key terms: {missing}")

        # 3. Contradiction detection accuracy
        contradictions    = final_state.get("contradictions", [])
        expect_contradict = tc["expected"]["expect_contradiction"]
        if contradictions and expect_contradict:
            score += 1
            top_conf = max(c["confidence"] for c in contradictions)
            breakdown.append(f"  ✅ Contradiction detected ({len(contradictions)} found, top confidence {top_conf:.0%})")
        elif not contradictions and not expect_contradict:
            score += 1
            breakdown.append(f"  ✅ Correctly no contradiction detected")
        elif contradictions and not expect_contradict:
            breakdown.append(f"  ❌ False positive — contradiction detected when none expected")
        else:
            breakdown.append(f"  ❌ Missed contradiction — none detected but one was expected")

        for line in breakdown:
            print(line)

        print(f"\n  SCORE: {score}/{max_score}")
        results.append({
            "id":       tc["id"],
            "query":    tc["query"],
            "score":    score,
            "max":      max_score,
            "elapsed":  elapsed,
        })

    except requests.exceptions.Timeout:
        print("  ❌ TIMEOUT — query took more than 120 seconds")
        results.append({"id": tc["id"], "query": tc["query"], "score": 0, "max": 3, "elapsed": 120})
    except Exception as e:
        print(f"  ❌ ERROR — {e}")
        results.append({"id": tc["id"], "query": tc["query"], "score": 0, "max": 3, "elapsed": 0})

# ── Final summary ─────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print("EVAL SUMMARY")
print(f"{'='*50}")

total     = sum(r["score"] for r in results)
maximum   = sum(r["max"]   for r in results)
pct       = (total / maximum * 100) if maximum > 0 else 0

for r in results:
    bar = "█" * r["score"] + "░" * (r["max"] - r["score"])
    print(f"  {r['id']}: [{bar}] {r['score']}/{r['max']} ({r['elapsed']}s)")

print(f"\n  TOTAL SCORE: {total}/{maximum} ({pct:.0f}%)")

if pct >= 70:
    print("  ✅ PASS — system is demo ready")
else:
    print("  ⚠️  NEEDS WORK — review failed cases above")

# ── Save results to file ──────────────────────────────────────────────────────
with open("eval_results.json", "w") as f:
    json.dump({
        "total": total,
        "maximum": maximum,
        "percentage": round(pct, 1),
        "cases": results,
    }, f, indent=2)

print(f"\n  Results saved to eval_results.json")
print(f"  Show this score to judges: {total}/{maximum} ({pct:.0f}%)")