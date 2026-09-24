"""Create the mid-sem before/after ASR chart from evaluation CSVs."""

import csv
import os
from collections import defaultdict

import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE, "results")


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def as_bool(value):
    return str(value).strip().lower() == "true"


def category_asr(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["category"]].append(as_bool(row["success"]))
    return {k: 100 * sum(v) / len(v) for k, v in grouped.items()}


def main():
    none_path = os.path.join(RESULTS_DIR, "results_none.csv")
    def_path = os.path.join(RESULTS_DIR, "results_segregator.csv")
    if not (os.path.exists(none_path) and os.path.exists(def_path)):
        raise FileNotFoundError("Run both --defense none and --defense segregator first.")

    none = read_rows(none_path)
    defended = read_rows(def_path)
    a = category_asr(none)
    b = category_asr(defended)
    categories = sorted(set(a) | set(b))

    x = list(range(len(categories)))
    width = 0.36
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar([i - width/2 for i in x], [a.get(c, 0) for c in categories], width, label="No defense")
    ax.bar([i + width/2 for i in x], [b.get(c, 0) for c in categories], width, label="Segregator")
    ax.set_ylabel("Attack Success Rate (%)")
    ax.set_title("Prompt-Injection ASR: Before vs After Defense")
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=20, ha="right")
    ax.set_ylim(0, 100)
    ax.legend()
    fig.tight_layout()

    out = os.path.join(RESULTS_DIR, "asr_before_after.png")
    fig.savefig(out, dpi=180)
    print(f"Chart written to: {out}")


if __name__ == "__main__":
    main()
