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
    print(f"Match: {match}")
    if not match:
        return None
    level = len(match.group(1))
    print(f"Heading: {level}, {match.group(2).strip()}")
    title = match.group(2).strip()
    print(f"Heading: {level}, {title}")
    return (level, title)


def parse_architecture_doc(raw_content: str) -> dict[str, Any]:
    """
    Parse markdown content into a structure (sections, headers, lists, etc.).

    - Extracts heading hierarchy (H1–H6) and sections as (level, title, body).
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
    in_code_block = False
    code_lang = ""
    code_lines: list[str] = []
    in_table = False
    table_lines: list[str] = []

    def flush_section() -> None:
        nonlocal current_section, current_body
        if current_section is not None:
            current_section["body"] = "\n".join(current_body).strip()
            sections.append(current_section)
        current_section = None
        current_body = []

    for line in lines:
        # Code block boundary
        if line.strip().startswith("```"):
            if in_code_block:
                block_content = "\n".join(code_lines)
                code_blocks.append({
                    "language": code_lang or "text",
                    "content": block_content,
                    "is_mermaid": (code_lang or "").strip().lower() == "mermaid",
                })
                code_lines = []
            else:
                code_lang = line.strip()[3:].strip()
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
            table_lines.append(line)
            if current_section is not None:
                current_body.append(line)
            continue
        else:
            if in_table and table_lines:
                tables.append(table_lines)
                table_lines = []
            in_table = False

        # Heading
        heading = parse_heading(line)
        if heading is not None:
            level, title = heading
            flush_section()
            headings.append({"level": level, "title": title})
            current_section = {"level": level, "title": title, "body": ""}
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
        })
    if table_lines:
        tables.append(table_lines)

    flush_section()

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
