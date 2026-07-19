# cache_demo.py — pre-cached demo results
#
# Run without flags to execute the live pipeline for 2 demo queries and save
# the full ResearchState results to cache_demo.json.
#
# If the live query hangs or you need an instant demo, run with --cache to
# load the saved results straight from JSON instead of calling the graph.
#
#   python cache_demo.py            # live run, writes cache_demo.json
#   python cache_demo.py --cache    # instant replay from cache_demo.json

import argparse
import json
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

CACHE_FILE = Path("cache_demo.json")

DEMO_QUERIES = [
    "What accuracy does GPT-4 achieve on the MMLU benchmark?",
    "Does chain-of-thought prompting improve LLM reasoning accuracy?",
]


def run_live() -> list[dict]:
    from graph import build_graph
    from state import ResearchState

    print("Building graph...")
    graph = build_graph()

    results = []
    for query in DEMO_QUERIES:
        print(f"\nRunning live query: {query!r}")
        start = time.time()

        state: ResearchState = {
            "query": query,
            "pdf_bytes": None,
            "sources": [],
            "contradictions": [],
            "report_markdown": "",
            "status": "",
            "error": None,
        }

        final = graph.invoke(state)
        elapsed = time.time() - start

        results.append({
            "query": query,
            "elapsed": elapsed,
            "sources": [
                {k: v for k, v in s.items() if k != "raw_text"}
                for s in final["sources"]
            ],
            "contradictions": final["contradictions"],
            "report_markdown": final["report_markdown"],
        })
        print(f"Done in {elapsed:.1f}s — {len(final['sources'])} sources, "
              f"{len(final['contradictions'])} contradictions")

    return results


def save_cache(results: list[dict]) -> None:
    CACHE_FILE.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved {len(results)} query result(s) to {CACHE_FILE}")


def load_cache() -> list[dict]:
    if not CACHE_FILE.exists():
        raise FileNotFoundError(
            f"{CACHE_FILE} not found — run `python cache_demo.py` once without "
            f"--cache to generate it."
        )
    return json.loads(CACHE_FILE.read_text(encoding="utf-8"))


def display(results: list[dict]) -> None:
    for r in results:
        print(f"\n=== {r['query']} ===")
        print(f"Time to report: {r['elapsed']:.1f}s")
        print(f"Sources analyzed: {len(r['sources'])}")
        print(f"Contradictions found: {len(r['contradictions'])}")
        for c in r["contradictions"]:
            print(f"  [{c['confidence']:.0%}] {c['claim_a']} VS {c['claim_b']}")
        print("\n--- REPORT PREVIEW ---")
        print(r["report_markdown"][:500])


def main() -> None:
    parser = argparse.ArgumentParser(description="Cache demo for the deep researcher pipeline.")
    parser.add_argument(
        "--cache", action="store_true",
        help="Load previously saved results instantly instead of running the live pipeline.",
    )
    args = parser.parse_args()

    if args.cache:
        print(f"Loading cached results from {CACHE_FILE} (instant, no live query)...")
        results = load_cache()
    else:
        results = run_live()
        save_cache(results)

    display(results)


if __name__ == "__main__":
    main()
