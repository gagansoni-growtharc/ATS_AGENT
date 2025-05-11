from agno.tools import tool
from pathlib import Path
import json
from logger.logger import log_info, log_debug, log_error, log_warn
from typing import Dict
from tools.pdf_utils import read_pdf_content

def safe_read_pdf(path: Path) -> str:
    """Safely read the content of a PDF file using the centralized PDF utility."""
    try:
        return read_pdf_content(path)
    except Exception as e:
        log_error(f"Error in PDF utility: {str(e)}, falling back to basic methods")
        try:
            return path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    return path.read_text(encoding=encoding)
                except UnicodeDecodeError:
                    continue
            return path.read_bytes().decode('utf-8', errors='replace')
        
def success_response(data: Dict) -> str:
    data["success"] = True
    return json.dumps(data)

def error_response(message: str, extra: Dict = {}) -> str:
    return json.dumps({"success": False, "error": message, **extra})

@tool(description="Parse a resume PDF and extract its text content.")
def parse_resume_pdf(pdf_path: str) -> str:
    path = Path(pdf_path)
    if not path.exists():
        log_error(f"[parse_resume_pdf] File not found: {pdf_path}")
        return error_response(f"File not found: {pdf_path}")

    try:
        content = safe_read_pdf(path)
        log_debug(f"[parse_resume_pdf] Extracted {len(content)} characters from {path.name}")
        return success_response({"filename": path.name, "content": content})
    except Exception as e:
        log_error(f"[parse_resume_pdf] Error: {str(e)}")
        return error_response(str(e))

@tool(description="Load metadata from a JSON file for a given resume.")
def load_metadata(metadata_path: str) -> str:
    path = Path(metadata_path)
    if not path.exists():
        log_warn(f"[load_metadata] Metadata file not found: {metadata_path}")
        return error_response(f"File not found: {metadata_path}", {"metadata": {}, "warning": f"Missing metadata"})

    try:
        with open(path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        log_info(f"[load_metadata] Metadata loaded for {path.stem}", source="resume_agent")
        return success_response({"metadata": metadata})
    except Exception as e:
        log_error(f"[load_metadata] Error: {str(e)}")
        return error_response(str(e))

@tool(description="Find metadata file matching a given resume.")
def find_matching_metadata(resume_name: str, metadata_folder: str) -> str:
    try:
        metadata_path = Path(metadata_folder) / f"{resume_name}.json"
        if metadata_path.exists():
            return success_response({"metadata_path": str(metadata_path)})
        else:
            log_warn(f"[find_matching_metadata] No match for {resume_name}")
            return error_response(f"No metadata for {resume_name}", {"warning": "Missing metadata"})
    except Exception as e:
        log_error(f"[find_matching_metadata] Error: {str(e)}")
        return error_response(str(e))

@tool(description="Process all resume files in a folder.")
def batch_process_resume_folder(folder_path: str) -> str:
    folder = Path(folder_path)
    if not folder.exists():
        log_error(f"[batch_process_resume_folder] Folder not found: {folder_path}")
        return error_response(f"Folder not found: {folder_path}")

    try:
        pdf_files = list(folder.glob("*.pdf"))
        log_info(f"[batch_process_resume_folder] Found {len(pdf_files)} files")
        results = []

        for pdf_file in pdf_files:
            try:
                content = safe_read_pdf(pdf_file)
                results.append({
                    "filename": pdf_file.name,
                    "path": str(pdf_file),
                    "content": content,
                    "success": True
                })
            except Exception as e:
                results.append({
                    "filename": pdf_file.name,
                    "path": str(pdf_file),
                    "success": False,
                    "error": str(e)
                })

        return success_response({
            "total_files": len(pdf_files),
            "processed_files": len(results),
            "results": results
        })
    except Exception as e:
        log_error(f"[batch_process_resume_folder] Error: {str(e)}")
        return error_response(str(e))
