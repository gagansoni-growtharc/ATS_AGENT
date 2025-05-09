"""
Job Description Agent

This module contains the agent responsible for parsing job descriptions and extracting requirements.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools import tool

from logger.logger import log_info, log_debug, log_error, log_warn
from config.settings import Settings
import datetime

# Import the JD parsing tools
from tools.jd_parser import extract_job_title, extract_required_skills, extract_responsibilities, extract_qualifications

class JDAgent:
    """Agent for parsing job descriptions and extracting requirements."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.agent = self._setup_agent()
    
    @tool
    def parse_job_description(self, jd_path: str) -> Dict[str, Any]:
        """
        Parse a job description file to extract content and requirements.
        
        Args:
            jd_path: Path to the job description file
            
        Returns:
            Dict with parsed content
        """
        try:
            path = Path(jd_path)
            if not path.exists():
                log_error(f"Job description file not found: {jd_path}")
                return {"error": f"File not found: {jd_path}", "success": False}
                
            log_debug(f"Parsing job description: {path.name}")
            
            # Read the file with utf-8 encoding
            with open(path, 'r', encoding='utf-8') as f:
                jd_content = f.read()
            
            # Extract job title
            job_title = extract_job_title(jd_content)
            
            # Extract required skills
            required_skills = extract_required_skills(jd_content)
            
            # Extract responsibilities
            responsibilities = extract_responsibilities(jd_content)
            
            # Extract qualifications
            qualifications = extract_qualifications(jd_content)
            
            # Log to MongoDB if available
            if hasattr(self.settings, 'MONGO_URI') and self.settings.MONGO_URI:
                try:
                    from pymongo import MongoClient
                    client = MongoClient(self.settings.MONGO_URI)
                    db = client.ats_agent
                    collection = db.ats_job_descriptions
                    collection.insert_one({
                        "filename": path.name,
                        "job_title": job_title,
                        "required_skills": required_skills,
                        "responsibilities": responsibilities,
                        "qualifications": qualifications,
                        "timestamp": datetime.datetime.now()
                    })
                except Exception as e:
                    log_warn(f"Failed to store in MongoDB: {str(e)}")
            
            log_info(f"Job description parsed: {job_title}", source="jd_agent")
            
            return {
                "filename": path.name,
                "job_title": job_title,
                "required_skills": required_skills,
                "responsibilities": responsibilities,
                "qualifications": qualifications,
                "content": jd_content,
                "success": True
            }
            
        except Exception as e:
            log_error(f"Error parsing job description {jd_path}: {str(e)}")
            return {"error": str(e), "success": False}
    
    @tool
    def parse_job_description_content(self, jd_content: str) -> Dict[str, Any]:
        """
        Parse job description content directly.
        
        Args:
            jd_content: The text content of the job description
                
        Returns:
            Dict with parsed content
        """
        try:
            log_debug(f"Parsing job description content")
            
            # Extract job title
            job_title = extract_job_title(jd_content)
            
            # Extract required skills
            required_skills = extract_required_skills(jd_content)
            
            # Extract responsibilities
            responsibilities = extract_responsibilities(jd_content)
            
            # Extract qualifications
            qualifications = extract_qualifications(jd_content)
            
            # Log to MongoDB if available
            if hasattr(self.settings, 'MONGO_URI') and self.settings.MONGO_URI:
                try:
                    from pymongo import MongoClient
                    client = MongoClient(self.settings.MONGO_URI)
                    db = client.ats_agent
                    collection = db.ats_job_descriptions
                    collection.insert_one({
                        "job_title": job_title,
                        "required_skills": required_skills,
                        "responsibilities": responsibilities,
                        "qualifications": qualifications,
                        "timestamp": datetime.datetime.now()
                    })
                except Exception as e:
                    log_warn(f"Failed to store in MongoDB: {str(e)}")
            
            log_info(f"Job description parsed: {job_title}", source="jd_agent")
            
            return {
                "job_title": job_title,
                "required_skills": required_skills,
                "responsibilities": responsibilities,
                "qualifications": qualifications,
                "content": jd_content,
                "success": True
            }
            
        except Exception as e:
            log_error(f"Error parsing job description content: {str(e)}")
            return {"error": str(e), "success": False}
    
    @tool
    def get_required_skills(self, parsed_jd: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract required skills from parsed job description.
        
        Args:
            parsed_jd: Parsed job description data
            
        Returns:
            Dict mapping skills to required years of experience
        """
        try:
            if not parsed_jd.get("success", False):
                log_error("Invalid job description data")
                return {"error": "Invalid job description data", "success": False}
            
            required_skills = parsed_jd.get("required_skills", {})
            
            if not required_skills:
                # If no skills were extracted by the parser, try to extract them from content
                content = parsed_jd.get("content", "")
                if content:
                    required_skills = extract_required_skills(content)
            
            log_info(f"Extracted {len(required_skills)} required skills", source="jd_agent")
            return {"skills": required_skills, "success": True}
            
        except Exception as e:
            log_error(f"Error extracting required skills: {str(e)}")
            return {"error": str(e), "success": False}
    
    def _setup_agent(self) -> Agent:
        """Set up the job description parsing agent."""
        return Agent(
            name="JDParser",
            role="Parse job descriptions and extract requirements",
            model=OpenAIChat(api_key=self.settings.OPENAI_API_KEY, id="gpt-4o"),
            add_name_to_instructions=True,
            instructions=dedent("""
                You are a Job Description Parsing Agent responsible for:
                1. Extracting information from job description files or direct text content
                2. Identifying required skills and experience levels
                3. Extracting responsibilities and qualifications
                4. Providing structured data for resume matching
                
                IMPORTANT: You can process job descriptions either from a file path OR from direct text content.
                If you are given direct text content, use the parse_job_description_content tool.
                If you are given a file path, use the parse_job_description tool.
            """),
            tools=[
                self.parse_job_description,
                self.parse_job_description_content,
                self.get_required_skills
            ],
            markdown=True,
        )