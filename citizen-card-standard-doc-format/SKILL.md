---
name: citizen-card-standard-doc-format
description: Adjust Chinese Word/DOCX materials to the Citizen Card standard meeting-document format. Use when the user asks to format 市民卡、上会材料、汇报材料、方案材料, or similar .docx files according to 文件材料格式要求, including page setup, fonts, paragraph spacing, manual numbering, footers, and render-based layout verification.
---

# 市民卡标准文件格式调整

Use this skill to normalize `.docx` materials to the 市民卡上会材料 style, while preserving the original document as much as possible.

## Workflow

1. Identify the source `.docx` and create a copy named `原文件名-格式调整版.docx`. Do not overwrite the original unless the user explicitly asks.
2. If the user provides a current `文件材料格式要求.docx`, extract/check it first. Otherwise use `references/format-requirements.md`.
3. Apply page setup, fonts, paragraph spacing, hierarchy numbering, table layout, and outside footers.
4. Render the result with the Documents skill `render_docx.py` and visually inspect representative pages: cover/title page, table-heavy pages, pages with diagrams, and final page.
5. Iterate until there is no obvious text clipping, table overflow, incoherent pagination, or blank tail page.

## Default Format Rules

Read `references/format-requirements.md` for the concise standard.

Core rules:
- Page: A4; margins top 3.6 cm, bottom 2.8 cm, left 3.2 cm, right 2.6 cm; footer distance 2.6 cm.
- Paragraphs: before/after 0; exact line spacing 29 pt; body first-line indent about 2 Chinese characters.
- Title: 二号, 方正小标宋简体 or 创艺简标宋, centered.
- Level 1 heading: 三号黑体, manual sequence like `一、`.
- Level 2 heading: 三号楷体_GB2312, manual sequence like `（一）`.
- Body: 三号仿宋_GB2312.
- Numbering: use manually typed hierarchy `一、` / `（一）` / `1.` / `（1）`; remove Word automatic numbering when normalizing headings.
- Footer page numbers: outside aligned for duplex printing, commonly `-1-`, `-2-`.

## Automation Helper

For ordinary DOCX normalization, use:

```bash
python3 /Users/hetao/.codex/skills/citizen-card-standard-doc-format/scripts/format_citizen_card_docx.py input.docx --output output.docx
```

Useful options:
- `--strict-table-font`: keep table text at 三号 size. Use only when tables are narrow enough.
- `--no-manual-renumber`: preserve existing heading text numbering.

The helper handles common formatting operations but does not replace visual QA. Always render and inspect after running it.

## Table Policy

The formal requirement says "其他文字" uses 三号仿宋. In real Word materials, wide tables may clip or become unreadable at 三号. If strict table text causes overflow after rendering, use smaller 仿宋 table text, usually 12-14 pt with 20-24 pt exact line spacing, while keeping the official page setup and body/headings strict.

Mention this explicitly in the final response when a table-size adjustment was needed.

## Visual QA

Use the Documents skill render workflow. Inspect:
- table continuation across pages, especially bottom rows and repeated headers;
- title and heading fonts/spacing;
- outside footer placement on odd/even pages;
- final page for blank tails;
- diagrams or images for cropping and caption alignment.

Final response should link only the final adjusted `.docx` unless the user asks for render images or PDFs.
