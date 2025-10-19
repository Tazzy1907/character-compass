"""
Local file loader for reading story text files.
Replaces Google Docs API functionality with local file operations.
"""

from pathlib import Path
import os
from typing import List, Dict

# Stories directory - located at backend/stories/
STORIES_DIR = Path(__file__).parent.parent / "stories"


def get_story_content(file_path: str) -> str:
    """
    Read content from a txt file in the stories directory.
    
    Args:
        file_path: Name of the txt file (e.g., "story1.txt")
        
    Returns:
        str: Content of the file
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    full_path = STORIES_DIR / file_path
    
    if not full_path.exists():
        raise FileNotFoundError(f"Story file not found: {file_path}")
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content:
            print(f"Warning: File {file_path} is empty")
        
        return content
    except Exception as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def get_file_modified_time(file_path: str) -> float:
    """
    Get last modification time of a file.
    
    Args:
        file_path: Name of the txt file (e.g., "story1.txt")
        
    Returns:
        float: Unix timestamp of last modification
    """
    full_path = STORIES_DIR / file_path
    
    if not full_path.exists():
        raise FileNotFoundError(f"Story file not found: {file_path}")
    
    return os.path.getmtime(full_path)


def scan_stories_folder() -> List[Dict[str, any]]:
    """
    Scan stories folder and return list of txt files with metadata.
    
    Returns:
        List of dicts containing file_path, title, and modified_time
    """
    # Create directory if it doesn't exist
    STORIES_DIR.mkdir(exist_ok=True)
    
    stories = []
    for file in STORIES_DIR.glob("*.txt"):
        stories.append({
            "file_path": file.name,
            "title": file.stem,  # Filename without extension
            "modified_time": os.path.getmtime(file)
        })
    
    # Sort by name
    stories.sort(key=lambda x: x['file_path'])
    
    return stories


def ensure_stories_directory():
    """Ensure the stories directory exists."""
    STORIES_DIR.mkdir(exist_ok=True)
    print(f"Stories directory: {STORIES_DIR}")

