"""
Entry point for the architectural review agent.

Run: python -m arch_review_agent.main [path_to_architecture.md]
"""

import asyncio
import sys
from pathlib import Path
from arch_review_agent.parsing.markdown_parser import parse_heading, parse_architecture_doc
# TODO: Wire orchestrator and config once implemented
# from arch_review_agent.config import Settings
# from arch_review_agent.orchestration import Orchestrator


def main() -> None:

    heading = parse_heading("## Heading 600")
    if heading is None:
        print("Not a valid heading line")
    else:
        level, title = heading
        print(f"Level: {level}, Title: {title}")

    parsed = parse_architecture_doc("This is a sample architecture document")
    print(f"Parsed: {parsed}")

    # """CLI entry: load config, run orchestration pipeline."""
    # doc_path = sys.argv[1] if len(sys.argv) > 1 else None
    # if not doc_path or not Path(doc_path).exists():
    #     print("Usage: arch-review-agent <path_to_architecture.md>")
    #     sys.exit(1)

    # # TODO: Load settings and run orchestrator
    # # settings = Settings(arch_doc_path=doc_path)
    # # result = asyncio.run(Orchestrator(settings).run())
    # # print(result)

    # print(f"Architecture document: {doc_path}")
    # print("(Orchestration not yet implemented)")


if __name__ == "__main__":
    main()
