"""
Job Description Parser Tool

This module provides utility functions for parsing job descriptions.
"""

import re
import json
from typing import List

from agno.tools import tool
from logger.logger import log_debug, log_error


@tool
def extract_job_title(text: str) -> str:
    """
    Extract job title from job description.
    
    Args:
        text: Job description text
        
    Returns:
        Extracted job title as JSON string
    """
    try:
        title_patterns = [
            r"(?:Job Title|Position|Role):\s*([^\n]+)",
            r"^([^:]+?)(?:Job|Position|Role|Overview)",
            r"([^:]+?)\s+\d+[\+]?\s+[Yy]ears"
        ]
        for pattern in title_patterns:
            title_match = re.search(pattern, text, re.IGNORECASE)
            if title_match:
                return json.dumps(title_match.group(1).strip())

        first_line = text.strip().split('\n')[0]
        if len(first_line) < 100:
            return json.dumps(first_line)

        return json.dumps("Undefined Role")
    except Exception as e:
        log_error(f"Error in extract_job_title: {e}")
        return json.dumps("Undefined Role")


@tool
def extract_required_skills(text: str) -> str:
    """
    Extract required skills and experience years from job description.
    
    Args:
        text: Job description text
        
    Returns:
        JSON string of Dict mapping skills to required years
    """
    try:
        patterns = [
            r"(\w+(?:\s+\w+)?):\s*(\d+)(?:\+)?\s*(?:years|yrs)",
            r"(\w+(?:\s+\w+)?)\s*\((\d+)(?:\+)?\s*(?:years|yrs)?\)",
            r"(\w+(?:\s+\w+)?)\s*(?:with)?\s*(\d+)(?:\+)?\s*(?:years|yrs)",
            r"(\d+)(?:\+)?\s*(?:years|yrs)(?:\s*of)?\s*(\w+(?:\s+\w+)?)",
        ]

        skills = {}
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:
                    skill, years = match
                    if pattern == patterns[-1]:
                        skill, years = years, skill
                    try:
                        skills[skill.strip()] = int(years.strip())
                    except ValueError:
                        skills[skill.strip()] = 1

        if not skills:
            common_skills = [
                "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "PHP", "Ruby", "Go",
                "SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL", "Redis", "AWS", "Azure", "GCP",
                "Docker", "Kubernetes", "ML", "AI", "Machine Learning", "Deep Learning", "NLP",
                "React", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI", "Spring",
                "DevOps", "CI/CD", "Git", "Jenkins", "Terraform", "Ansible", "Agile", "Scrum"
            ]
            for skill in common_skills:
                if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
                    skills[skill] = 1

        return json.dumps(skills)
    except Exception as e:
        log_error(f"Error in extract_required_skills: {e}")
        return json.dumps({})


@tool
def extract_responsibilities(text: str) -> str:
    """
    Extract job responsibilities from job description.
    
    Args:
        text: Job description text
        
    Returns:
        JSON string of list of responsibilities
    """
    try:
        responsibilities = []
        resp_section = re.search(
            r'(?:Responsibilities|RESPONSIBILITIES|Duties|DUTIES|You will).*?(?:Requirements|REQUIREMENTS|Qualifications|QUALIFICATIONS|$)', 
            text, re.DOTALL)

        if resp_section:
            section_text = resp_section.group(0)
            bullets = re.findall(r'(?:•|\*|\-|\d+\.)\s*([^\n•\*\-\d\.][^\n]+)', section_text)
            if bullets:
                responsibilities.extend([bullet.strip() for bullet in bullets])
            else:
                lines = [line.strip() for line in section_text.split('\n') if line.strip()]
                if len(lines) > 1 and re.search(r'responsibilities|duties', lines[0], re.IGNORECASE):
                    responsibilities.extend(lines[1:])
                else:
                    responsibilities.extend(lines)

        return json.dumps(responsibilities)
    except Exception as e:
        log_error(f"Error in extract_responsibilities: {e}")
        return json.dumps([])


@tool
def extract_qualifications(text: str) -> str:
    """
    Extract required qualifications from job description.
    
    Args:
        text: Job description text
        
    Returns:
        JSON string of list of qualifications
    """
    try:
        qualifications = []
        qual_section = re.search(
            r'(?:Requirements|REQUIREMENTS|Qualifications|QUALIFICATIONS).*?(?:Benefits|BENEFITS|$)', 
            text, re.DOTALL)

        if qual_section:
            section_text = qual_section.group(0)
            bullets = re.findall(r'(?:•|\*|\-|\d+\.)\s*([^\n•\*\-\d\.][^\n]+)', section_text)
            if bullets:
                qualifications.extend([bullet.strip() for bullet in bullets])
            else:
                lines = [line.strip() for line in section_text.split('\n') if line.strip()]
                if len(lines) > 1 and re.search(r'requirements|qualifications', lines[0], re.IGNORECASE):
                    qualifications.extend(lines[1:])
                else:
                    qualifications.extend(lines)

        return json.dumps(qualifications)
    except Exception as e:
        log_error(f"Error in extract_qualifications: {e}")
        return json.dumps([])
