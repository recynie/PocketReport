"""
Utility function for loading and concatenating Markdown files.
"""
import os
from pathlib import Path
from typing import List, Tuple


def load_markdown_files(directory_path: str) -> Tuple[str, int]:
    """
    Load and concatenate all Markdown files from a directory.
    
    Args:
        directory_path: Path to directory containing Markdown files
        
    Returns:
        Tuple of (concatenated_content, file_count)
    """
    directory = Path(directory_path)
    
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    if not directory.is_dir():
        raise ValueError(f"Path is not a directory: {directory_path}")
    
    # Find all markdown files
    markdown_extensions = {'.md', '.markdown', '.mdown', '.mkd', '.mkdn', '.mdwn', '.mdt', '.mdtext'}
    markdown_files = []
    
    for file_path in directory.rglob('*'):
        if file_path.suffix.lower() in markdown_extensions and file_path.is_file():
            markdown_files.append(file_path)
    
    if not markdown_files:
        raise FileNotFoundError(f"No Markdown files found in {directory_path}")
    
    # Read and concatenate files
    concatenated_content = []
    for file_path in sorted(markdown_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Add file header
                concatenated_content.append(f"# File: {file_path.relative_to(directory)}\n")
                concatenated_content.append(content)
                concatenated_content.append("\n" + "="*80 + "\n")
        except Exception as e:
            raise IOError(f"Error reading file {file_path}: {e}")
    
    return "\n".join(concatenated_content), len(markdown_files)


def load_markdown_file(file_path: str) -> str:
    """
    Load a single Markdown file.
    
    Args:
        file_path: Path to Markdown file
        
    Returns:
        File content as string
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def get_markdown_files_info(directory_path: str) -> List[dict]:
    """
    Get information about Markdown files in a directory.
    
    Args:
        directory_path: Path to directory
        
    Returns:
        List of dicts with file info
    """
    directory = Path(directory_path)
    
    if not directory.exists() or not directory.is_dir():
        return []
    
    markdown_extensions = {'.md', '.markdown', '.mdown', '.mkd', '.mkdn', '.mdwn', '.mdt', '.mdtext'}
    files_info = []
    
    for file_path in directory.rglob('*'):
        if file_path.suffix.lower() in markdown_extensions and file_path.is_file():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    files_info.append({
                        'path': str(file_path.relative_to(directory)),
                        'size': len(content),
                        'lines': len(content.splitlines()),
                        'filename': file_path.name
                    })
            except:
                # Skip files we can't read
                continue
    
    return files_info


if __name__ == "__main__":
    # Test the markdown loading
    test_dir = "./test_materials"
    
    print("Testing markdown loading...")
    
    # Create a test directory if it doesn't exist
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a test markdown file
    test_file = os.path.join(test_dir, "test.md")
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("# Test Document\n\nThis is a test markdown file.\n")
    
    try:
        content, count = load_markdown_files(test_dir)
        print(f"Loaded {count} file(s)")
        print(f"Content preview (first 200 chars): {content[:200]}...")
        
        files_info = get_markdown_files_info(test_dir)
        print(f"Files info: {files_info}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Clean up
    os.remove(test_file)
    os.rmdir(test_dir)