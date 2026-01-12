"""
Utility functions for serializing and deserializing report outlines.
"""
import yaml
import json
from pathlib import Path
from typing import Union, Optional, Dict, Any
from .models import ReportOutline, Section, SectionType, LegacyReportOutline, Chapter


class OutlineSerializer:
    """Main class for outline serialization operations."""
    
    @staticmethod
    def save_outline(outline: Union[ReportOutline, LegacyReportOutline],
                     file_path: Union[str, Path],
                     format: str = "yaml") -> Path:
        """
        Save an outline (either hierarchical or legacy) to file.
        
        Args:
            outline: The outline to save
            file_path: Path to save the file
            format: "yaml" or "json"
            
        Returns:
            Path to the saved file
        """
        # Convert legacy to hierarchical if needed
        if isinstance(outline, LegacyReportOutline):
            outline = convert_legacy_to_hierarchical(outline)
        
        if format.lower() == "yaml":
            return save_outline_yaml(outline, file_path)
        elif format.lower() == "json":
            return save_outline_json(outline, file_path)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'yaml' or 'json'.")
    
    @staticmethod
    def load(file_path: Union[str, Path],
             format: Optional[str] = None) -> ReportOutline:
        """
        Load an outline from file, auto‑detecting format from extension.
        
        Args:
            file_path: Path to the outline file
            format: Optional format override ("yaml" or "json")
            
        Returns:
            ReportOutline object
        """
        return load_outline(file_path, format)
    
    @staticmethod
    def to_dict(outline: ReportOutline) -> Dict[str, Any]:
        """Convert ReportOutline to a serializable dict."""
        return _outline_to_dict(outline)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> ReportOutline:
        """Convert dict to ReportOutline."""
        return _dict_to_outline(data)


# Create a singleton instance
outline_serializer = OutlineSerializer()


def save_outline_yaml(outline: ReportOutline, file_path: Union[str, Path]) -> Path:
    """
    Save a ReportOutline to a YAML file.
    
    Args:
        outline: The outline to save
        file_path: Path to save the YAML file
        
    Returns:
        Path to the saved file
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dict
    outline_dict = _outline_to_dict(outline)
    
    # Save as YAML
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(outline_dict, f, default_flow_style=False, allow_unicode=True)
    
    print(f"Outline saved to YAML: {path}")
    return path


def load_outline_yaml(file_path: Union[str, Path]) -> ReportOutline:
    """
    Load a ReportOutline from a YAML file.
    
    Args:
        file_path: Path to the YAML file
        
    Returns:
        ReportOutline object
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Outline file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        outline_dict = yaml.safe_load(f)
    
    return _dict_to_outline(outline_dict)


def save_outline_json(outline: ReportOutline, file_path: Union[str, Path]) -> Path:
    """
    Save a ReportOutline to a JSON file (alternative format).
    
    Args:
        outline: The outline to save
        file_path: Path to save the JSON file
        
    Returns:
        Path to the saved file
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    outline_dict = _outline_to_dict(outline)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(outline_dict, f, indent=2, ensure_ascii=False)
    
    print(f"Outline saved to JSON: {path}")
    return path


def load_outline_json(file_path: Union[str, Path]) -> ReportOutline:
    """
    Load a ReportOutline from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        ReportOutline object
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Outline file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        outline_dict = json.load(f)
    
    return _dict_to_outline(outline_dict)


def _outline_to_dict(outline: ReportOutline) -> Dict[str, Any]:
    """Convert ReportOutline to a serializable dict."""
    def section_to_dict(section: Section) -> Dict[str, Any]:
        # Type field is deprecated, but include a default for backward compatibility
        # Section objects no longer have a type attribute
        return {
            "type": SectionType.SECTION.value,  # Default for backward compatibility
            "index": section.index,
            "title": section.title,
            "description": section.description,
            "content": section.content,
            "subsections": [section_to_dict(sub) for sub in section.subsections]
        }
    
    return {
        "title": outline.title,
        "sections": [section_to_dict(section) for section in outline.sections]
    }


def _dict_to_outline(data: Dict[str, Any]) -> ReportOutline:
    """Convert dict to ReportOutline."""
    def dict_to_section(section_dict: Dict[str, Any]) -> Section:
        # Type field is deprecated and ignored
        # Section class no longer accepts type parameter
        return Section(
            index=section_dict["index"],
            title=section_dict["title"],
            description=section_dict["description"],
            content=section_dict.get("content"),
            subsections=[dict_to_section(sub) for sub in section_dict.get("subsections", [])]
        )
    
    return ReportOutline(
        title=data["title"],
        sections=[dict_to_section(section) for section in data["sections"]]
    )


