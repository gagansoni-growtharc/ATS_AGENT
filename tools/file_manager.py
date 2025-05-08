"""
File Manager Tool

This module provides utility functions for file operations.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, List

from agno.tools import tool
from logger.logger import log_debug, log_error

@tool
def list_resume_files(folder_path: str, extension: str = "pdf") -> List[str]:
    """
    List all resume files in a folder.
    
    Args:
        folder_path: Path to folder containing resumes
        extension: File extension to filter by (default: pdf)
        
    Returns:
        List of file paths
    """
    try:
        folder = Path(folder_path)
        if not folder.exists():
            log_error(f"Folder not found: {folder_path}")
            return []
            
        files = list(folder.glob(f"*.{extension}"))
        return [str(file) for file in files]
    except Exception as e:
        log_error(f"Error listing files: {str(e)}")
        return []

@tool
def move_file(source_path: str, destination_path: str, create_dirs: bool = True) -> Dict[str, Any]:
    """
    Move a file from source to destination.
    
    Args:
        source_path: Path to source file
        destination_path: Path to destination
        create_dirs: Whether to create destination directories if they don't exist
        
    Returns:
        Dict with success status
    """
    try:
        source = Path(source_path)
        destination = Path(destination_path)
        
        if not source.exists():
            log_error(f"Source file not found: {source_path}")
            return {"success": False, "error": "Source file not found"}
            
        # Create destination directory if it doesn't exist
        if create_dirs:
            os.makedirs(destination.parent, exist_ok=True)
            
        # Move the file
        shutil.move(source, destination)
        
        log_debug(f"Moved file: {source.name} -> {destination.name}")
        return {"success": True, "source": str(source), "destination": str(destination)}
    except Exception as e:
        log_error(f"Error moving file: {str(e)}")
        return {"success": False, "error": str(e)}

@tool
def copy_file(source_path: str, destination_path: str, create_dirs: bool = True) -> Dict[str, Any]:
    """
    Copy a file from source to destination.
    
    Args:
        source_path: Path to source file
        destination_path: Path to destination
        create_dirs: Whether to create destination directories if they don't exist
        
    Returns:
        Dict with success status
    """
    try:
        source = Path(source_path)
        destination = Path(destination_path)
        
        if not source.exists():
            log_error(f"Source file not found: {source_path}")
            return {"success": False, "error": "Source file not found"}
            
        # Create destination directory if it doesn't exist
        if create_dirs:
            os.makedirs(destination.parent, exist_ok=True)
            
        # Copy the file
        shutil.copy2(source, destination)
        
        log_debug(f"Copied file: {source.name} -> {destination.name}")
        return {"success": True, "source": str(source), "destination": str(destination)}
    except Exception as e:
        log_error(f"Error copying file: {str(e)}")
        return {"success": False, "error": str(e)}

@tool
def rename_file(file_path: str, new_name: str) -> Dict[str, Any]:
    """
    Rename a file.
    
    Args:
        file_path: Path to file
        new_name: New filename (without path)
        
    Returns:
        Dict with success status
    """
    try:
        path = Path(file_path)
        if not path.exists():
            log_error(f"File not found: {file_path}")
            return {"success": False, "error": "File not found"}
            
        new_path = path.parent / new_name
        
        # Rename the file
        path.rename(new_path)
        
        log_debug(f"Renamed file: {path.name} -> {new_name}")
        return {"success": True, "original": str(path), "new": str(new_path)}
    except Exception as e:
        log_error(f"Error renaming file: {str(e)}")
        return {"success": False, "error": str(e)}

@tool
def create_directory(dir_path: str) -> Dict[str, Any]:
    """
    Create a directory if it doesn't exist.
    
    Args:
        dir_path: Path to directory
        
    Returns:
        Dict with success status
    """
    try:
        path = Path(dir_path)
        os.makedirs(path, exist_ok=True)
        
        log_debug(f"Created directory: {dir_path}")
        return {"success": True, "path": str(path)}
    except Exception as e:
        log_error(f"Error creating directory: {str(e)}")
        return {"success": False, "error": str(e)}