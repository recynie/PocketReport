"""
Pydantic models for the academic report writing system.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Chapter(BaseModel):
    """Represents a chapter in the report outline."""
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


class ReportOutline(BaseModel):
    """Represents the complete report outline with title and chapters."""
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
    """Complete report with all chapters assembled."""
    title: str
    chapters: Dict[int, str] = Field(..., description="Chapter index to content mapping")
    analysis_summary: Optional[AnalysisSummary] = None
    outline: Optional[ReportOutline] = None
    
    def assemble(self) -> str:
        """Assemble the complete report in markdown format."""
        lines = [f"# {self.title}\n"]
        
        # Sort chapters by index
        sorted_indices = sorted(self.chapters.keys())
        for idx in sorted_indices:
            content = self.chapters[idx]
            lines.append(content)
            lines.append("")  # Add blank line between chapters
            
        return "\n".join(lines)