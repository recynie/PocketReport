"""
Pydantic models for the academic report writing system.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from enum import Enum


class SectionType(str, Enum):
    """Type of section in the report outline."""
    CHAPTER = "chapter"
    SECTION = "section"
    SUBSECTION = "subsection"


class Section(BaseModel):
    """Represents a hierarchical section in the report outline."""
    type: SectionType = Field(SectionType.SECTION, description="Type of section")
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
        """Assemble the complete report in markdown format with proper heading levels."""
        from collections import defaultdict
        
        # Build hierarchy from outline if available
        if self.outline:
            return self._assemble_from_outline()
        
        # Fallback: flat sections sorted by index
        lines = [f"# {self.title}\n"]
        sorted_indices = sorted(self.sections.keys())
        for idx in sorted_indices:
            content = self.sections[idx]
            # Determine heading level based on dot count in index
            level = idx.count('.') + 1
            heading = '#' * min(level, 6)  # limit to h6
            lines.append(f"{heading} {idx} {content.splitlines()[0] if content else ''}")
            lines.append(content if content else "")
            lines.append("")  # Add blank line between sections
        return "\n".join(lines)
    
    def _assemble_from_outline(self) -> str:
        """Assemble report by traversing outline hierarchy."""
        lines = [f"# {self.title}\n"]
        
        def traverse(section: Section, depth: int = 1):
            heading = '#' * (depth + 1)  # +1 because title is h1
            lines.append(f"{heading} {section.index} {section.title}")
            if section.index in self.sections:
                content = self.sections[section.index]
                if content:
                    lines.append(content)
            lines.append("")
            for sub in section.subsections:
                traverse(sub, depth + 1)
        
        for top_section in self.outline.sections:
            traverse(top_section, depth=1)
        
