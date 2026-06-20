import logging
from .gemini_client import _get_model, _extract_json, GeminiError
import google.generativeai as genai

logger = logging.getLogger(__name__)

RESUME_PARSER_PROMPT = """
You are an expert AI recruiter. Your task is to extract structured data from the following resume text.
Return ONLY a valid JSON object matching this schema exactly:
{
    "summary": "A brief 2-3 sentence professional summary",
    "skills": ["skill 1", "skill 2", ...],
    "experience": [
        {
            "company": "Company Name",
            "title": "Job Title",
            "duration": "Start Date - End Date",
            "description": "Brief description of responsibilities and achievements"
        }
    ],
    "education": [
        {
            "institution": "University/School Name",
            "degree": "Degree/Major",
            "year": "Graduation Year"
        }
    ]
}

Resume Text:
---
{resume_text}
---
"""

async def parse_resume_with_gemini(resume_text: str) -> dict:
    """
    Parse a raw resume text into structured JSON data using Gemini.
    """
    if not resume_text or not resume_text.strip():
        return {}
        
    try:
        model = _get_model()
        full_prompt = RESUME_PARSER_PROMPT.format(resume_text=resume_text)
        
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=2048,
            ),
        )
        raw_text = response.text
        logger.debug("[Gemini Parser] Raw response: %s", raw_text[:500])
        return _extract_json(raw_text)
        
    except GeminiError as e:
        logger.warning("[Gemini Parser] Parsing failed: %s", e)
        return {}
    except Exception as e:
        logger.warning("[Gemini Parser] Unexpected error: %s", e)
        return {}
