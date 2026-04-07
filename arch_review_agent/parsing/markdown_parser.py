"""
Parse architecture review documentation from markdown.

Produces a structured representation for the agent and LLM.
"""

import re
from pathlib import Path
from typing import Any


def parse_heading(line: str) -> tuple[int, str] | None:
    """Return (level, title) for a heading line, else None."""
    match = re.match(r"^(#{1,6})\s*(.+)$", line.strip())
    if not match:
        return None
    level = len(match.group(1))
    title = match.group(2).strip()
    return (level, title)


def title_to_anchor(title: str) -> str:
    """Convert a heading title to a markdown anchor ID.
    
    Follows GitHub-flavored markdown anchor rules:
    - Lowercase
    - Replace spaces with hyphens
    - Remove special characters except hyphens and underscores
    """
    anchor = title.lower()
    anchor = re.sub(r'[^\w\s-]', '', anchor)
    anchor = re.sub(r'\s+', '-', anchor)
    return anchor


def parse_architecture_doc(raw_content: str) -> dict[str, Any]:
    """
    Parse markdown content into a structure (sections, headers, lists, etc.).

    - Extracts heading hierarchy (H1–H6) and sections as (level, title, body).
    - Tracks line numbers (1-indexed) and generates anchor IDs for each section.
    - Extracts code blocks (language, content); mermaid blocks flagged.
    - Detects table blocks and returns their raw lines.
    - Returned dict is suitable for building LLM prompts and tool inputs.
    """
    lines = raw_content.splitlines()
    sections: list[dict[str, Any]] = []
    code_blocks: list[dict[str, Any]] = []
    tables: list[list[str]] = []
    headings: list[dict[str, Any]] = []

    current_section: dict[str, Any] | None = None
    current_body: list[str] = []
    section_start_line: int = 0
    in_code_block = False
    code_lang = ""
    code_lines: list[str] = []
    code_start_line: int = 0
    in_table = False
    table_lines: list[str] = []
    table_start_line: int = 0
    
    # Track anchor counts for duplicate headings
    anchor_counts: dict[str, int] = {}

    def get_unique_anchor(title: str) -> str:
        """Generate unique anchor, appending -1, -2, etc. for duplicates."""
        base_anchor = title_to_anchor(title)
        if base_anchor in anchor_counts:
            anchor_counts[base_anchor] += 1
            return f"{base_anchor}-{anchor_counts[base_anchor]}"
        anchor_counts[base_anchor] = 0
        return base_anchor

    def flush_section(end_line: int) -> None:
        nonlocal current_section, current_body
        if current_section is not None:
            current_section["body"] = "\n".join(current_body).strip()
            current_section["end_line"] = end_line
            sections.append(current_section)
        current_section = None
        current_body = []

    for line_num, line in enumerate(lines, start=1):
        # Code block boundary
        if line.strip().startswith("```"):
            if in_code_block:
                block_content = "\n".join(code_lines)
                code_blocks.append({
                    "language": code_lang or "text",
                    "content": block_content,
                    "is_mermaid": (code_lang or "").strip().lower() == "mermaid",
                    "start_line": code_start_line,
                    "end_line": line_num,
                })
                code_lines = []
            else:
                code_lang = line.strip()[3:].strip()
                code_start_line = line_num
                if current_section is not None:
                    current_body.append(line)
            in_code_block = not in_code_block
            continue

        if in_code_block:
            code_lines.append(line)
            if current_section is not None:
                current_body.append(line)
            continue

        # Table: line contains | and looks like a table row
        if "|" in line and (line.strip().startswith("|") or re.match(r"^\s*\|", line)):
            if not in_table:
                in_table = True
                table_lines = []
                table_start_line = line_num
            table_lines.append(line)
            if current_section is not None:
                current_body.append(line)
            continue
        else:
            if in_table and table_lines:
                tables.append({
                    "lines": table_lines,
                    "start_line": table_start_line,
                    "end_line": line_num - 1,
                })
                table_lines = []
            in_table = False

        # Heading
        heading = parse_heading(line)
        if heading is not None:
            level, title = heading
            flush_section(line_num - 1)
            anchor = get_unique_anchor(title)
            headings.append({
                "level": level,
                "title": title,
                "anchor": anchor,
                "line": line_num,
            })
            current_section = {
                "level": level,
                "title": title,
                "anchor": anchor,
                "start_line": line_num,
                "body": "",
            }
            section_start_line = line_num
            current_body = []
            continue

        # Regular line
        if current_section is not None:
            current_body.append(line)

    if in_code_block and code_lines:
        code_blocks.append({
            "language": code_lang or "text",
            "content": "\n".join(code_lines),
            "is_mermaid": (code_lang or "").strip().lower() == "mermaid",
            "start_line": code_start_line,
            "end_line": len(lines),
        })
    if table_lines:
        tables.append({
            "lines": table_lines,
            "start_line": table_start_line,
            "end_line": len(lines),
        })

    flush_section(len(lines))

    return {
        "raw": raw_content,
        "headings": headings,
        "sections": sections,
        "code_blocks": code_blocks,
        "tables": tables,
        "mermaid_blocks": [b for b in code_blocks if b.get("is_mermaid")],
    }


def load_and_parse(doc_path: Path) -> dict[str, Any]:
    """Load file and parse. Convenience for orchestrator."""
    content = doc_path.read_text(encoding="utf-8")
    return parse_architecture_doc(content)
