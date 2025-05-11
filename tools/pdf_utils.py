"""
PDF Utility Functions

This module provides utility functions for handling PDF files.
"""

import os
from pathlib import Path
from typing import Optional, List

from logger.logger import log_debug, log_warn, log_error


def read_pdf_content(path: Path) -> str:
    """
    Read content from a PDF file using multiple methods with fallbacks.
    
    Args:
        path: Path to the PDF file
        
    Returns:
        Text content of the PDF
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    # Try using PyMuPDF (fitz) if available
    try:
        import fitz
        log_debug(f"Reading PDF with PyMuPDF: {path.name}")
        doc = fitz.open(str(path))
        content = ""
        for page in doc:
            content += page.get_text()
        doc.close()
        if content.strip():  # Check if we got meaningful content
            return content
        else:
            log_warn(f"PyMuPDF returned empty content for {path.name}, trying fallback methods")
    except ImportError:
        log_warn("PyMuPDF not available, falling back to text extraction")
    except Exception as e:
        log_warn(f"PyMuPDF failed: {str(e)}, trying fallback methods")
    
    # Try various text encodings
    for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            log_debug(f"Trying to read with {encoding} encoding")
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
                if content.strip():  # Check if content is not empty
                    return content
        except UnicodeDecodeError:
            continue
    
    # Last resort: binary read with replace for decoding errors
    try:
        log_debug("Using binary read with replacement for decoding errors")
        with open(path, 'rb') as f:
            return f.read().decode('utf-8', errors='replace')
    except Exception as e:
        log_error(f"All PDF reading methods failed for {path.name}: {str(e)}")
        raise RuntimeError(f"Failed to extract text from PDF: {str(e)}")


def read_text_file(path: Path) -> str:
    """
    Read content from a text file trying multiple encodings.
    
    Args:
        path: Path to the text file
        
    Returns:
        Text content of the file
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    # Try various text encodings
    for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    
    # Last resort: binary read with replace for decoding errors
    with open(path, 'rb') as f:
        return f.read().decode('utf-8', errors='replace')


def read_file_content(path: Path) -> str:
    """
    Read content from a file based on its extension.
    
    Args:
        path: Path to the file
        
    Returns:
        Text content of the file
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    # Handle based on file extension
    suffix = path.suffix.lower()
    if suffix == '.pdf':
        return read_pdf_content(path)
    else:
        return read_text_file(path)