"""
Pydantic schemas for architecture review output.

Defines structured feedback format with anchor links for referencing
specific sections in the source document.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severity level for improvement suggestions."""
    
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


class Strength(BaseModel):
    """A positive aspect identified in the architecture document."""
    
    aspect: str = Field(
        description="Review aspect (e.g., api_design, security, observability)"
    )
    point: str = Field(
        description="What is done well"
    )
    section_ref: str = Field(
        description="Section title from the document"
    )
    anchor: str = Field(
        description="Markdown anchor link (e.g., #components)"
    )
    
    def to_markdown(self) -> str:
        """Format as markdown with anchor link."""
        return f"- **{self.aspect}**: {self.point} ([{self.section_ref}]({self.anchor}))"


class Improvement(BaseModel):
    """A suggested improvement for the architecture document."""
    
    aspect: str = Field(
        description="Review aspect (e.g., api_design, security, observability)"
    )
    severity: Severity = Field(
        description="Severity level: critical, major, or minor"
    )
    issue: str = Field(
        description="What is missing or problematic"
    )
    suggestion: str = Field(
        description="Specific actionable recommendation"
    )
    section_ref: str = Field(
        description="Section title from the document"
    )
    anchor: str = Field(
        description="Markdown anchor link (e.g., #components)"
    )
    
    def to_markdown(self) -> str:
        """Format as markdown with anchor link."""
        severity_icon = {
            Severity.CRITICAL: "🔴",
            Severity.MAJOR: "🟠",
            Severity.MINOR: "🟡",
        }.get(self.severity, "⚪")
        
        return (
            f"- {severity_icon} **[{self.severity.value.upper()}] {self.aspect}**: {self.issue}\n"
            f"  - **Suggestion**: {self.suggestion}\n"
            f"  - **Reference**: [{self.section_ref}]({self.anchor})"
        )


class ReviewFeedback(BaseModel):
    """Complete architecture review feedback."""
    
    summary: str = Field(
        description="Brief overall assessment (2-3 sentences)"
    )
    strengths: list[Strength] = Field(
        default_factory=list,
        description="Positive aspects of the design"
    )
    improvements: list[Improvement] = Field(
        default_factory=list,
        description="Suggested improvements with severity"
    )
    questions: list[str] = Field(
        default_factory=list,
        description="Clarifying questions about ambiguous parts"
    )
    missing_sections: list[str] = Field(
        default_factory=list,
        description="Important sections that should be added"
    )
    raw_response: str | None = Field(
        default=None,
        description="Raw LLM response if JSON parsing failed"
    )
    
    @classmethod
    def from_llm_response(cls, data: dict[str, Any]) -> "ReviewFeedback":
        """Parse LLM response dict into ReviewFeedback."""
        strengths = []
        for s in data.get("strengths", []):
            if isinstance(s, dict):
                strengths.append(Strength(
                    aspect=s.get("aspect", "general"),
                    point=s.get("point", ""),
                    section_ref=s.get("section_ref", ""),
                    anchor=s.get("anchor", ""),
                ))
        
        improvements = []
        for i in data.get("improvements", []):
            if isinstance(i, dict):
                severity_str = i.get("severity", "minor").lower()
                try:
                    severity = Severity(severity_str)
                except ValueError:
                    severity = Severity.MINOR
                
                improvements.append(Improvement(
                    aspect=i.get("aspect", "general"),
                    severity=severity,
                    issue=i.get("issue", ""),
                    suggestion=i.get("suggestion", ""),
                    section_ref=i.get("section_ref", ""),
                    anchor=i.get("anchor", ""),
                ))
        
        return cls(
            summary=data.get("summary", ""),
            strengths=strengths,
            improvements=improvements,
            questions=data.get("questions", []),
            missing_sections=data.get("missing_sections", []),
            raw_response=data.get("raw_response"),
        )
    
    def to_markdown(self) -> str:
        """Format complete feedback as markdown."""
        sections = [f"# Architecture Review\n\n{self.summary}"]
        
        if self.strengths:
            sections.append("\n## Strengths\n")
            sections.append("\n".join(s.to_markdown() for s in self.strengths))
        
        if self.improvements:
            # Sort by severity (critical first)
            severity_order = {Severity.CRITICAL: 0, Severity.MAJOR: 1, Severity.MINOR: 2}
            sorted_improvements = sorted(
                self.improvements,
                key=lambda x: severity_order.get(x.severity, 3)
            )
            sections.append("\n## Improvements\n")
            sections.append("\n".join(i.to_markdown() for i in sorted_improvements))
        
        if self.questions:
            sections.append("\n## Questions\n")
            sections.append("\n".join(f"- {q}" for q in self.questions))
        
        if self.missing_sections:
            sections.append("\n## Missing Sections\n")
            sections.append(
                "The following sections should be added to the document:\n"
                + "\n".join(f"- {s}" for s in self.missing_sections)
            )
        
        return "\n".join(sections)
    
    def get_critical_issues(self) -> list[Improvement]:
        """Return only critical severity improvements."""
        return [i for i in self.improvements if i.severity == Severity.CRITICAL]
    
    def get_issues_by_aspect(self, aspect: str) -> list[Improvement]:
        """Return improvements for a specific aspect."""
        return [i for i in self.improvements if i.aspect == aspect]
