from agno.tools import tool
from tools.jd_parser import extract_job_title, extract_required_skills, extract_responsibilities, extract_qualifications
import datetime

@tool(description="Parse a job description from text content.")
def parse_job_description_content(jd_content: str) -> dict:
    try:
        return {
            "job_title": extract_job_title(jd_content),
            "required_skills": extract_required_skills(jd_content),
            "responsibilities": extract_responsibilities(jd_content),
            "qualifications": extract_qualifications(jd_content),
            "content": jd_content,
            "success": True
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@tool(description="Extract required skills from parsed job description.")
def get_required_skills(parsed_jd: dict) -> dict:
    try:
        skills = parsed_jd.get("required_skills")
        if not skills and "content" in parsed_jd:
            skills = extract_required_skills(parsed_jd["content"])
        return {"skills": skills, "success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
