"""
Utility functions for saving intermediate results.
"""
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


def save_intermediate(
    data: Dict[str, Any],
    category: str,
    output_dir: str = "./output",
    timestamp: bool = True,
    format: str = "json"
) -> str:
    """
    Save intermediate data to a file.
    
    Args:
        data: Data to save (must be JSON‑serializable)
        category: Category name (e.g., "analysis", "outline", "conversion_info")
        output_dir: Base output directory
        timestamp: Whether to add timestamp to filename
        format: "json" or "yaml"
        
    Returns:
        Path to the saved file
    """
    # Create category directory
    category_dir = Path(output_dir) / "intermediate" / category
    category_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S") if timestamp else ""
    if timestamp_str:
        filename = f"{category}_{timestamp_str}.{format}"
    else:
        filename = f"{category}.{format}"
    
    file_path = category_dir / filename
    
    # Save in requested format
    if format.lower() == "json":
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    elif format.lower() in ["yaml", "yml"]:
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    print(f"Saved intermediate {category} to {file_path}")
    return str(file_path)


def save_analysis_summary(
    summary_text: str,
    output_dir: str = "./output",
    timestamp: bool = True
) -> str:
    """
    Save analysis summary as a markdown file.
    
    Args:
        summary_text: Analysis summary text (markdown)
        output_dir: Base output directory
        timestamp: Whether to add timestamp to filename
        
    Returns:
        Path to the saved file
    """
    category_dir = Path(output_dir) / "intermediate" / "analysis"
    category_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S") if timestamp else ""
    if timestamp_str:
        filename = f"analysis_summary_{timestamp_str}.md"
    else:
        filename = "analysis_summary.md"
    
    file_path = category_dir / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(summary_text)
    
    print(f"Saved analysis summary to {file_path}")
    return str(file_path)


def save_outline_file(
    outline_data: Dict[str, Any],
    output_dir: str = "./output",
    timestamp: bool = True,
    format: str = "yaml"
) -> str:
    """
    Save outline data to a file.
    
    Args:
        outline_data: Outline data (dict representation)
        output_dir: Base output directory
        timestamp: Whether to add timestamp to filename
        format: "yaml" or "json"
        
    Returns:
        Path to the saved file
    """
    category_dir = Path(output_dir) / "intermediate" / "outline"
    category_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S") if timestamp else ""
    if timestamp_str:
        filename = f"outline_{timestamp_str}.{format}"
    else:
        filename = f"outline.{format}"
    
    file_path = category_dir / filename
    
    if format.lower() == "json":
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(outline_data, f, indent=2, ensure_ascii=False, default=str)
    elif format.lower() in ["yaml", "yml"]:
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(outline_data, f, default_flow_style=False, allow_unicode=True)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    print(f"Saved outline to {file_path}")
    return str(file_path)


def save_conversion_info(
    converted_files: list,
    materials_dir: str,
    output_dir: str = "./output",
    timestamp: bool = True
) -> str:
    """
    Save information about converted files.
    
    Args:
        converted_files: List of converted file info dicts
        materials_dir: Original materials directory
        output_dir: Base output directory
        timestamp: Whether to add timestamp to filename
        
    Returns:
        Path to the saved file
    """
    data = {
        "materials_dir": materials_dir,
        "conversion_time": datetime.now().isoformat(),
        "total_converted": len(converted_files),
        "converted_files": converted_files
    }
    
    return save_intermediate(
        data,
        category="conversion_info",
        output_dir=output_dir,
        timestamp=timestamp,
        format="json"
    )


def load_intermediate(
    category: str,
    output_dir: str = "./output",
    filename: Optional[str] = None,
    format: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load intermediate data from a file.
    
    Args:
        category: Category name (e.g., "analysis", "outline")
        output_dir: Base output directory
        filename: Specific filename to load (optional, loads latest if None)
        format: "json" or "yaml" (optional, auto‑detected from extension)
        
    Returns:
        Loaded data as dict
    """
    category_dir = Path(output_dir) / "intermediate" / category
    
    if not category_dir.exists():
        raise FileNotFoundError(f"Category directory not found: {category_dir}")
    
    # Find file to load
    if filename:
        file_path = category_dir / filename
    else:
        # Find latest file by modification time
        files = list(category_dir.glob("*"))
        if not files:
            raise FileNotFoundError(f"No files found in {category_dir}")
        file_path = max(files, key=lambda p: p.stat().st_mtime)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Determine format
    if format is None:
        suffix = file_path.suffix.lower()
        if suffix in ['.json']:
            format = "json"
        elif suffix in ['.yaml', '.yml']:
            format = "yaml"
        else:
            # Try to detect
            with open(file_path, 'r', encoding='utf-8') as f:
                first_char = f.read(1)
                f.seek(0)
                if first_char == '{':
                    format = "json"
                else:
                    format = "yaml"
    
    # Load file
    with open(file_path, 'r', encoding='utf-8') as f:
        if format == "json":
            return json.load(f)
        elif format in ["yaml", "yml"]:
            return yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported format: {format}")


if __name__ == "__main__":
    # Test the intermediate saver
    print("Testing intermediate saver...")
    
    test_data = {
        "test_key": "test_value",
        "numbers": [1, 2, 3],
        "nested": {"a": 1, "b": 2}
    }
    
    # Save JSON
    json_path = save_intermediate(test_data, "test", "./test_output", timestamp=False, format="json")
    print(f"Saved JSON to {json_path}")
    
    # Save YAML
    yaml_path = save_intermediate(test_data, "test", "./test_output", timestamp=False, format="yaml")
    print(f"Saved YAML to {yaml_path}")
    
    # Load back
    loaded_json = load_intermediate("test", "./test_output", filename="test.json")
    print(f"Loaded JSON: {loaded_json['test_key']}")
    
    # Clean up
    import shutil
    shutil.rmtree("./test_output", ignore_errors=True)
    print("Test completed.")