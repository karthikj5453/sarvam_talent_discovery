"""
Gemini LLM Client
Wraps Google's Gemini API for:
  1. Competency scoring (reads transcript → produces 6 scores + justifications)
  2. Follow-up question generation (reads intro transcript → generates questions)

Requires: GEMINI_API_KEY in .env
Model: gemini-2.0-flash (fast, long-context, free-tier friendly)
"""
import json
import logging
import re
from typing import Optional

import google.generativeai as genai

from config import settings

logger = logging.getLogger(__name__)

# ─── INIT ─────────────────────────────────────────────────────

def _get_model():
    """Configure and return a Gemini model instance."""
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY in ("your_gemini_api_key_here", ""):
        raise GeminiError("GEMINI_API_KEY is not set. Add it to backend/.env")
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(settings.GEMINI_MODEL)


class GeminiError(Exception):
    """Raised when Gemini API call fails or key is missing."""


# ─── JSON EXTRACTION ──────────────────────────────────────────

def _extract_json(text: str) -> dict:
    """
    Parse JSON from a Gemini response that may contain markdown fences.
    Tries multiple strategies before giving up.
    """
    # Strategy 1: direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Strategy 2: extract from ```json ... ``` block
    match = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Strategy 3: find the first {...} block
    match = re.search(r"\{[\s\S]+\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise GeminiError(f"Could not parse JSON from Gemini response: {text[:300]}")


# ─── COMPETENCY SCORING ───────────────────────────────────────

async def score_competencies_with_gemini(
    system_prompt: str,
    user_prompt: str,
) -> dict:
    """
    Send the competency scoring prompt to Gemini and return parsed JSON.

    Args:
        system_prompt: The role/context prompt (from competency_scorer.py)
        user_prompt:   The transcript + scoring instructions

    Returns:
        dict with keys: scores, justifications, flags, hr_summary

    Raises:
        GeminiError if the API call fails or key is missing.
    """
    try:
        model = _get_model()
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Use generate_content with JSON output instruction
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,        # Low temp for consistent scoring
                max_output_tokens=2048,
            ),
        )
        raw_text = response.text
        logger.debug(f"[Gemini] Raw scoring response (first 500): {raw_text[:500]}")
        return _extract_json(raw_text)

    except GeminiError:
        raise
    except Exception as e:
        raise GeminiError(f"Gemini API call failed: {e}") from e


# ─── FOLLOW-UP QUESTION GENERATION ───────────────────────────

QUESTION_SYSTEM_PROMPT = """
You are an expert technical interviewer for an Indian tech company.
Based on the candidate's introduction, generate {n} highly relevant follow-up interview questions.

Role: {job_title}
Required Skills: {required_skills}

{github_context}

Rules:
- Questions must be specific to what the candidate mentioned, not generic
- Mix technical depth, problem-solving, and behavioral questions
- Keep each question concise (1-2 sentences max)
- Return ONLY a JSON array of strings — no extra text
"""

QUESTION_USER_PROMPT = """
## Candidate's Introduction

{intro_transcript}

---

Generate {n} follow-up questions as a JSON array.

Example format:
["Question 1?", "Question 2?", "Question 3?"]
"""


async def generate_followup_questions(
    intro_transcript: str,
    job_title: str,
    required_skills: list,
    github_url: Optional[str] = None,
    n: int = 3,
) -> list[str]:
    """
    Generate n follow-up interview questions based on the candidate's intro.

    Returns:
        list of question strings

    Falls back to generic questions if Gemini is unavailable.
    """
    try:
        model = _get_model()
        skills_str = ", ".join(required_skills) if required_skills else "General Software Engineering"

        github_ctx = ""
        if github_url:
            github_data = _fetch_github_context(github_url)
            if github_data:
                github_ctx = f"GitHub Context (from {github_url}):\n{github_data}\nPlease ask one hyper-specific question related to one of these repositories."

        system = QUESTION_SYSTEM_PROMPT.format(
            n=n,
            job_title=job_title,
            required_skills=skills_str,
            github_context=github_ctx,
        )
        user = QUESTION_USER_PROMPT.format(
            intro_transcript=intro_transcript,
            n=n,
        )

        full_prompt = f"{system}\n\n{user}"
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,        # Slightly higher for question variety
                max_output_tokens=512,
            ),
        )
        raw_text = response.text
        logger.debug(f"[Gemini] Questions response: {raw_text[:300]}")

        # Parse the JSON array
        # Try direct parse first
        try:
            questions = json.loads(raw_text.strip())
            if isinstance(questions, list):
                return [str(q) for q in questions[:n]]
        except json.JSONDecodeError:
            pass

        # Extract from markdown fence
        match = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw_text)
        if match:
            try:
                questions = json.loads(match.group(1).strip())
                if isinstance(questions, list):
                    return [str(q) for q in questions[:n]]
            except json.JSONDecodeError:
                pass

        # Extract array pattern
        match = re.search(r"\[[\s\S]+\]", raw_text)
        if match:
            try:
                questions = json.loads(match.group(0))
                if isinstance(questions, list):
                    return [str(q) for q in questions[:n]]
            except json.JSONDecodeError:
                pass

        logger.warning("[Gemini] Could not parse questions JSON, using fallback")

    except GeminiError as e:
        logger.warning(f"[Gemini] Question generation failed: {e} — using fallback questions")
    except Exception as e:
        logger.warning(f"[Gemini] Unexpected error: {e} — using fallback questions")

    # ── Fallback: generic questions ─────────────────────────
    return _fallback_questions(job_title, n)

import urllib.request
import urllib.error

def _fetch_github_context(github_url: str) -> str:
    """Extract username from URL and fetch top 3 repos from GitHub API."""
    try:
        # crude extraction
        parts = github_url.rstrip("/").split("/")
        username = parts[-1]
        if not username:
            return ""
            
        url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=3"
        req = urllib.request.Request(url, headers={'User-Agent': 'Sarvam-Talent-AI'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            
        repos = []
        for r in data:
            desc = r.get("description") or "No description"
            lang = r.get("language") or "Unknown"
            repos.append(f"- {r['name']} ({lang}): {desc}")
            
        return "\n".join(repos)
    except Exception as e:
        logger.warning(f"[GitHub] Failed to fetch context for {github_url}: {e}")
        return ""

def _fallback_questions(job_title: str, n: int = 3) -> list[str]:
    """Generic fallback questions when Gemini is unavailable."""
    all_questions = [
        f"Tell me about a challenging technical problem you solved in your most recent role related to {job_title}.",
        "Describe a project where you had to make an important architectural decision. What was your reasoning?",
        "How do you approach debugging a production issue that you've never seen before?",
        "Tell me about a time you had to ship something under tight deadlines. How did you prioritize?",
        "What aspect of your work are you most proud of, and why?",
    ]
    return all_questions[:n]