def convert_legacy_to_hierarchical(legacy_outline: LegacyReportOutline) -> ReportOutline:
    """
    Convert a legacy flat outline to a hierarchical outline.
    Each chapter becomes a top‑level section with no subsections.
    
    Args:
        legacy_outline: LegacyReportOutline with flat chapters
        
    Returns:
        ReportOutline with hierarchical sections
    """
    sections = []
    for chapter in legacy_outline.chapters:
        section = Section(
            index=str(chapter.index),
            title=chapter.title,
            description=chapter.description,
            content=chapter.content,
            subsections=[]
        )
        sections.append(section)
    
    return ReportOutline(title=legacy_outline.title, sections=sections)


def convert_hierarchical_to_legacy(outline: ReportOutline) -> LegacyReportOutline:
    """
    Convert a hierarchical outline to a legacy flat outline.
    All leaf sections become chapters with sequential integer indices.
    
    Args:
        outline: ReportOutline with hierarchical sections
        
    Returns:
        LegacyReportOutline with flat chapters
    """
    leaves = outline.flatten()
    chapters = []
    for i, leaf in enumerate(leaves, start=1):
        chapter = Chapter(
            index=i,
            title=leaf.title,
            description=leaf.description,
            content=leaf.content
        )
        chapters.append(chapter)
    
    return LegacyReportOutline(title=outline.title, chapters=chapters)


def save_outline(outline: Union[ReportOutline, LegacyReportOutline], 
                 file_path: Union[str, Path],
                 format: str = "yaml") -> Path:
    """
    Save an outline (either hierarchical or legacy) to file.
    
    Args:
        outline: The outline to save
        file_path: Path to save the file
        format: "yaml" or "json"
        
    Returns:
        Path to the saved file
    """
    # Convert legacy to hierarchical if needed
    if isinstance(outline, LegacyReportOutline):
        outline = convert_legacy_to_hierarchical(outline)
    
    if format.lower() == "yaml":
        return save_outline_yaml(outline, file_path)
    elif format.lower() == "json":
        return save_outline_json(outline, file_path)
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'yaml' or 'json'.")


def load_outline(file_path: Union[str, Path], 
                 format: Optional[str] = None) -> ReportOutline:
    """
    Load an outline from file, auto‑detecting format from extension.
    
    Args:
        file_path: Path to the outline file
        format: Optional format override ("yaml" or "json")
        
    Returns:
        ReportOutline object
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Outline file not found: {file_path}")
    
    # Determine format
    if format is None:
        suffix = path.suffix.lower()
        if suffix in ['.yaml', '.yml']:
            format = "yaml"
        elif suffix == '.json':
            format = "json"
        else:
            # Try to detect by reading first few bytes
            with open(path, 'r', encoding='utf-8') as f:
                first_char = f.read(1)
                f.seek(0)
                if first_char == '{':
                    format = "json"
                else:
                    format = "yaml"
    
    if format == "yaml":
        return load_outline_yaml(path)
    elif format == "json":
        return load_outline_json(path)
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'yaml' or 'json'.")


if __name__ == "__main__":
    # Test the serializer
    print("Testing outline serializer...")
    
    # Create a test hierarchical outline
    from .models import Section, ReportOutline
    
    outline = ReportOutline(
        title="Test Report",
        sections=[
            Section(
                index="1",
                title="Introduction",
                description="Introduce the topic",
                subsections=[
                    Section(
                        index="1.1",
                        title="Background",
                        description="Provide background context"
                    ),
                    Section(
                        index="1.2",
                        title="Problem Statement",
                        description="Define the problem"
                    )
                ]
            ),
            Section(
                index="2",
                title="Methodology",
                description="Describe the methods used"
            )
        ]
    )
    
    # Save and load YAML
    yaml_path = Path("./test_outline.yaml")
    save_outline_yaml(outline, yaml_path)
    loaded_yaml = load_outline_yaml(yaml_path)
    print(f"YAML round‑trip successful: {loaded_yaml.title}")
    
    # Save and load JSON
    json_path = Path("./test_outline.json")
    save_outline_json(outline, json_path)
    loaded_json = load_outline_json(json_path)
    print(f"JSON round‑trip successful: {loaded_json.title}")
    
    # Test legacy conversion
    legacy = convert_hierarchical_to_legacy(outline)
    print(f"Converted to legacy: {len(legacy.chapters)} chapters")
    
    # Clean up
    yaml_path.unlink(missing_ok=True)
    json_path.unlink(missing_ok=True)
    print("Test completed.")