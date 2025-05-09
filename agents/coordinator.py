"""
Coordinator Agent

This module contains the coordinator agent that manages the resume matching process.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools import tool

from logger.logger import log_info, log_debug, log_error
from config.settings import Settings

class CoordinatorAgent:
    """Agent for coordinating the resume matching and ranking process."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.agent = self._setup_agent()
        
    @tool
    def score_resume(self, resume_content: str, job_requirements: Dict[str, Any], 
                    metadata: Optional[Dict[str, Any]] = None, 
                    strict_mode: bool = False) -> Dict[str, Any]:
        """
        Score a resume against job requirements.
        
        Args:
            resume_content: The text content of the resume
            job_requirements: Dictionary of job requirements
            metadata: Optional dictionary of resume metadata
            strict_mode: Whether to require all skills to be present
            
        Returns:
            Dict with score and matching details
        """
        try:
            # Note: This is just a placeholder. The actual scoring is done by the LLM
            # based on the resume content, job requirements, and metadata.
            log_debug(f"Scoring resume with {len(resume_content)} chars against {len(job_requirements)} requirements")
            
            # Return structured data for the LLM to fill in
            return {
                "score_framework": {
                    "skills_match": "To be scored by LLM",
                    "experience_match": "To be scored by LLM",
                    "education_match": "To be scored by LLM",
                    "overall_score": "To be calculated by LLM",
                },
                "success": True
            }
            
        except Exception as e:
            log_error(f"Error scoring resume: {str(e)}")
            return {"error": str(e), "success": False}
    
    @tool
    def rename_and_move_resume(self, source_path: str, score: float, 
                              destination_folder: str = "filtered_resumes") -> Dict[str, Any]:
        """
        Rename a resume file with its score and move it to the destination folder.
        
        Args:
            source_path: Path to the original resume file
            score: The calculated match score (0-100)
            destination_folder: Target folder for filtered resumes
            
        Returns:
            Dict with path information
        """
        try:
            source = Path(source_path)
            if not source.exists():
                log_error(f"Source file not found: {source_path}")
                return {"error": f"File not found: {source_path}", "success": False}
                
            # Create destination folder if it doesn't exist
            dest_folder = Path(destination_folder)
            dest_folder.mkdir(parents=True, exist_ok=True)
            
            # Format new filename with score
            score_str = f"{score:.1f}".replace('.', '_')
            new_filename = f"{score_str}__{source.name}"
            destination = dest_folder / new_filename
            
            # Copy file (using copy instead of move to preserve original)
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
    
    @tool
    def batch_process_resumes(self, 
                             resume_folder: str, 
                             job_requirements: Dict[str, Any],
                             metadata_folder: Optional[str] = None, 
                             top_n: int = 5,
                             strict_mode: bool = False) -> Dict[str, Any]:
        """
        Process multiple resumes at once and select top candidates.
        
        Args:
            resume_folder: Path to folder containing resumes
            job_requirements: Dictionary of job requirements
            metadata_folder: Optional path to folder containing metadata files
            top_n: Number of top candidates to select
            strict_mode: Whether to require all skills to be present
            
        Returns:
            Dict with results of batch processing
        """
        try:
            folder = Path(resume_folder)
            if not folder.exists():
                log_error(f"Resume folder not found: {resume_folder}")
                return {"error": f"Folder not found: {resume_folder}", "success": False}
                
            # Return structured data for the LLM to fill in
            # This is a placeholder - actual implementation would process each resume
            resume_files = [f.name for f in folder.glob("*.pdf")]
            log_info(f"Found {len(resume_files)} resumes in {resume_folder}")
            
            batch_results = {
                "total_resumes": len(resume_files),
                "metadata_available": metadata_folder is not None,
                "top_candidates": [],  # To be filled by LLM
                "success": True
            }
            
            return batch_results
            
        except Exception as e:
            log_error(f"Error in batch processing: {str(e)}")
            return {"error": str(e), "success": False}
            
    
    def _setup_agent(self) -> Agent:
        """Set up the coordinator agent."""
        return Agent(
            name="Coordinator",
            role="Coordinate resume matching process and rank candidates",
            model=OpenAIChat(api_key=self.settings.OPENAI_API_KEY, id="gpt-4o"),
            add_name_to_instructions=True,
            instructions=dedent("""
                You are a Coordinator Agent responsible for:
                1. Matching resumes against job requirements
                2. Scoring candidates based on skills, experience, and education
                3. Ranking candidates and selecting the top matches
                4. Moving qualified resumes to a filtered folder
                
                Consider metadata if available, but it's optional.
                Use your judgment and prioritize content-based matching.
            """),
            tools=[
                self.score_resume,
                self.rename_and_move_resume,
                self.batch_process_resumes  # Add the new alias tool
            ],
            markdown=True,
        )