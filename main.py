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
from agents.resume_agent import resume_parser_agent
from agents.jd_agent import jd_parser_agent
from agents.coordinator import coordinator_agent
from logger.logger import logger, log_info, log_debug, log_error
from config.settings import get_settings
from tools.pdf_utils import read_file_content

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
    
    # Create the team
    ats_team = Team(
        name="ATS_Team",
        mode="coordinate",
        success_criteria="Successfully match and rank candidates based on job description requirements",
        members=[resume_parser_agent, jd_parser_agent, coordinator_agent],
        instructions=[
            "Process the job description using the JDParser's parse_job_description_content tool",
            "Process resumes from the folder path provided using the ResumeParser's batch_process_resume_folder tool",
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

    # Read job description content using our PDF utility
    try:
        jd_content = read_file_content(job_description_path)
        log_info(f"Successfully read job description file: {job_description_path.name}")
    except Exception as e:
        log_error(f"Error reading job description file: {str(e)}")
        return

    if jd_content is None:
        logger.error("Failed to read job description file with any encoding, using binary mode")
        with open(job_description_path, 'rb') as f:
            jd_content = f.read().decode('utf-8', errors='replace')

    # Process resumes and metadata
    resume_folder = Path(args.folder)
    if not resume_folder.exists():
        logger.error(f"Resume folder not found: {args.folder}")
        return

    # Build the message for the ATS team
    message = f"""
    I need to process job applications for the following job description:
    
    ```
    {jd_content}
    ```
    
    Please analyze the job requirements and then process the candidate resumes in this folder: {str(resume_folder)}
    
    Follow these steps:
    1. First, use the JDParser to extract key information from the job description text I've provided
    2. Then, use the ResumeParser to process all resumes from the folder at: {str(resume_folder)}
    3. Finally, use the Coordinator to match and rank candidates
    """

    # Handle metadata folder (optional)
    if args.metadata:
        metadata_folder = Path(args.metadata)
        if metadata_folder.exists():
            message += f"\n\nAdditional candidate metadata is available in this folder: {str(metadata_folder)}"
        else:
            log_info(f"Metadata folder not found: {args.metadata}, continuing without metadata")

    message += f"\n\nStrict mode is {'enabled' if args.strict else 'disabled'} for skills matching."

    try:
        # Execute the workflow
        log_info("Starting ATS workflow", center=True)
        ats_team.print_response(
            message=message,
            stream=True,
            stream_intermediate_steps=True,
        )
        log_info("ATS workflow completed", center=True)
    except Exception as e:
        log_error(f"Error occurred while processing ATS workflow: {str(e)}")

if __name__ == "__main__":
    main()
