#!/usr/bin/env python3
"""Extract a book PDF into a Skill scaffold.

Stage 1 of the book-to-skill workflow. Splits a PDF into chapter/section
files based on heading detection, and writes a structure map (TOC) plus
scaffolding for the agent to distill into a Skill.

Usage:
  python extract.py --pdf book.pdf --out scaffold --name my-book

Output:
  <out>/
    metadata.json        parsing stats + warnings (e.g. scanned pages)
    structure.md         table of contents
    sections/sec_*.md    one file per detected section

Heading detection strategy (textbooks + Chinese Q&A-style books):
  - A real section title is a SHORT line (<= ~24 chars, no trailing punct,
    not a number/date/url) that appears in the TOP region of >=2 distinct
    pages. In Q&A/essay books the section heading is set large at the start
    of a section and then repeated as a smaller RUNNING HEADER on every
    subsequent page of that section — so "repeats at page-top" is the
    reliable boundary signal (the running header literally marks where a
    new section begins).
  - Fallback: explicit structural markers ("第X章/节/篇", "Chapter",
    "Section") on a standalone short line.
  - Lines that appear on >=60% of ALL pages but NOT at page-top are treated
    as global header/footer noise and dropped from body text.
  - TOC pages (many "title <page-number>" lines) contribute no body text.
"""
import argparse
import json
import os
import re
from collections import defaultdict

import pdfplumber


def norm(t):
    return re.sub(r"[\s\d.,%\-/:()（）]+", "", t).strip()


def is_numberish(t):
    return bool(re.fullmatch(r"[\d.,%\-\s/:]+", t.strip()))


