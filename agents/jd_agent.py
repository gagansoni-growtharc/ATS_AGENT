"""
Job Description Parsing Agent (Functional Style) - Fixed Implementation

This module defines JD parsing tools and bundles them into an Agent.
"""

import datetime
import json
from pathlib import Path
from typing import Dict, Any

from agno.tools import tool
from agno.agent import Agent
from agno.models.openai import OpenAIChat

from tools.jd_parser import (
    extract_job_title,
    extract_required_skills,
    extract_responsibilities,
    extract_qualifications
)

from config.settings import get_settings
from logger.logger import log_info, log_debug, log_error, log_warn

settings = get_settings()


@tool(description="Parse a job description file and extract structured information.")
def parse_job_description(jd_path: str) -> Dict[str, Any]:
    """
    Parse job description from a file path.
    
    Args:
        jd_path: Path to the job description file
        
    Returns:
        Structured job description information
    """
    try:
        path = Path(jd_path)
        if not path.exists():
            log_error(f"Job description file not found: {jd_path}")
            return json.dumps({"error": f"File not found: {jd_path}", "success": False})

        log_debug(f"Parsing job description: {path.name}")
        with open(path, 'r', encoding='utf-8') as f:
            jd_content = f.read()

        # Call the parse_job_description_content function directly
        return _parse_job_description_content(jd_content)
    except Exception as e:
        log_error(f"Error parsing job description {jd_path}: {str(e)}")
        return json.dumps({"error": str(e), "success": False})


@tool(description="Parse job description content directly from string input.")
def parse_job_description_content(jd_content: str) -> Dict[str, Any]:
    """
    Parse job description content directly.
    
    Args:
        jd_content: Job description text content
        
    Returns:
        Structured job description information
    """
    try:
        log_debug(f"Parsing job description content")
        return _parse_job_description_content(jd_content)
    except Exception as e:
        log_error(f"Error parsing job description content: {str(e)}")
        return json.dumps({"error": str(e), "success": False})


def _parse_job_description_content(jd_content: str) -> Dict[str, Any]:
    """
    Internal implementation of job description parsing.
    
    Args:
        jd_content: Job description text content
        
    Returns:
        Structured job description information
    """
    try:
        # Extract job components
        job_title = extract_job_title(jd_content)
        required_skills = extract_required_skills(jd_content)
        responsibilities = extract_responsibilities(jd_content)
        qualifications = extract_qualifications(jd_content)

        # Convert string json to Python objects
        job_title_obj = json.loads(job_title)
        required_skills_obj = json.loads(required_skills)
        responsibilities_obj = json.loads(responsibilities)
        qualifications_obj = json.loads(qualifications)

        # Store in MongoDB if configured
        if getattr(settings, 'MONGO_URI', None):
            try:
                from pymongo import MongoClient
                client = MongoClient(settings.MONGO_URI)
                db = client.ats_agent
                db.ats_job_descriptions.insert_one({
                    "job_title": job_title_obj,
                    "required_skills": required_skills_obj,
                    "responsibilities": responsibilities_obj,
                    "qualifications": qualifications_obj,
                    "timestamp": datetime.datetime.now()
                })
            except Exception as e:
                log_warn(f"Failed to store in MongoDB: {str(e)}")

        log_info(f"Job description parsed: {job_title_obj}", source="jd_agent")

        # Return the structured result
        return json.dumps({
            "job_title": job_title_obj,
            "required_skills": required_skills_obj,
            "responsibilities": responsibilities_obj,
            "qualifications": qualifications_obj,
            "content": jd_content,
            "success": True
        })
    except Exception as e:
        log_error(f"Error in _parse_job_description_content: {str(e)}")
        return json.dumps({"error": str(e), "success": False})


@tool(description="Extract only the required skills from a parsed JD.")
def get_required_skills(parsed_jd: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract only the required skills from a parsed job description.
    
    Args:
        parsed_jd: Previously parsed job description data
        
    Returns:
        Required skills information
    """
    try:
        if isinstance(parsed_jd, str):
            parsed_jd = json.loads(parsed_jd)

        if not parsed_jd.get("success", False):
            log_error("Invalid job description data")
            return json.dumps({"error": "Invalid job description data", "success": False})

        required_skills = parsed_jd.get("required_skills", {})
        if isinstance(required_skills, str):
            required_skills = json.loads(required_skills)

        # Try to extract skills if they're not already available
        if not required_skills and parsed_jd.get("content"):
            required_skills = json.loads(extract_required_skills(parsed_jd["content"]))

        log_info(f"Extracted {len(required_skills)} required skills", source="jd_agent")
        return json.dumps({"skills": required_skills, "success": True})
    except Exception as e:
        log_error(f"Error extracting required skills: {str(e)}")
        return json.dumps({"error": str(e), "success": False})


# 🧠 AGENT DEFINITION
jd_parser_agent = Agent(
    name="JDParser",
    role="Extract structured job requirements from job descriptions.",
    model=OpenAIChat(api_key=settings.OPENAI_API_KEY, id="gpt-4o"),
    instructions="""
    Use the tools provided to extract job title, required skills, responsibilities, 
    and qualifications from a job description file or text content.

    You can either:
    - Use `parse_job_description_content()` if given the text directly.
    - Use `parse_job_description()` if given a file path.

    You may also use `get_required_skills()` to isolate just the skills.
    
    Make sure to handle JSON responses appropriately - all functions return Python dictionaries,
    not JSON strings.
    """,
    tools=[
        parse_job_description,
        parse_job_description_content,
        get_required_skills
    ],
    markdown=True
)