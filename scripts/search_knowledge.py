#!/usr/bin/env python3
"""Deterministic deep lookup over a generated skill's references/.

Usage:
  python search_knowledge.py --base references --query "topic words" --top 5

Scores markdown files under <base> by term frequency in matching lines and
prints the best-matching snippets. No embedding/model needed — reproducible.
"""
import argparse
import os
import re


def collect_md(base):
    out = []
    for root, _, files in os.walk(base):
        for fn in files:
            if fn.endswith(".md"):
                out.append(os.path.join(root, fn))
    return out


def score_file(path, terms):
    hits = []
    with open(path, encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f, 1):
            low = line.lower()
            cnt = sum(low.count(t) for t in terms)
            if cnt:
                hits.append((cnt, i, line.strip()))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args()

    terms = [t.lower() for t in re.findall(r"\w+", args.query) if len(t) > 1]
    if not terms:
        raise SystemExit("No searchable terms in query")

    results = []  # (score, path, line_no, snippet)
    for path in collect_md(args.base):
        for cnt, ln, snippet in score_file(path, terms):
            results.append((cnt, path, ln, snippet))

    results.sort(key=lambda r: r[0], reverse=True)
    for score, path, ln, snippet in results[: args.top]:
        rel = os.path.relpath(path, args.base)
        print(f"[{score}] {rel}:{ln}  {snippet[:160]}")

    if not results:
        print("No matches.")


if __name__ == "__main__":
    main()
