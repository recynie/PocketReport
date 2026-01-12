"""
Pydantic models for the academic report writing system.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from enum import Enum


# DEPRECATED: SectionType enum is no longer used. Kept for backward compatibility.
# Heading levels are now determined by index dot count (e.g., "1" = h1, "1.1" = h2, "1.1.1" = h3)
class SectionType(str, Enum):
    """DEPRECATED: Type of section in the report outline."""
    CHAPTER = "chapter"
    SECTION = "section"
    SUBSECTION = "subsection"


class Section(BaseModel):
    """Represents a hierarchical section in the report outline."""
    index: str = Field(..., description="Hierarchical index (e.g., '1', '1.1', '1.2.3')")
    title: str = Field(..., description="Title of the section")
    description: str = Field(
        ...,
        description="Detailed instructions on what this section should cover, based on input materials"
    )
    
    # Optional fields for after writing
    content: Optional[str] = Field(
        None,
        description="The written content of the section (markdown format)"
    )
    
    subsections: List["Section"] = Field(
        default_factory=list,
        description="Child sections (can be nested arbitrarily)"
    )
    
    def is_leaf(self) -> bool:
        """Return True if this section has no subsections."""
        return len(self.subsections) == 0
    
    def flatten(self) -> List["Section"]:
        """Return a flat list of all leaf sections in depth‑first order."""
        leaves = []
        if self.is_leaf():
            leaves.append(self)
        else:
            for sub in self.subsections:
                leaves.extend(sub.flatten())
        return leaves
    
    def get_by_index(self, index: str) -> Optional["Section"]:
        """Find a section by its exact index (supports nested)."""
        if self.index == index:
            return self
        for sub in self.subsections:
            found = sub.get_by_index(index)
            if found:
                return found
        return None
    
    def get_heading_level(self) -> int:
        """Calculate heading level based on index dot count."""
        # Level 1 for top-level sections (no dot or single number)
        # "1" -> level 1, "1.1" -> level 2, "1.1.1" -> level 3, etc.
        dot_count = self.index.count('.')
        return min(dot_count + 1, 6)  # Cap at h6 per Markdown spec
    
    def get_heading_markdown(self, include_index: bool = False) -> str:
        """Generate markdown heading for this section.
        
        By default, headings only contain the title, not the index.
        Set include_index=True to include index like "1.2.1" in heading.
        """
        level = self.get_heading_level()
        heading = '#' * level
        if include_index:
            return f"{heading} {self.index} {self.title}"
        else:
            return f"{heading} {self.title}"


# Forward reference fix
Section.model_rebuild()


class ReportOutline(BaseModel):
    """Represents the complete report outline with hierarchical sections."""
    title: str
    sections: List[Section] = Field(..., description="Top‑level sections (usually chapters)")
    
    def get_section_by_index(self, index: str) -> Optional[Section]:
        """Get a section by its hierarchical index."""
        for section in self.sections:
            found = section.get_by_index(index)
            if found:
                return found
        return None
    
    def flatten(self) -> List[Section]:
        """Return a flat list of all leaf sections in depth‑first order."""
        leaves = []
        for section in self.sections:
            leaves.extend(section.flatten())
        return leaves
    
    def to_legacy_chapters(self) -> List[Dict[str, Any]]:
        """
        Convert hierarchical outline to flat list of chapters (for backward compatibility).
        Each leaf section becomes a chapter with integer index based on order.
        """
        leaves = self.flatten()
        chapters = []
        for i, leaf in enumerate(leaves, start=1):
            chapters.append({
                "index": i,
                "title": leaf.title,
                "description": leaf.description,
                "content": leaf.content
            })
        return chapters
    
    def to_legacy(self) -> "LegacyReportOutline":
        """
        Convert hierarchical outline to legacy flat outline.
        Each top-level section becomes a chapter with integer index.
        """
        chapters = []
        for i, section in enumerate(self.sections, start=1):
            chapter = Chapter(
                index=i,
                title=section.title,
                description=section.description,
                content=section.content
            )
            chapters.append(chapter)
        
        return LegacyReportOutline(
            title=self.title,
            chapters=chapters
        )


# Legacy models (kept for compatibility during transition)
class Chapter(BaseModel):
    """Legacy model representing a flat chapter in the report outline."""
    index: int
    title: str = Field(..., description="The title of the chapter")
    description: str = Field(
        ..., 
        description="Detailed instructions on what this chapter should cover, based on input materials"
    )
    
    # Optional fields for after writing
    content: Optional[str] = Field(
        None,
        description="The written content of the chapter (markdown format)"
    )


class LegacyReportOutline(BaseModel):
    """Legacy flat outline with chapters."""
    title: str
    chapters: List[Chapter]
    
    def get_chapter_by_index(self, index: int) -> Optional[Chapter]:
        """Get a chapter by its index."""
        for chapter in self.chapters:
            if chapter.index == index:
                return chapter
        return None
    
    def to_hierarchical(self) -> "ReportOutline":
        """
        Convert legacy flat outline to hierarchical outline.
        Each chapter becomes a top-level section with index as string.
        """
        sections = []
        for chapter in self.chapters:
            section = Section(
                index=str(chapter.index),
                title=chapter.title,
                description=chapter.description,
                content=chapter.content
            )
            sections.append(section)
        
        return ReportOutline(
            title=self.title,
            sections=sections
        )


class AnalysisSummary(BaseModel):
    """Structured summary from the Analyst agent."""
    core_problem: str = Field(..., description="Summary of the core problem")
    methods: str = Field(..., description="Summary of methods used")
    results: str = Field(..., description="Summary of results")
    key_terms: List[str] = Field(..., description="List of key technical terms and definitions")
    formulas_algorithms: List[str] = Field(..., description="Important math formulas or algorithms")
    
    def to_text(self) -> str:
        """Convert the analysis to a text summary for prompts."""
        lines = [
            "## Analysis Summary",
            f"### Core Problem: {self.core_problem}",
            f"### Methods: {self.methods}",
            f"### Results: {self.results}",
            "### Key Technical Terms:",
            *[f"- {term}" for term in self.key_terms],
            "### Important Formulas/Algorithms:",
            *[f"- {formula}" for formula in self.formulas_algorithms]
        ]
        return "\n".join(lines)


class Report(BaseModel):
    """Complete report with all sections assembled."""
    title: str
    sections: Dict[str, str] = Field(..., description="Section index to content mapping")
    analysis_summary: Optional[AnalysisSummary] = None
    outline: Optional[ReportOutline] = None
    
    def assemble(self) -> str:
        """Assemble the complete report in markdown format with proper heading levels.
        
        Note: The report title is NOT included as a heading in the content.
        Top-level sections (index like "1", "2") become h1 headings.
        """
        from collections import defaultdict
        
        # Build hierarchy from outline if available
        if self.outline:
            return self._assemble_from_outline()
        
        # Fallback: flat sections sorted by index
        lines = []
        sorted_indices = sorted(self.sections.keys())
        for idx in sorted_indices:
            content = self.sections[idx]
            # Determine heading level based on dot count in index
            # "1" -> h1, "1.1" -> h2, "1.1.1" -> h3, etc.
            level = idx.count('.') + 1
            heading = '#' * min(level, 6)  # limit to h6
            
            # Extract first line for heading if content exists
            first_line = ""
            if content:
                # Get first non-empty line
                for line in content.splitlines():
                    if line.strip():
                        first_line = line.strip()
                        break
            
            # Add heading with title only (no index)
            if first_line and first_line.startswith('#'):
                # Content already includes heading, don't add duplicate
                lines.append(content)
            else:
                # Use first line as heading text, or empty string if no content
                heading_text = first_line if first_line else ''
                lines.append(f"{heading} {heading_text}")
                if content:
                    lines.append(content)
            
            lines.append("")  # Add blank line between sections
        return "\n".join(lines)
    
    def _assemble_from_outline(self) -> str:
        """Assemble report by traversing outline hierarchy."""
        lines = []
        
        def traverse(section: Section):
            # Use section's own heading calculation (without index)
            heading_markdown = section.get_heading_markdown(include_index=False)
            
            # Check if content already includes a heading
            content = self.sections.get(section.index, "")
            if content and content.strip().startswith('#'):
                # Content already has heading, use it as-is
                lines.append(content)
            else:
                # Add heading and content
                lines.append(heading_markdown)
                if content:
                    lines.append(content)
            
            lines.append("")  # Blank line after section
            
            # Recursively process subsections
            for sub in section.subsections:
                traverse(sub)
        
        for top_section in self.outline.sections:
            traverse(top_section)
        
        return "\n".join(lines)
