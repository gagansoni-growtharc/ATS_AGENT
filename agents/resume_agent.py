"""
Resume Parsing Agent (Functional Style)

This module defines resume parsing tools and registers them into an Agent.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json
import datetime

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.vectordb.pgvector import PgVector, SearchType
from agno.embedder.openai import OpenAIEmbedder
from agno.tools import tool

from config.settings import get_settings
from logger.logger import log_info, log_debug, log_error, log_warn

# Load settings
settings = get_settings()

# Initialize Knowledge Base globally
try:
    kb = PDFKnowledgeBase(
        path=str(settings.KB_DIR),
        vector_db=PgVector(
            table_name="resume_kb",
            db_url=settings.PG_CONNECTION_STRING,
            search_type=SearchType.hybrid,
            embedder=OpenAIEmbedder(
                api_key=settings.OPENAI_API_KEY,
                id="text-embedding-3-small"
            ),
        ),
    )
    kb.load(upsert=True)
    log_info("Knowledge base initialized successfully")
except Exception as e:
    log_error(f"Failed to initialize knowledge base: {str(e)}")
    kb = None


@tool(description="Parse a resume PDF file and extract its text content.")
def parse_resume_pdf(pdf_path: str) -> Dict[str, Any]:
    try:
        path = Path(pdf_path)
        if not path.exists():
            log_error(f"PDF file not found: {pdf_path}")
            return {"error": f"File not found: {pdf_path}", "success": False}

        log_debug(f"Parsing resume: {path.name}")

        if kb:
            content = kb.get_document_content(str(path))
            log_debug(f"Extracted {len(content)} characters from {path.name}")
            return {"filename": path.name, "content": content, "success": True}

        log_warn(f"Knowledge base not available, using basic parsing for {path.name}")
        return {"filename": path.name, "content": "PDF content could not be extracted", "success": False}
    except Exception as e:
        log_error(f"Error parsing resume {pdf_path}: {str(e)}")
        return {"error": str(e), "success": False}


@tool(description="Load metadata from a JSON file for a given resume.")
def load_metadata(metadata_path: str) -> Dict[str, Any]:
    try:
        path = Path(metadata_path)
        if not path.exists():
            log_warn(f"Metadata file not found: {metadata_path}")
            return {"metadata": {}, "warning": f"File not found: {metadata_path}", "success": False}

        log_debug(f"Loading metadata: {path.name}")
        with open(path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        if getattr(settings, 'MONGO_URI', None):
            try:
                from pymongo import MongoClient
                client = MongoClient(settings.MONGO_URI)
                db = client.ats_agent
                db.ats_resumes.insert_one({
                    "filename": path.stem,
                    "metadata": metadata,
                    "timestamp": datetime.datetime.now()
                })
                log_info(f"Metadata stored in MongoDB for {path.stem}", source="resume_agent")
            except Exception as e:
                log_warn(f"Failed to store metadata in MongoDB: {str(e)}")

        log_info(f"Metadata loaded for {path.stem}", source="resume_agent")
        return {"metadata": metadata, "success": True}
    except Exception as e:
        log_error(f"Error loading metadata {metadata_path}: {str(e)}")
        return {"error": str(e), "success": False}


@tool(description="Find metadata file matching a given resume.")
def find_matching_metadata(resume_name: str, metadata_folder: str) -> Dict[str, Any]:
    try:
        metadata_path = Path(metadata_folder) / f"{resume_name}.json"
        if metadata_path.exists():
            return {"metadata_path": str(metadata_path), "success": True}
        else:
            log_warn(f"No matching metadata found for {resume_name}")
            return {"warning": f"No metadata for {resume_name}", "success": False}
    except Exception as e:
        log_error(f"Error finding metadata for {resume_name}: {str(e)}")
        return {"error": str(e), "success": False}


@tool(description="Process all resume files in a folder.")
def batch_process_resume_folder(folder_path: str) -> Dict[str, Any]:
    try:
        folder = Path(folder_path)
        if not folder.exists():
            log_error(f"Resume folder not found: {folder_path}")
            return {"error": f"Folder not found: {folder_path}", "success": False}

        pdf_files = list(folder.glob("*.pdf"))
        log_info(f"Found {len(pdf_files)} PDF files in {folder_path}")

        results = []
        for pdf_file in pdf_files:
            result = parse_resume_pdf(str(pdf_file))
            results.append({
                "filename": pdf_file.name,
                "path": str(pdf_file),
                "success": result.get("success", False),
                "error": result.get("error") if not result.get("success") else None
            })

        return {
            "total_files": len(pdf_files),
            "processed_files": len(results),
            "results": results,
            "success": True
        }
    except Exception as e:
        log_error(f"Error batch processing resumes: {str(e)}")
        return {"error": str(e), "success": False}

# 🧠 AGENT DEFINITION
resume_parser_agent = Agent(
    name="ResumeParser",
    role="Parse resumes and extract structured candidate data.",
    model=OpenAIChat(api_key=settings.OPENAI_API_KEY, id="gpt-4o"),
    instructions="""
    Use the tools to process resume PDFs, load and validate metadata, and handle batch operations.
    If metadata is not found, proceed with resume content only.
    Always validate file paths before parsing.
    """,
    tools=[
        parse_resume_pdf,
        load_metadata,
        find_matching_metadata,
        batch_process_resume_folder
    ],
    knowledge=kb,
    add_references=True,
    search_knowledge=True,
    markdown=True
)
