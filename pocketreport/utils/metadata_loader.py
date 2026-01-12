"""
Utility function for loading and managing report metadata from YAML template.
"""
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import yaml


def _get_template_path() -> Path:
    """Get the path to the report_metadata.yaml template file."""
    current_dir = Path(__file__).parent.parent
    template_path = current_dir.parent / "config" / "report_metadata.yaml"
    
    if not template_path.exists():
        raise FileNotFoundError(
            f"Metadata template file not found at {template_path}. "
            "Please ensure config/report_metadata.yaml exists in the project root."
        )
    
    return template_path


def load_metadata_template() -> Dict[str, Any]:
    """
    Load the base metadata template from YAML file.
    
    Returns:
        Dictionary with template structure:
        {
            "title": "",
            "subtitle": "",
            "abstract": "",
            "info": {
                "姓名": "...",
                "学号": "...",
                "课程": "...",
                "日期": "...",
                "指导教师": "..."
            },
            "bibliography": ""
        }
        
    Raises:
        FileNotFoundError: If template file doesn't exist
        RuntimeError: If template file cannot be parsed
    """
    template_path = _get_template_path()
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = yaml.safe_load(f)
        logging.debug(f"Loaded metadata template from {template_path}")
        return template
    except Exception as e:
        raise RuntimeError(f"Failed to load metadata template from {template_path}: {e}")


def update_metadata(
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    abstract: Optional[str] = None,
    info: Optional[Dict[str, str]] = None,
    bibliography: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load template and update with provided metadata values.
    
    Args:
        title: Report title (max 100 chars recommended)
        subtitle: Report subtitle (max 100 chars recommended)
        abstract: Report abstract (100-300 words recommended)
        info: Dictionary with student/author information
              (keys: 姓名, 学号, 课程, 日期, 指导教师)
        bibliography: Bibliography or references section
        
    Returns:
        Updated metadata dictionary
        
    Examples:
        metadata = update_metadata(
            title="Artificial Intelligence",
            subtitle="An Introduction",
            abstract="This report...",
            info={"姓名": "张三", "学号": "20230001"}
        )
    """
    metadata = load_metadata_template()
    
    # Update provided fields
    if title is not None:
        metadata["title"] = title
    
    if subtitle is not None:
        metadata["subtitle"] = subtitle
    
    if abstract is not None:
        metadata["abstract"] = abstract
    
    if bibliography is not None:
        metadata["bibliography"] = bibliography
    
    # Update info sub-dictionary (merge with template)
    if info is not None:
        if "info" not in metadata:
            metadata["info"] = {}
        metadata["info"].update(info)
    
    return metadata


def metadata_to_yaml(metadata: Dict[str, Any]) -> str:
    """
    Convert metadata dictionary to YAML string format.
    
    Args:
        metadata: Metadata dictionary
        
    Returns:
        YAML string representation
    """
    try:
        yaml_str = yaml.dump(
            metadata,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False
        )
        return yaml_str
    except Exception as e:
        raise RuntimeError(f"Failed to convert metadata to YAML: {e}")


def generate_frontmatter(metadata: Dict[str, Any]) -> str:
    """
    Generate markdown YAML frontmatter with separator lines.
    
    Args:
        metadata: Metadata dictionary
        
    Returns:
        Frontmatter string in format:
        ---
        title: "..."
        subtitle: "..."
        ...
        ---
    """
    yaml_content = metadata_to_yaml(metadata)
    # Remove trailing newline from YAML dump if present
    yaml_content = yaml_content.rstrip()
    frontmatter = f"---\n{yaml_content}\n---"
    return frontmatter


def append_frontmatter_to_report(
    frontmatter: str,
    report_content: str
) -> str:
    """
    Prepend YAML frontmatter to report content.
    
    Args:
        frontmatter: Generated frontmatter string (including --- separators)
        report_content: Main report content in markdown
        
    Returns:
        Combined string: frontmatter + newline + report_content
    """
    return f"{frontmatter}\n\n{report_content}"


if __name__ == "__main__":
    # Test script to verify metadata loading and generation
    import pprint
    
    logging.basicConfig(level=logging.DEBUG)
    
    print("=" * 80)
    print("Testing Metadata Loader")
    print("=" * 80)
    
    try:
        # Load template
        print("\n[1. Loading Template]")
        template = load_metadata_template()
        print("Template loaded successfully:")
        pprint.pprint(template)
        
        # Update with custom values
        print("\n[2. Updating Metadata]")
        custom_metadata = update_metadata(
            title="人工智能导论",
            subtitle="一份全面的研究报告",
            abstract="这是一份关于人工智能基础概念和应用的综合研究报告。",
            info={
                "姓名": "王五",
                "学号": "20230123"
            }
        )
        print("Updated metadata:")
        pprint.pprint(custom_metadata)
        
        # Generate frontmatter
        print("\n[3. Generating Frontmatter]")
        frontmatter = generate_frontmatter(custom_metadata)
        print("Generated frontmatter:")
        print(frontmatter)
        
        # Append to sample report
        print("\n[4. Appending to Report]")
        sample_report = "# Section 1\n\nSome content here..."
        full_report = append_frontmatter_to_report(frontmatter, sample_report)
        print("Combined report (first 200 chars):")
        print(full_report[:200])
        
        print("\n✓ All metadata operations completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
