# 市民卡标准文件格式要求

Use these defaults when the user asks for 市民卡标准文件格式调整 and does not provide a newer standard file.

## Page Setup

- Paper: A4.
- Margins: top 3.6 cm, bottom 2.8 cm, left 3.2 cm, right 2.6 cm.
- Footer distance: 2.6 cm.
- Layout target: generally 22 lines per page and 28 characters per line.
- Duplex printing: use outside page numbers when appropriate.

## Fonts

- Main title: 二号方正小标宋体. If unavailable, use 方正小标宋简体 or 创艺简标宋.
- Level 1 heading: 三号黑体.
- Level 2 heading: 三号楷体_GB2312.
- Other text/body: 三号仿宋_GB2312.
- Footer page number: 宋体 or a compatible Chinese serif, 14 pt is acceptable.

## Paragraphs

- Paragraph spacing before: 0.
- Paragraph spacing after: 0.
- Line spacing: fixed/exact 29 pt.
- Body first-line indent: about 2 Chinese characters.
- Avoid extra blank paragraphs unless needed for document structure.

## Numbering

Use manually typed hierarchy, not Word automatic numbering:

- `一、`
- `（一）`
- `1.`
- `（1）`

When normalizing documents, remove `w:numPr` automatic numbering from heading paragraphs if manual numbers are inserted.

## Practical Table Handling

Start with the formal style where feasible. If a table clips, overflows, or becomes visually unusable:

- keep 仿宋_GB2312;
- reduce table text to 12-14 pt;
- use exact line spacing around 20-24 pt;
- repeat header rows;
- allow rows to split across pages when needed;
- reduce cell margins moderately.

This is an implementation compromise to preserve readable official-layout output.
