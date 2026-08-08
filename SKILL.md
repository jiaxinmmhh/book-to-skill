---
name: book-to-skill
slug: book-to-skill
display_name: "书到技能 · 把技术书/PDF 蒸馏成 AI 技能"
displayName: "书到技能 · 把技术书/PDF 蒸馏成 AI 技能"
description: 【知识技能化】把技术书/PDF/白皮书/设计规范/运营手册蒸馏成可导入的 AI 技能（知识包）——不是 RAG 检索原文，而是把书里方法论内化为决策规则、模板、心智模型，让 AI 边干活边套用专业方法。适合：把《Clean Code》变代码审查 Skill、把品牌规范变审图 Skill、把投资问答录变投研 Skill。当用户说"把这本书变成 skill""把 PDF 转成技能""知识即服务"时使用。
agent_created: true
version: 1.0.2
category: productivity
emoji: "📚"
author: jiaxinmmhh
platforms:
  - WorkBuddy
  - QClaw
  - ima
  - Claude Code
  - Cursor
---

# Book-to-Skill

Turn a technical book (or any structured document) into an importable Skill: a distilled, procedural **knowledge pack** an agent loads on demand so it *applies* the book's methods while working — not merely retrieves its text.

## Requirements
- **`pdfplumber`** for Step 1 (PDF parsing): `pip install pdfplumber`. Step 2–4 (distilling + assembling) need no extra deps.
- Works best on **text PDFs**. If `metadata.json` reports `scanned_pages`, OCR the PDF first — image-only files have no extractable text.

## Why this is not RAG
- **RAG** = retrieve text chunks to stuff into context. **Skill** = load **distilled procedure + curated references** so the agent *acts* per the book's methodology.
- The output is a portable skill folder another agent can import and trigger by its `description`. That portability is the product.

## Workflow (run in order)

### 1. Ingest & scaffold
Parse the PDF into a navigable structure:
```bash
python scripts/extract.py --pdf "<path-to.pdf>" --out "<output-dir>" --name "<skill-slug>"
```
This produces in `<output-dir>`:
- `structure.md` — table of contents (section #, title, page range, size)
- `sections/sec_NNN.md` — per-chapter raw extracted text
- `metadata.json` — page count, font stats, `likely_scanned` flag

If `metadata.json` shows `"likely_scanned": true`, **STOP** and tell the user to OCR the PDF first (image-only file → no extractable text).

### 2. Distill (the value step — never skip)
Read `structure.md`, then load the relevant `sections/*.md` and rewrite each into **procedural knowledge** following `references/distill-guide.md`:
- Convert "what the book says" → "how to do X" checklists, decision rules, anti-patterns.
- Extract reusable templates, code patterns, naming/schema rules.
- Capture the book's *mental model*, not its prose.

### 3. Assemble the generated Skill
```
<skill-slug>/
├── SKILL.md            # name + description (trigger text) + how to apply the book
└── references/
    └── <book>.md       # distilled, sectioned knowledge (the curated pack)
```
- `SKILL.md` `description` must list concrete triggers ("when implementing X from <book>…").
- Keep `SKILL.md` lean (<5k words); put detail in `references/`.
- For deterministic deep lookups, ship `scripts/search_knowledge.py` pointing at `references/`.

### 4. Verify & package
- Spot-check that `references/<book>.md` covers the high-value sections from `structure.md`.
- Tell the user to import via the Skills UI → **上传技能** (or run the WorkBuddy skill packager). Do **not** claim auto-publish.

## Notes
- Deterministic retrieval while an agent uses the generated skill:
  `python scripts/search_knowledge.py --base references --query "topic" --top 5`
- Very large books: split `references/` by part; keep it one level deep from `SKILL.md`.
- This skill creates the *scaffold + distilling method*; the actual distillation of a specific book is done by the agent at use time (or by a human reviewer for quality-gated packs).
