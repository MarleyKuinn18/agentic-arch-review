"""Entry point for the architectural review agent.

Run: python -m arch_review_agent.main [path_to_architecture.md]
  or: python run.py [path_to_architecture.md]
"""

import asyncio
import sys
from pathlib import Path

from arch_review_agent.config import Settings
from arch_review_agent.orchestration.orchestrator import Orchestrator


def main() -> None:
    """CLI entry: load config, run orchestration pipeline."""
    doc_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not doc_path:
        print("Usage: arch-review-agent <path_to_architecture.md>")
        print("       python run.py <path_to_architecture.md>")
        sys.exit(1)
    
    path = Path(doc_path)
    if not path.exists():
        print(f"Error: File not found: {doc_path}")
        sys.exit(1)
    
    # Load settings (reads from .env)
    settings = Settings(arch_doc_path=str(path))
    
    print(f"\n{'='*60}")
    print(f"Architecture Review Agent")
    print(f"{'='*60}")
    print(f"Document: {path}")
    print(f"LLM: {settings.llm_base_url} ({settings.llm_model})")
    print(f"{'='*60}\n")
    
    # Run the orchestrator
    orchestrator = Orchestrator(settings)
    result = asyncio.run(orchestrator.run(path))
    
    if result.success:
        print(result.feedback)
        print(f"\n{'='*60}")
        print("Review completed successfully.")
        
        # Print summary stats
        if result.review:
            print(f"  - Strengths: {len(result.review.strengths)}")
            print(f"  - Improvements: {len(result.review.improvements)}")
            critical = result.review.get_critical_issues()
            if critical:
                print(f"  - Critical issues: {len(critical)}")
            print(f"  - Questions: {len(result.review.questions)}")
            print(f"  - Missing sections: {len(result.review.missing_sections)}")
    else:
        print(f"Error: {result.error}")
        if result.context.errors:
            print("Details:")
            for err in result.context.errors:
                print(f"  - {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
