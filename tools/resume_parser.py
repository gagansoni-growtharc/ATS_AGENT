from agno.tools import tool
from pathlib import Path
import json
import datetime
from logger.logger import log_info, log_debug, log_error, log_warn

@tool(description="Parse a resume PDF and extract its text content.")
def parse_resume_pdf(pdf_path: str) -> dict:
    try:
        path = Path(pdf_path)
        if not path.exists():
            return {"success": False, "error": f"File not found: {pdf_path}"}
        content = path.read_text()
        return {"filename": path.name, "content": content, "success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@tool(description="Load resume metadata from a JSON file.")
def load_metadata(metadata_path: str) -> dict:
    try:
        path = Path(metadata_path)
        if not path.exists():
            return {"success": False, "error": f"Metadata file not found: {metadata_path}"}
        metadata = json.loads(path.read_text(encoding="utf-8"))
        return {"metadata": metadata, "success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@tool(description="Find the metadata file that matches a resume name.")
def find_matching_metadata(resume_name: str, metadata_folder: str) -> dict:
    try:
        metadata_path = Path(metadata_folder) / f"{resume_name}.json"
        if metadata_path.exists():
            return {"metadata_path": str(metadata_path), "success": True}
        return {"success": False, "warning": "Matching metadata not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@tool(description="Process all resume PDFs in a folder.")
def batch_process_resume_folder(folder_path: str) -> dict:
    try:
        folder = Path(folder_path)
        if not folder.exists():
            return {"success": False, "error": f"Folder not found: {folder_path}"}
        pdfs = list(folder.glob("*.pdf"))
        results = []
        for pdf in pdfs:
            result = parse_resume_pdf(str(pdf))
            result["filename"] = pdf.name
            results.append(result)
        return {"total_files": len(pdfs), "results": results, "success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
