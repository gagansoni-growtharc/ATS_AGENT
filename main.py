"""
ATS Resume Filtering System: Main Entry Point

This script orchestrates the entire ATS filtering system, parsing resumes and job descriptions,
ranking candidates, and logging results to both MongoDB and the console.
"""
import os
import argparse
from dotenv import load_dotenv
from pathlib import Path

from agno.team.team import Team
from agents.resume_agent import ResumeAgent
from agents.jd_agent import JDAgent
from agents.coordinator import CoordinatorAgent
from logger.logger import logger, log_info, log_debug
from config.settings import get_settings

def parse_args():
    parser = argparse.ArgumentParser(description="ATS Resume Filtering System")
    parser.add_argument("--folder", type=str, required=True, help="Path to folder containing resumes")
    parser.add_argument("--jd", type=str, required=True, help="Path to job description file")
    parser.add_argument("--metadata", type=str, required=False, help="Path to metadata folder (optional)")
    parser.add_argument("--strict", action="store_true", help="Require all JD skills to be present")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()

def main():
    # Load environment variables
    load_dotenv()
    # Parse command-line arguments
    args = parse_args()
    
    # Load settings
    settings = get_settings()
    
    # Configure logging based on debug flag
    if args.debug:
        logger.setLevel("DEBUG")
    
    log_info("Starting ATS Resume Filtering System", center=True)
    
    # Initialize agents
    resume_agent = ResumeAgent(settings)
    jd_agent = JDAgent(settings)
    coordinator = CoordinatorAgent(settings)
    
    # Create the team
    ats_team = Team(
        name="ATS_Team",
        mode="coordinate",
        success_criteria="Successfully match and rank candidates based on job description requirements",
        members=[resume_agent.agent, jd_agent.agent, coordinator.agent],
        instructions=[
            "Process the job description text provided directly in the message, not as a file path",
            "Process resumes from the folder path provided using the batch_process_resume_folder tool",
            "Score and rank candidates based on metadata and content",
            "Move top candidates to filtered folder",
            "Log all actions to MongoDB and console"
        ],
        enable_agentic_context=True,
        share_member_interactions=True,
        show_tool_calls=True,
        debug_mode=args.debug,
        markdown=True,
        show_members_responses=True,
    )
    
    # Process job description
    job_description_path = Path(args.jd)
    if not job_description_path.exists():
        logger.error(f"Job description file not found: {args.jd}")
        return

    # Try different encodings to read the file
    encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    jd_content = None
    
    for encoding in encodings_to_try:
        try:
            with open(job_description_path, 'r', encoding=encoding) as f:
                jd_content = f.read()
            log_info(f"Successfully read job description file using {encoding} encoding")
            break
        except UnicodeDecodeError:
            log_debug(f"Failed to read with {encoding} encoding, trying next...")
    
    if jd_content is None:
        logger.error("Failed to read job description file with any encoding, using binary mode")
        # Last resort: read as binary and decode with errors='replace'
        with open(job_description_path, 'rb') as f:
            jd_content = f.read().decode('utf-8', errors='replace')
    
    # Process resumes and metadata
    resume_folder = Path(args.folder)
    
    if not resume_folder.exists():
        logger.error(f"Resume folder not found: {args.folder}")
        return
    
    # Build the message based on available parameters
    message = f"""
    IMPORTANT: The job description content is provided directly below - please parse this content directly, not as a file path:
    
    {jd_content}
    
    Resume folder: {str(resume_folder)}
    Please process all resumes in this folder using the batch_process_resume_folder tool.
    """
    
    # Handle metadata folder (optional)
    if args.metadata:
        metadata_folder = Path(args.metadata)
        if metadata_folder.exists():
            message += f"\nMetadata folder: {str(metadata_folder)}"
        else:
            log_info(f"Metadata folder not found: {args.metadata}, continuing without metadata")
    else:
        log_info("No metadata folder specified, continuing without metadata")
    
    message += f"""
    
    Strict mode: {"enabled" if args.strict else "disabled"}
    
    Process steps:
    1. Parse the job description content provided above using parse_job_description_content
    2. Process all resumes in the folder using batch_process_resume_folder
    3. Match resumes against the job requirements
    4. Rank the candidates and move top matches to filtered_resumes folder
    5. Log all actions
    """
    
    # Execute the workflow
    log_info("Starting ATS workflow", center=True)
    ats_team.print_response(
        message=message,
        stream=True,
        stream_intermediate_steps=True,
    )
    
    log_info("ATS workflow completed", center=True)

if __name__ == "__main__":
    main()