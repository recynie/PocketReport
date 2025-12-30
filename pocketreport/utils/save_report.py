"""
Utility function for saving reports to files.
"""
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


def save_report(
    content: str,
    output_path: Optional[str] = None,
    report_title: Optional[str] = None,
    timestamp: bool = True
) -> str:
    """
    Save report content to a file.
    
    Args:
        content: Report content to save
        output_path: Path where to save the file (if None, generates automatic name)
        report_title: Title of the report (used for automatic filename)
        timestamp: Whether to add timestamp to filename
        
    Returns:
        Path to the saved file
    """
    if output_path is None:
        # Generate automatic filename
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S") if timestamp else ""
        title_slug = "report"
        if report_title:
            # Create filesystem-safe slug from title
            import re
            title_slug = re.sub(r'[^\w\s-]', '', report_title.lower())
            title_slug = re.sub(r'[-\s]+', '_', title_slug).strip('-_')
        
        if timestamp_str:
            filename = f"{title_slug}_{timestamp_str}.md"
        else:
            filename = f"{title_slug}.md"
        
        output_path = os.path.join(".", "output", filename)
    
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save the file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Get file stats
        file_size = os.path.getsize(output_path)
        
        print(f"Report saved to: {output_path}")
        print(f"File size: {file_size} bytes")
        
        return output_path
        
    except Exception as e:
        raise IOError(f"Error saving report to {output_path}: {e}")


def save_chapter(
    chapter_content: str,
    chapter_title: str,
    chapter_index: int,
    output_dir: str = "./output/chapters"
) -> str:
    """
    Save a single chapter to a file.
    
    Args:
        chapter_content: Chapter content
        chapter_title: Chapter title
        chapter_index: Chapter index
        output_dir: Directory to save chapters
        
    Returns:
        Path to the saved chapter file
    """
    # Create filesystem-safe slug from title
    import re
    title_slug = re.sub(r'[^\w\s-]', '', chapter_title.lower())
    title_slug = re.sub(r'[-\s]+', '_', title_slug).strip('-_')
    
    filename = f"{chapter_index:02d}_{title_slug}.md"
    output_path = os.path.join(output_dir, filename)
    
    # Ensure directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(chapter_content)
        
        return output_path
        
    except Exception as e:
        raise IOError(f"Error saving chapter to {output_path}: {e}")


def save_outline(
    outline_data: dict,
    output_path: Optional[str] = None
) -> str:
    """
    Save report outline to a JSON file.
    
    Args:
        outline_data: Outline data (dict)
        output_path: Path to save JSON file
        
    Returns:
        Path to the saved outline file
    """
    import json
    
    if output_path is None:
        output_path = os.path.join(".", "output", "outline.json")
    
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(outline_data, f, indent=2, ensure_ascii=False)
        
        return output_path
        
    except Exception as e:
        raise IOError(f"Error saving outline to {output_path}: {e}")


if __name__ == "__main__":
    # Test the save report function
    test_content = "# Test Report\n\nThis is a test report content."
    
    print("Testing report saving...")
    
    try:
        saved_path = save_report(test_content, report_title="Test Report")
        print(f"Saved to: {saved_path}")
        
        # Test chapter saving
        chapter_path = save_chapter(
            "# Test Chapter\n\nChapter content.",
            "Test Chapter",
            1
        )
        print(f"Chapter saved to: {chapter_path}")
        
        # Test outline saving
        test_outline = {
            "title": "Test Report",
            "chapters": [
                {"index": 1, "title": "Introduction", "description": "Intro chapter"}
            ]
        }
        outline_path = save_outline(test_outline)
        print(f"Outline saved to: {outline_path}")
        
    except Exception as e:
        print(f"Error: {e}")