"""
Coordinator Agent (Functional Style)

This module defines coordination and scoring tools and bundles them into an Agent.
"""

import shutil
from pathlib import Path
from typing import Dict, Any, Optional

from agno.tools import tool
from agno.agent import Agent
from agno.models.openai import OpenAIChat

from config.settings import get_settings
from logger.logger import log_info, log_debug, log_error, log_warn

settings = get_settings()


@tool(description="Score a resume against job requirements using LLM.")
def score_resume(
    resume_content: str,
    job_requirements: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
    strict_mode: bool = False
) -> Dict[str, Any]:
    """
    Score a resume against job requirements.
    
    Args:
        resume_content: The content of the resume
        job_requirements: Dictionary of job requirements
        metadata: Optional metadata for the resume
        strict_mode: Whether to use strict matching
        
    Returns:
        Scoring results
    """
    try:
        log_debug(f"Scoring resume with {len(resume_content)} chars against {len(job_requirements)} requirements")

        # Return a framework for the LLM to fill in
        return {
            "score_framework": {
                "skills_match": "To be scored by LLM",
                "experience_match": "To be scored by LLM",
                "education_match": "To be scored by LLM",
                "overall_score": "To be calculated by LLM",
            },
            "metadata_used": metadata is not None,
            "strict_mode": strict_mode,
            "success": True
        }

    except Exception as e:
        log_error(f"Error scoring resume: {str(e)}")
        return {"error": str(e), "success": False}


@tool(description="Rename a resume with its score and move it to a destination folder.")
def rename_and_move_resume(
    source_path: str,
    score: float,
    destination_folder: str = "filtered_resumes"
) -> Dict[str, Any]:
    """
    Rename and move a resume based on its score.
    
    Args:
        source_path: Path to the resume file
        score: Score to include in the filename
        destination_folder: Destination folder
        
    Returns:
        Result of the operation
    """
    try:
        source = Path(source_path)
        if not source.exists():
            log_error(f"Source file not found: {source_path}")
            return {"error": f"File not found: {source_path}", "success": False}

        dest_folder = Path(destination_folder)
        dest_folder.mkdir(parents=True, exist_ok=True)

        score_str = f"{score:.1f}".replace('.', '_')
        new_filename = f"{score_str}__{source.name}"
        destination = dest_folder / new_filename

        shutil.copy2(source, destination)

        log_info(f"Moved resume from {source.name} to {destination}")
        return {
            "original_path": str(source),
            "new_path": str(destination),
            "score": score,
            "success": True
        }

    except Exception as e:
        log_error(f"Error moving resume: {str(e)}")
        return {"error": str(e), "success": False}


@tool(description="Batch process resumes in a folder and prepare them for scoring and filtering.")
def batch_process_resumes(
    resume_folder: str,
    job_requirements: Dict[str, Any],
    metadata_folder: Optional[str] = None,
    top_n: int = 5,
    strict_mode: bool = False
) -> Dict[str, Any]:
    """
    Process multiple resumes and prepare them for scoring.
    
    Args:
        resume_folder: Folder containing resumes
        job_requirements: Dictionary of job requirements
        metadata_folder: Optional folder with metadata
        top_n: Number of top candidates to select
        strict_mode: Whether to use strict matching
        
    Returns:
        Batch processing results
    """
    try:
        folder = Path(resume_folder)
        if not folder.exists():
            log_error(f"Resume folder not found: {resume_folder}")
            return {"error": f"Folder not found: {resume_folder}", "success": False}

        resume_files = [f.name for f in folder.glob("*.pdf")]
        log_info(f"Found {len(resume_files)} resumes in {resume_folder}")

        return {
            "total_resumes": len(resume_files),
            "metadata_available": metadata_folder is not None,
            "top_candidates": [],  # To be completed by LLM
            "success": True
        }

    except Exception as e:
        log_error(f"Error in batch processing: {str(e)}")
        return {"error": str(e), "success": False}


# 🧠 AGENT DEFINITION
coordinator_agent = Agent(
    name="Coordinator",
    role="Coordinate resume evaluation, scoring, and selection.",
    model=OpenAIChat(api_key=settings.OPENAI_API_KEY, id="gpt-4o"),
    instructions="""
    You are responsible for:
    - Scoring resumes based on job requirements and optional metadata
    - Ranking and selecting the top candidates
    - Moving resumes into a filtered folder with their score in the filename

    Use 'score_resume' to compute matches,
    'rename_and_move_resume' to organize results,
    and 'batch_process_resumes' to handle bulk operations.
    """,
    tools=[
        score_resume,
        rename_and_move_resume,
        batch_process_resumes
    ],
    markdown=True
)