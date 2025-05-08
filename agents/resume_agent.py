"""
Resume Parsing Agent

This module contains the agent responsible for parsing resumes and associated metadata.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.embedder.openai import OpenAIEmbedder
from agno.tools import tool
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.vectordb.pgvector import PgVector, SearchType

from logger.logger import log_info, log_debug, log_error, log_warn
from config.settings import Settings
import datetime

class ResumeAgent:
    """Agent for parsing resume PDFs and metadata files."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.kb = self._setup_knowledge_base()
        self.agent = self._setup_agent()
        
    def _setup_knowledge_base(self) -> PDFKnowledgeBase:
        """Set up the PDF knowledge base with PgVector for semantic search."""
        try:
            kb = PDFKnowledgeBase(
                path=str(self.settings.KB_DIR),  # Changed from 'location' to 'path'
                vector_db=PgVector(
                    table_name="resume_kb",
                    db_url=self.settings.PG_CONNECTION_STRING,
                    search_type=SearchType.hybrid,
                    embedder=OpenAIEmbedder(
                        api_key=self.settings.OPENAI_API_KEY,
                        id="text-embedding-3-small"
                    ),
                ),
            )
            kb.load(upsert=True)
            log_info("Knowledge base initialized successfully")
            return kb
        except Exception as e:
            log_error(f"Failed to initialize knowledge base: {str(e)}")
            # Fallback to None if KB setup fails
            return None
    
    @tool
    def parse_resume_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parse a resume PDF file to extract content.
        
        Args:
            pdf_path: Path to the resume PDF file
            
        Returns:
            Dict with parsed content
        """
        try:
            path = Path(pdf_path)
            if not path.exists():
                log_error(f"PDF file not found: {pdf_path}")
                return {"error": f"File not found: {pdf_path}", "success": False}
                
            log_debug(f"Parsing resume: {path.name}")
            
            # If we have a knowledge base, use it to extract content
            if self.kb:
                # Use knowledge base to extract content
                content = self.kb.get_document_content(str(path))
                log_debug(f"Extracted {len(content)} characters from {path.name}")
                return {
                    "filename": path.name,
                    "content": content,
                    "success": True
                }
            
            # Fallback if knowledge base is not available
            log_warn(f"Knowledge base not available, using basic parsing for {path.name}")
            # TODO: Implement basic PDF parsing fallback
            return {
                "filename": path.name,
                "content": "PDF content could not be extracted",
                "success": False
            }
            
        except Exception as e:
            log_error(f"Error parsing resume {pdf_path}: {str(e)}")
            return {"error": str(e), "success": False}
    
    @tool
    def load_metadata(self, metadata_path: str) -> Dict[str, Any]:
        """
        Load metadata for a resume from a JSON file.
        
        Args:
            metadata_path: Path to the metadata JSON file
            
        Returns:
            Dict with parsed metadata
        """
        try:
            path = Path(metadata_path)
            if not path.exists():
                log_warn(f"Metadata file not found: {metadata_path}")
                return {"metadata": {}, "warning": f"File not found: {metadata_path}", "success": False}
                
            log_debug(f"Loading metadata: {path.name}")
            
            with open(path, 'r', encoding='utf-8') as f:  # Added explicit UTF-8 encoding
                metadata = json.load(f)
                
            # Log to MongoDB if MongoDB URI is available
            if hasattr(self.settings, 'MONGO_URI') and self.settings.MONGO_URI:
                try:
                    from pymongo import MongoClient
                    client = MongoClient(self.settings.MONGO_URI)
                    db = client.ats_agent
                    collection = db.ats_resumes
                    collection.insert_one({
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
    
    @tool
    def find_matching_metadata(self, resume_name: str, metadata_folder: str) -> Dict[str, Any]:
        """
        Find metadata file matching a resume.
        
        Args:
            resume_name: Name of the resume file (without extension)
            metadata_folder: Path to folder containing metadata files
            
        Returns:
            Dict with path to matching metadata file
        """
        try:
            # Check if metadata folder is provided
            if not metadata_folder:
                log_warn(f"No metadata folder provided for {resume_name}")
                return {"warning": "No metadata folder provided", "success": False}
                
            metadata_path = Path(metadata_folder) / f"{resume_name}.json"
            if metadata_path.exists():
                return {
                    "metadata_path": str(metadata_path),
                    "success": True
                }
            else:
                log_warn(f"No matching metadata found for {resume_name}")
                return {"warning": f"No metadata for {resume_name}", "success": False}
        except Exception as e:
            log_error(f"Error finding metadata for {resume_name}: {str(e)}")
            return {"error": str(e), "success": False}
    
    def _setup_agent(self) -> Agent:
        """Set up the resume parsing agent."""
        return Agent(
            name="ResumeParser",
            role="Parse and extract information from resumes and metadata files",
            model=OpenAIChat(api_key=self.settings.OPENAI_API_KEY, id="gpt-4o"),
            add_name_to_instructions=True,
            instructions=dedent("""
                You are a Resume Parsing Agent responsible for:
                1. Extracting information from resume PDFs
                2. Loading and validating resume metadata (if available)
                3. Ensuring all required fields are present
                4. Storing information in MongoDB (if available)
                
                Always validate input files before processing them.
                Metadata is optional - if not available, continue with resume content only.
            """),
            tools=[
                self.parse_resume_pdf, 
                self.load_metadata,
                self.find_matching_metadata
            ],
            knowledge=self.kb,
            add_references=True,
            search_knowledge=True,
            markdown=True,
        )