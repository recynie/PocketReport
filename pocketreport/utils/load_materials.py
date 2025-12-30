"""
Utility function for loading and converting materials to Markdown.
"""
import os
import shutil
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import hashlib
import json

try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False


def load_materials(
    directory_path: str,
    output_dir: Optional[str] = None,
    cache_conversions: bool = True
) -> Tuple[str, int, List[Dict[str, str]]]:
    """
    Load and convert all supported files in a directory to Markdown.
    
    Args:
        directory_path: Path to directory containing materials
        output_dir: Directory to save converted markdown files (default: ./output/converted)
        cache_conversions: Whether to cache conversions to avoid re‑converting unchanged files
        
    Returns:
        Tuple of (concatenated_content, total_file_count, converted_files_info)
        where converted_files_info is a list of dicts with keys:
            'original_path', 'converted_path', 'size', 'hash'
    
    Raises:
        FileNotFoundError: If directory doesn't exist
        ImportError: If markitdown is not installed
    """
    directory = Path(directory_path)
    
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    if not directory.is_dir():
        raise ValueError(f"Path is not a directory: {directory_path}")
    
    if not MARKITDOWN_AVAILABLE:
        raise ImportError(
            "MarkItDown is not installed. Install with: pip install 'markitdown[all]'"
        )
    
    # Set up output directory for converted files
    if output_dir is None:
        output_dir = "./output/converted"
    converted_dir = Path(output_dir)
    converted_dir.mkdir(parents=True, exist_ok=True)
    
    # Cache file to store conversion hashes
    cache_file = converted_dir / ".conversion_cache.json"
    cache = _load_cache(cache_file) if cache_conversions else {}
    
    # Supported markdown extensions (will be read directly)
    markdown_extensions = {'.md', '.markdown', '.mdown', '.mkd', '.mkdn', '.mdwn', '.mdt', '.mdtext'}
    
    # Files that need conversion (non‑markdown)
    convert_extensions = {
        '.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls',
        '.html', '.htm', '.txt', '.csv', '.json', '.xml', '.epub',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
        '.mp3', '.wav', '.m4a', '.flac',
        '.zip'
    }
    
    markitdown = MarkItDown()
    concatenated_content = []
    total_files = 0
    converted_files = []
    
    # Walk through directory
    for file_path in sorted(directory.rglob('*')):
        if not file_path.is_file():
            continue
        
        suffix = file_path.suffix.lower()
        relative_path = file_path.relative_to(directory)
        
        # Compute file hash for caching
        file_hash = _compute_file_hash(file_path) if cache_conversions else None
        
        # Check if we need to convert
        if suffix in markdown_extensions:
            # Read markdown directly
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                concatenated_content.append(f"# File: {relative_path}\n")
                concatenated_content.append(content)
                concatenated_content.append("\n" + "="*80 + "\n")
                total_files += 1
            except Exception as e:
                print(f"Warning: Could not read markdown file {file_path}: {e}")
                continue
                
        elif suffix in convert_extensions:
            # Convert to markdown
            converted_path = converted_dir / f"{relative_path.stem}.md"
            
            # Check cache
            cache_key = str(file_path)
            if (cache_conversions and cache_key in cache and 
                cache[cache_key].get('hash') == file_hash and
                converted_path.exists()):
                # Use cached conversion
                try:
                    with open(converted_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    print(f"Using cached conversion: {relative_path}")
                except Exception as e:
                    print(f"Warning: Cached file corrupted, re‑converting {file_path}: {e}")
                    content = _convert_file(markitdown, file_path, converted_path)
                    cache[cache_key] = {'hash': file_hash}
            else:
                # Perform conversion
                content = _convert_file(markitdown, file_path, converted_path)
                if cache_conversions:
                    cache[cache_key] = {'hash': file_hash}
            
            concatenated_content.append(f"# File: {relative_path} (converted from {suffix})\n")
            concatenated_content.append(content)
            concatenated_content.append("\n" + "="*80 + "\n")
            total_files += 1
            
            converted_files.append({
                'original_path': str(file_path),
                'converted_path': str(converted_path),
                'size': len(content),
                'hash': file_hash
            })
            
        else:
            # Unsupported extension
            print(f"Warning: Unsupported file type {suffix} for {relative_path}")
            continue
    
    # Save cache
    if cache_conversions:
        _save_cache(cache_file, cache)
    
    if total_files == 0:
        raise FileNotFoundError(f"No supported files found in {directory_path}")
    
    return "\n".join(concatenated_content), total_files, converted_files


def _convert_file(markitdown: MarkItDown, file_path: Path, output_path: Path) -> str:
    """Convert a single file to markdown and save to output_path."""
    try:
        print(f"Converting {file_path} to markdown...")
        result = markitdown.convert(str(file_path))
        # Use markdown attribute (DocumentConverterResult has markdown, text_content, title)
        content = result.markdown if hasattr(result, 'markdown') else str(result)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save converted markdown
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  Saved to {output_path}")
        return content
        
    except Exception as e:
        print(f"Error converting {file_path}: {e}")
        # Return empty content but still create a placeholder file
        error_content = f"# Conversion Error\n\nFailed to convert {file_path}: {e}"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(error_content)
        return error_content


def _compute_file_hash(file_path: Path) -> str:
    """Compute SHA‑256 hash of file content."""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def _load_cache(cache_file: Path) -> Dict:
    """Load conversion cache from JSON file."""
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_cache(cache_file: Path, cache: Dict) -> None:
    """Save conversion cache to JSON file."""
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save cache: {e}")


def get_materials_info(directory_path: str) -> List[dict]:
    """
    Get information about all supported files in a directory.
    
    Args:
        directory_path: Path to directory
        
    Returns:
        List of dicts with file info
    """
    directory = Path(directory_path)
    
    if not directory.exists() or not directory.is_dir():
        return []
    
    markdown_extensions = {'.md', '.markdown', '.mdown', '.mkd', '.mkdn', '.mdwn', '.mdt', '.mdtext'}
    convert_extensions = {
        '.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls',
        '.html', '.htm', '.txt', '.csv', '.json', '.xml', '.epub',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
        '.mp3', '.wav', '.m4a', '.flac',
        '.zip'
    }
    
    files_info = []
    
    for file_path in directory.rglob('*'):
        if not file_path.is_file():
            continue
        
        suffix = file_path.suffix.lower()
        file_type = "markdown" if suffix in markdown_extensions else \
                   "convertible" if suffix in convert_extensions else "unsupported"
        
        try:
            size = file_path.stat().st_size
            files_info.append({
                'path': str(file_path.relative_to(directory)),
                'size': size,
                'type': file_type,
                'filename': file_path.name
            })
        except:
            continue
    
    return files_info


if __name__ == "__main__":
    # Test the materials loading
    test_dir = "./test_materials"
    
    print("Testing materials loading...")
    
    # Create a test directory if it doesn't exist
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a test markdown file
    test_md = os.path.join(test_dir, "test.md")
    with open(test_md, 'w', encoding='utf-8') as f:
        f.write("# Test Document\n\nThis is a test markdown file.\n")
    
    # Create a test text file (will be converted)
    test_txt = os.path.join(test_dir, "test.txt")
    with open(test_txt, 'w', encoding='utf-8') as f:
        f.write("This is a plain text file that should be converted.\n")
    
    try:
        content, count, converted = load_materials(
            test_dir,
            output_dir="./test_output/converted",
            cache_conversions=False
        )
        print(f"Loaded {count} file(s)")
        print(f"Converted {len(converted)} file(s)")
        print(f"Content preview (first 300 chars): {content[:300]}...")
        
        files_info = get_materials_info(test_dir)
        print(f"Files info: {files_info}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Clean up
    shutil.rmtree("./test_output", ignore_errors=True)
    os.remove(test_md)
    os.remove(test_txt)
    os.rmdir(test_dir)