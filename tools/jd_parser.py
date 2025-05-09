"""
Job Description Parser Tool

This module provides utility functions for parsing job descriptions.
"""

import re
from typing import Dict, Any, List

from agno.tools import tool
from logger.logger import log_debug, log_error

@tool
def extract_job_title(text: str) -> str:
    """
    Extract job title from job description.
    
    Args:
        text: Job description text
        
    Returns:
        Extracted job title
    """
    # Common patterns for job titles
    title_patterns = [
        r"(?:Job Title|Position|Role):\s*([^\n]+)",
        r"^([^:]+?)(?:Job|Position|Role|Overview)",
        r"([^:]+?)\s+\d+[\+]?\s+[Yy]ears"
    ]
    
    for pattern in title_patterns:
        title_match = re.search(pattern, text, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()
    
    # If no match found, try to use the first line
    first_line = text.strip().split('\n')[0]
    if len(first_line) < 100:  # Reasonable title length
        return first_line
        
    return "Undefined Role"

@tool
def extract_required_skills(text: str) -> Dict[str, Any]:
    """
    Extract required skills and experience years from job description.
    
    Args:
        text: Job description text
        
    Returns:
        Dict mapping skills to required years of experience
    """
    # Define patterns to match skills with experience requirements
    patterns = [
        r"(\w+(?:\s+\w+)?):\s*(\d+)(?:\+)?\s*(?:years|yrs)",  # Python: 3 years
        r"(\w+(?:\s+\w+)?)\s*\((\d+)(?:\+)?\s*(?:years|yrs)?\)",  # Python (3+)
        r"(\w+(?:\s+\w+)?)\s*(?:with)?\s*(\d+)(?:\+)?\s*(?:years|yrs)",  # Python with 3 years
        r"(\d+)(?:\+)?\s*(?:years|yrs)(?:\s*of)?\s*(\w+(?:\s+\w+)?)",  # 3+ years of Python
    ]
    
    skills = {}
    
    # Search for skills using patterns
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match) == 2:
                skill, years = match
                
                # For patterns like "3 years of Python", swap skill and years
                if pattern == patterns[-1]:
                    skill, years = years, skill
                
                # Clean up skill name
                skill = skill.strip()
                
                # Convert years to integer
                try:
                    years = int(years.strip())
                except ValueError:
                    years = 1  # Default if parsing fails
                
                skills[skill] = years
    
    # If no skills with experience requirements found, extract common skills without years
    if not skills:
        # Common technical skills to look for
        common_skills = [
            "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "PHP", "Ruby", "Go",
            "SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL", "Redis", "AWS", "Azure", "GCP",
            "Docker", "Kubernetes", "ML", "AI", "Machine Learning", "Deep Learning", "NLP",
            "React", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI", "Spring",
            "DevOps", "CI/CD", "Git", "Jenkins", "Terraform", "Ansible", "Agile", "Scrum"
        ]
        
        for skill in common_skills:
            if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
                skills[skill] = 1  # Default to 1 year requirement
    
    return skills

@tool
def extract_responsibilities(text: str) -> List[str]:
    """
    Extract job responsibilities from job description.
    
    Args:
        text: Job description text
        
    Returns:
        List of responsibilities
    """
    responsibilities = []
    
    # Look for responsibilities section
    resp_section = re.search(r'(?:Responsibilities|RESPONSIBILITIES|Duties|DUTIES|You will).*?(?:Requirements|REQUIREMENTS|Qualifications|QUALIFICATIONS|$)', 
                            text, re.DOTALL)
    
    if resp_section:
        section_text = resp_section.group(0)
        
        # Extract bullet points
        bullets = re.findall(r'(?:•|\*|\-|\d+\.)\s*([^\n•\*\-\d\.][^\n]+)', section_text)
        
        if bullets:
            responsibilities.extend([bullet.strip() for bullet in bullets])
        else:
            # If no bullets found, try splitting by newlines
            lines = [line.strip() for line in section_text.split('\n') if line.strip()]
            # Skip header line if it contains "responsibilities" or similar
            if len(lines) > 1 and re.search(r'responsibilities|duties', lines[0], re.IGNORECASE):
                responsibilities.extend(lines[1:])
            else:
                responsibilities.extend(lines)
    
    return responsibilities

@tool
def extract_qualifications(text: str) -> List[str]:
    """
    Extract required qualifications from job description.
    
    Args:
        text: Job description text
        
    Returns:
        List of qualifications
    """
    qualifications = []
    
    # Look for qualifications section
    qual_section = re.search(r'(?:Requirements|REQUIREMENTS|Qualifications|QUALIFICATIONS).*?(?:Benefits|BENEFITS|$)', 
                            text, re.DOTALL)
    
    if qual_section:
        section_text = qual_section.group(0)
        
        # Extract bullet points
        bullets = re.findall(r'(?:•|\*|\-|\d+\.)\s*([^\n•\*\-\d\.][^\n]+)', section_text)
        
        if bullets:
            qualifications.extend([bullet.strip() for bullet in bullets])
        else:
            # If no bullets found, try splitting by newlines
            lines = [line.strip() for line in section_text.split('\n') if line.strip()]
            # Skip header line if it contains "requirements" or similar
            if len(lines) > 1 and re.search(r'requirements|qualifications', lines[0], re.IGNORECASE):
                qualifications.extend(lines[1:])
            else:
                qualifications.extend(lines)
    
    return qualifications