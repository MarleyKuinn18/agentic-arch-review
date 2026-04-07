"""
Chunk indexer for RAG: splits parsed markdown into retrievable chunks.

Each chunk contains:
- content: the text content
- section_title: heading title
- anchor: markdown anchor ID for linking
- start_line / end_line: line numbers in original document
- keywords: extracted keywords for retrieval
"""

import re
from dataclasses import dataclass, field
from typing import Any


# Common English stopwords to filter out
STOPWORDS = frozenset([
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
    "be", "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare", "ought",
    "used", "this", "that", "these", "those", "i", "you", "he", "she", "it",
    "we", "they", "what", "which", "who", "whom", "whose", "where", "when",
    "why", "how", "all", "each", "every", "both", "few", "more", "most",
    "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "just", "also", "now", "here", "there", "then",
])


@dataclass
class Chunk:
    """A retrievable chunk of the architecture document."""
    
    content: str
    section_title: str
    anchor: str
    start_line: int
    end_line: int
    keywords: set[str] = field(default_factory=set)
    level: int = 2  # heading level
    
    def to_context_str(self) -> str:
        """Format chunk for LLM context with reference info."""
        return (
            f"[Section: {self.section_title}](#L{self.start_line}-L{self.end_line})\n"
            f"{self.content}"
        )
    
    def get_anchor_link(self) -> str:
        """Return markdown anchor link."""
        return f"[{self.section_title}](#{self.anchor})"
    
    def get_line_reference(self) -> str:
        """Return line reference string."""
        return f"L{self.start_line}-L{self.end_line}"


def extract_keywords(text: str) -> set[str]:
    """Extract keywords from text, filtering stopwords and short tokens."""
    # Lowercase and extract word tokens
    tokens = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text.lower())
    # Filter stopwords and very short tokens
    keywords = {t for t in tokens if t not in STOPWORDS and len(t) > 2}
    return keywords


class ChunkIndexer:
    """
    Indexes parsed markdown sections into chunks for retrieval.
    
    Handles large documents by:
    - Splitting sections that exceed max_chunk_size
    - Preserving section hierarchy and line references
    """
    
    def __init__(self, max_chunk_size: int = 1500):
        """
        Args:
            max_chunk_size: Maximum characters per chunk. Sections larger than
                           this will be split into multiple chunks.
        """
        self.max_chunk_size = max_chunk_size
        self.chunks: list[Chunk] = []
    
    def index_parsed_doc(self, parsed: dict[str, Any]) -> list[Chunk]:
        """
        Index a parsed markdown document into chunks.
        
        Args:
            parsed: Output from parse_architecture_doc()
            
        Returns:
            List of Chunk objects ready for retrieval
        """
        self.chunks = []
        sections = parsed.get("sections", [])
        
        for section in sections:
            self._index_section(section)
        
        return self.chunks
    
    def _index_section(self, section: dict[str, Any]) -> None:
        """Index a single section, splitting if necessary."""
        title = section.get("title", "Untitled")
        anchor = section.get("anchor", "")
        body = section.get("body", "")
        start_line = section.get("start_line", 1)
        end_line = section.get("end_line", start_line)
        level = section.get("level", 2)
        
        # Include title in content for context
        full_content = f"## {title}\n\n{body}" if level == 2 else f"{'#' * level} {title}\n\n{body}"
        
        if len(full_content) <= self.max_chunk_size:
            # Section fits in one chunk
            chunk = Chunk(
                content=full_content,
                section_title=title,
                anchor=anchor,
                start_line=start_line,
                end_line=end_line,
                keywords=extract_keywords(full_content),
                level=level,
            )
            self.chunks.append(chunk)
        else:
            # Split large section into multiple chunks
            self._split_section(
                title=title,
                anchor=anchor,
                body=body,
                start_line=start_line,
                end_line=end_line,
                level=level,
            )
    
    def _split_section(
        self,
        title: str,
        anchor: str,
        body: str,
        start_line: int,
        end_line: int,
        level: int,
    ) -> None:
        """Split a large section into multiple chunks by paragraphs."""
        paragraphs = re.split(r'\n\s*\n', body)
        
        current_content = f"{'#' * level} {title}\n\n"
        current_start = start_line
        chunk_index = 0
        lines_so_far = 1  # heading line
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_lines = para.count('\n') + 1
            
            # Check if adding this paragraph exceeds limit
            if len(current_content) + len(para) + 2 > self.max_chunk_size and current_content.strip():
                # Save current chunk
                chunk = Chunk(
                    content=current_content.strip(),
                    section_title=f"{title} (part {chunk_index + 1})" if chunk_index > 0 else title,
                    anchor=f"{anchor}-{chunk_index}" if chunk_index > 0 else anchor,
                    start_line=current_start,
                    end_line=current_start + lines_so_far - 1,
                    keywords=extract_keywords(current_content),
                    level=level,
                )
                self.chunks.append(chunk)
                
                # Start new chunk
                chunk_index += 1
                current_start = current_start + lines_so_far
                current_content = f"{'#' * level} {title} (continued)\n\n"
                lines_so_far = 1
            
            current_content += para + "\n\n"
            lines_so_far += para_lines + 1  # +1 for blank line
        
        # Save final chunk
        if current_content.strip():
            chunk = Chunk(
                content=current_content.strip(),
                section_title=f"{title} (part {chunk_index + 1})" if chunk_index > 0 else title,
                anchor=f"{anchor}-{chunk_index}" if chunk_index > 0 else anchor,
                start_line=current_start,
                end_line=end_line,
                keywords=extract_keywords(current_content),
                level=level,
            )
            self.chunks.append(chunk)
    
    def get_all_chunks(self) -> list[Chunk]:
        """Return all indexed chunks."""
        return self.chunks
    
    def get_chunk_by_anchor(self, anchor: str) -> Chunk | None:
        """Find a chunk by its anchor ID."""
        for chunk in self.chunks:
            if chunk.anchor == anchor:
                return chunk
        return None
