"""
Resume Parser Tool

This module provides utility functions for parsing resumes.
"""

import re
from pathlib import Path
from typing import Dict, Any, List

from agno.tools import tool
from logger.logger import log_debug, log_error

@tool
def extract_contact_info(text: str) -> Dict[str, Any]:
    """
    Extract contact information from resume text.
    
    Args:
        text: Resume text content
        
    Returns:
        Dict with extracted contact information
    """
    # Extract email address
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_matches = re.findall(email_pattern, text)
    email = email_matches[0] if email_matches else None
    
    # Extract phone number
    phone_pattern = r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    phone_matches = re.findall(phone_pattern, text)
    phone = phone_matches[0] if phone_matches else None
    
    # Extract LinkedIn profile
    linkedin_pattern = r'(?:linkedin\.com/in/|linkedin/|linkedin:)([A-Za-z0-9_-]+)'
    linkedin_matches = re.findall(linkedin_pattern, text, re.IGNORECASE)
    linkedin = linkedin_matches[0] if linkedin_matches else None
    
    return {
        "email": email,
        "phone": phone,
        "linkedin": linkedin
    }

@tool
def extract_education(text: str) -> List[Dict[str, Any]]:
    """
    Extract education information from resume text.
    
    Args:
        text: Resume text content
        
    Returns:
        List of education entries
    """
    education = []
    
    # Common degree patterns
    degree_patterns = [
        r'(B\.?S\.?|Bachelor of Science|Bachelor\'s)',
        r'(M\.?S\.?|Master of Science|Master\'s)',
        r'(Ph\.?D\.?|Doctor of Philosophy)',
        r'(B\.?A\.?|Bachelor of Arts)',
        r'(M\.?B\.?A\.?|Master of Business Administration)'
    ]
    
    # Try to find education sections
    education_section = re.search(r'(?:EDUCATION|Education).*?(?:EXPERIENCE|Experience|SKILLS|Skills|$)', 
                                 text, re.DOTALL)
    
    if education_section:
        section_text = education_section.group(0)
        
        # Extract degree, institution, and year
        for degree_pattern in degree_patterns:
            matches = re.finditer(degree_pattern + r'.*?(\d{4})', section_text, re.DOTALL)
            
            for match in matches:
                degree = match.group(1).strip()
                year = match.group(2).strip()
                
                # Try to extract institution
                inst_match = re.search(r'at|from|in\s+([\w\s]+)', match.group(0))
                institution = inst_match.group(1).strip() if inst_match else "Unknown"
                
                education.append({
                    "degree": degree,
                    "institution": institution,
                    "year": year
                })
    
    return education

@tool
def extract_skills(text: str) -> List[str]:
    """
    Extract skills from resume text.
    
    Args:
        text: Resume text content
        
    Returns:
        List of extracted skills
    """
    # Common skills to look for
    common_skills = [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "PHP", "Ruby", "Go",
        "SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL", "Redis", "AWS", "Azure", "GCP",
        "Docker", "Kubernetes", "ML", "AI", "Machine Learning", "Deep Learning", "NLP",
        "React", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI", "Spring",
        "DevOps", "CI/CD", "Git", "Jenkins", "Terraform", "Ansible", "Agile", "Scrum"
    ]
    
    found_skills = []
    
    # Look for skills section
    skills_section = re.search(r'(?:SKILLS|Skills|TECHNOLOGIES|Technologies).*?(?:EXPERIENCE|Experience|EDUCATION|Education|$)', 
                               text, re.DOTALL)
    
    section_text = skills_section.group(0) if skills_section else text
    
    # Look for common skills
    for skill in common_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', section_text, re.IGNORECASE):
            found_skills.append(skill)
    
    return found_skills