def is_date(t):
    return bool(re.fullmatch(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", t.strip()))


def is_url(t):
    return bool(re.search(r"https?://|www\.", t))


def is_chapter_marker(nl):
    return bool(re.search(r"第[一二三四五六七八九十百千0-9]+[章節篇回部分]|chapter|section", nl, re.I))


def is_toc_page(lines):
    n = 0
    for ln in lines:
        s = ln.strip()
        if re.search(r".{2,}\s+\d{1,3}\s*$", s) and not is_numberish(s):
            n += 1
    return n >= 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--max-chars", type=int, default=100000)
    ap.add_argument("--min-title-len", type=int, default=2)
    ap.add_argument("--max-title-len", type=int, default=24)
    ap.add_argument("--top-frac", type=float, default=0.14)
    ap.add_argument("--header-page-frac", type=float, default=0.60)
    ap.add_argument("--min-top-pages", type=int, default=2)
    args = ap.parse_args()

    os.makedirs(os.path.join(args.out, "sections"), exist_ok=True)

    per_page = {}        # page_no -> list of (norm, text, top, size)
    all_sizes = []
    scanned = 0
    total = 0
    page_heights = []
    toc_pages = set()

    with pdfplumber.open(args.pdf) as pdf:
        total = len(pdf.pages)
        for i, page in enumerate(pdf.pages, 1):
            page_heights.append(page.height)
            text = page.extract_text(x_tolerance=1.5, y_tolerance=3) or ""
            raw_lines = [ln for ln in text.split("\n") if ln.strip()]
            if len(text) > args.max_chars:
                scanned += 1
                per_page[i] = []
                continue
            if raw_lines and is_toc_page(raw_lines):
                toc_pages.add(i)
                per_page[i] = []
                continue
            # group chars into lines by 'top'
            line_map = defaultdict(list)
            for c in page.chars:
                line_map[round(c["top"])].append(c)
            rows = []
            for top in sorted(line_map):
                chars = sorted(line_map[top], key=lambda x: x["x0"])
                txt = "".join(ch.get("text", "") for ch in chars).strip()
                if not txt:
                    continue
                sz = max((c["size"] for c in chars if c.get("size")), default=None)
                rows.append((norm(txt), txt, top, sz))
                if sz:
                    all_sizes.append(sz)
            per_page[i] = rows

    if not all_sizes:
        raise SystemExit("No font sizes detected — possibly a scanned PDF.")

    body_size = sorted(all_sizes)[int(len(all_sizes) * 0.95)]
    avg_h = sum(page_heights) / max(1, len(page_heights))

    # Count, per normalized string, how many DISTINCT pages it appears in the
    # top region, and how many pages total (for global noise detection).
    top_pages = defaultdict(set)
    total_pages_of = defaultdict(int)
    for pno, rows in per_page.items():
        seen = set()
        for nl, txt, top, sz in rows:
            if not nl:
                continue
            total_pages_of[nl] += 1
            if top < args.top_frac * avg_h and nl not in seen:
                top_pages[nl].add(pno)
                seen.add(nl)

    # Global header/footer noise: appears on >=60% of pages but rarely at top.
    noise_norms = {
        nl for nl, c in total_pages_of.items()
        if c >= args.header_page_frac * total and len(top_pages.get(nl, ())) < 2
    }

    # Title norms: repeats at page-top on >= min_top_pages distinct pages,
    # or is an explicit chapter marker on a short standalone line.
    title_norms = set()
    for nl, pages in top_pages.items():
        if len(pages) >= args.min_top_pages:
            title_norms.add(nl)
    for pno, rows in per_page.items():
        for nl, txt, top, sz in rows:
            if (is_chapter_marker(nl)
                    and args.min_title_len <= len(txt) <= args.max_title_len
                    and not is_numberish(txt)):
                title_norms.add(nl)

    # Clean a title string: strip trailing page numbers, lone punctuation,
    # and junk fragments from header/footer or mid-line breaks.
    def clean_title(txt):
        t = txt.strip()
        t = re.sub(r"[\s]*\d{1,4}\s*$", "", t)          # trailing page number
        t = re.sub(r"^[\s，。、：；,.:;（）()]+", "", t)  # leading punctuation
        return t.strip()

    def is_junk_title(txt):
        t = txt.strip()
        if len(t) <= 1:
            return True
        if not re.search(r"[\u4e00-\u9fffA-Za-z]", t):  # no CJK/letter at all
            return True
        if re.fullmatch(r"[，。、：；,.:;（）()\-\s]+", t):
            return True
        # A real section title in a Chinese book must contain a 2-char run of
        # CJK. English-only fragments at page tops (brand/percent headers like
        # "OPPOvivo100%", "CEO", "GE）", "eBay") are rejected. English books
        # rely on the "Chapter/Section" structural-marker fallback below.
        if not re.search(r"[\u4e00-\u9fff]{2,}", t):
            return True
        return False

    # Determine representative title text + first page for each title norm.
    title_first = {}   # norm -> (first_page, cleaned_text)
    for pno, rows in per_page.items():
        for nl, txt, top, sz in rows:
            if nl in title_norms and nl not in title_first:
                ct = clean_title(txt)
                if is_junk_title(ct):
                    continue
                title_first[nl] = (pno, ct)

    boundaries = sorted(title_first.values(), key=lambda x: x[0])
    if not boundaries:
        boundaries = [(1, "（未识别到章节标题）")]

    def safe_fn(s, n):
        s = re.sub(r"[\\/:*?\"<>|（）()\s]+", "_", s).strip("_")
        return (s[:n] or "sec")[:n]

    # Build body text per page (drop title lines + noise lines; skip TOC).
    page_body = {}
    for pno, rows in per_page.items():
        if pno in toc_pages:
            page_body[pno] = ""
            continue
        kept = []
        for nl, txt, top, sz in rows:
            if nl in title_norms or nl in noise_norms:
                continue
            if is_numberish(txt) or is_date(txt) or is_url(txt):
                continue
            kept.append(txt)
        page_body[pno] = "\n".join(kept)

    toc = []
    bps = [b[0] for b in boundaries]
    sec_idx = 0
    for idx, (b_page, b_title) in enumerate(boundaries):
        end = (bps[idx + 1] - 1) if idx + 1 < len(bps) else total
        title = (b_title or f"第{b_page}页起").strip() or f"第{b_page}页起"
        body = "\n\n".join(page_body.get(pg, "") for pg in range(b_page, end + 1)).strip()
        if not body:
            # Skip cover/front-matter titles that carry no body text.
            continue
        fname = f"sec_{sec_idx+1:03d}_{safe_fn(title, 30)}.md"
        with open(os.path.join(args.out, "sections", fname), "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n{body}\n")
        toc.append((sec_idx + 1, title, fname, len(body)))
        sec_idx += 1

    with open(os.path.join(args.out, "structure.md"), "w", encoding="utf-8") as f:
        f.write(f"# Structure — {args.name}\n\n")
        f.write(f"- Pages: {total}\n")
        f.write(f"- Body font size: {body_size:.1f}px\n")
        f.write(f"- Scanned/empty pages: {scanned}\n")
        if scanned:
            f.write("- WARNING: scanned pages detected; consider OCR before distillation.\n")
        f.write("\n| # | Title | File | Chars |\n")
        f.write("|---|-------|------|-------|\n")
        for num, title, fname, chars in toc:
            f.write(f"| {num} | {title} | sections/{fname} | {chars} |\n")

    meta = {
        "name": args.name,
        "pages": total,
        "body_font_size": round(body_size, 1),
        "scanned_pages": scanned,
        "sections": len(toc),
        "warnings": ["Scanned pages detected" if scanned else None],
    }
    meta["warnings"] = [w for w in meta["warnings"] if w]
    with open(os.path.join(args.out, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"Parsed {total} pages, {len(toc)} sections.")
    print(f"Output: {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
