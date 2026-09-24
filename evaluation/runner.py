"""Evaluation runner for attacks + benign false-positive tests.

Examples:
    python evaluation/runner.py --defense none
    python evaluation/runner.py --defense segregator
    python evaluation/runner.py --defense segregator --include-benign
"""

import argparse
import csv
import os
import sys
import time
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "target"))
sys.path.insert(0, os.path.join(BASE, "attacks"))
sys.path.insert(0, os.path.join(BASE, "defense"))
sys.path.insert(0, os.path.join(BASE, "evaluation"))

from chatbot import RAGChatbot, DOCS_DIR
from seeds import SEED_ATTACKS
from judge import check_success
from benign_queries import BENIGN_QUERIES

RESULTS_DIR = os.path.join(BASE, "results")


def write_poisoned_doc(poisoned_doc):
    if poisoned_doc is None:
        return None
    name, content = poisoned_doc
    os.makedirs(DOCS_DIR, exist_ok=True)
    path = os.path.join(DOCS_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def cleanup_doc(path):
    if path and os.path.exists(path):
        os.remove(path)


def get_defense_pipeline(name):
    if name == "none":
        return None
    if name == "segregator":
        from segregator import segregator_defense
        return segregator_defense
    raise ValueError(f"Unknown defense: {name}")


def run_attacks(defense_name):
    defense_pipeline = get_defense_pipeline(defense_name)
    results = []

    for attack in SEED_ATTACKS:
        doc_path = write_poisoned_doc(attack.get("poisoned_doc"))
        try:
            bot = RAGChatbot(defense_pipeline=defense_pipeline)
            start = time.perf_counter()
            response = bot.respond(attack["query"])
            latency_ms = round((time.perf_counter() - start) * 1000, 1)
            success, judge_reason = check_success(response, attack)

            results.append({
                "id": attack["id"],
                "category": attack["category"],
                "defense": defense_name,
                "success": success,
                "latency_ms": latency_ms,
                "judge_reason": judge_reason,
                "response_preview": response[:240].replace("\n", " "),
            })
        finally:
            cleanup_doc(doc_path)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, f"results_{defense_name}.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    total = len(results)
    succeeded = sum(bool(r["success"]) for r in results)
    print(f"\nDefense: {defense_name}")
    print(f"Attack Success Rate (ASR): {succeeded}/{total} ({100*succeeded/total:.1f}%)")

    by_cat = defaultdict(list)
    for r in results:
        by_cat[r["category"]].append(r)
    for category, rows in sorted(by_cat.items()):
        cat_success = sum(bool(r["success"]) for r in rows)
        print(f"  {category:<16}: {cat_success}/{len(rows)} ({100*cat_success/len(rows):.1f}%)")

    print(f"Results written to: {out_path}")
    return results


def run_benign(defense_name):
    defense_pipeline = get_defense_pipeline(defense_name)
    results = []

    for i, query in enumerate(BENIGN_QUERIES, start=1):
        bot = RAGChatbot(defense_pipeline=defense_pipeline)
        start = time.perf_counter()
        response = bot.respond(query)
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        falsely_blocked = response.lower().startswith("[blocked by defense:")
        results.append({
            "id": f"B{i:02d}",
            "defense": defense_name,
            "falsely_blocked": falsely_blocked,
            "latency_ms": latency_ms,
            "query": query,
            "response_preview": response[:240].replace("\n", " "),
        })

    out_path = os.path.join(RESULTS_DIR, f"benign_{defense_name}.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    fp = sum(bool(r["falsely_blocked"]) for r in results)
    total = len(results)
    print(f"False Positive Rate (FPR): {fp}/{total} ({100*fp/total:.1f}%)")
    print(f"Benign results written to: {out_path}")
    return results


def run(defense_name="none", include_benign=False):
    attacks = run_attacks(defense_name)
    benign = run_benign(defense_name) if include_benign else []
    return attacks, benign


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--defense", default="none", choices=["none", "segregator"])
    parser.add_argument("--include-benign", action="store_true")
    args = parser.parse_args()
    run(args.defense, args.include_benign)
