"""
Competency Scoring Prompt — Sarvam Talent Discovery Engine

This is the master prompt used to score a candidate across 6 competency dimensions.
Used in: services/pipeline/evaluator.py → _score_competencies()

Variables to fill (Python .format() style):
  {job_title}        - e.g. "ML Engineer"
  {required_skills}  - e.g. "Python, LangGraph, RAG, PostgreSQL"
  {transcript}       - Full English transcript of intro + all answers
  {w_technical}      - Weight for technical_depth (e.g. 0.25)
  {w_first}          - Weight for first_principles
  {w_shipping}       - Weight for shipping_velocity
  {w_ownership}      - Weight for ownership_signals
  {w_curiosity}      - Weight for curiosity_depth
  {w_multilingual}   - Weight for multilingual_fluency
  {w_eq}             - Weight for eq_score
"""

SYSTEM_PROMPT = """
You are an expert technical interviewer and talent evaluator for an Indian tech company.
Your task is to evaluate a candidate's screening interview transcript for the role of {job_title}.

The required skills for this role are: {required_skills}

You will score the candidate on 7 competency dimensions. Each score is from 0 to 10.
Be calibrated — a 10 is exceptional, a 5 is adequate, a 3 is concerning.

IMPORTANT: Return ONLY valid JSON. No extra text before or after the JSON block.
"""

USER_PROMPT = """
## Candidate Transcript

{transcript}

---

## Scoring Task

Score the candidate on each dimension below (0-10) with a brief justification (1-2 sentences):

1. **technical_depth** (weight: {w_technical})
   - Depth and accuracy of technical knowledge
   - Appropriate use of domain-specific concepts
   - Evidence of hands-on expertise

2. **first_principles** (weight: {w_first})
   - Ability to reason from fundamentals rather than patterns
   - Can explain *why* something works, not just *how*
   - Shows structured analytical thinking

3. **shipping_velocity** (weight: {w_shipping})
   - Track record of delivering complete, working software
   - Evidence of shipping to real users in production
   - Bias for completion over perfection

4. **ownership_signals** (weight: {w_ownership})
   - Takes initiative without being asked
   - Accountability for outcomes (not just tasks)
   - Goes beyond their defined scope when needed

5. **curiosity_depth** (weight: {w_curiosity})
   - Genuine intellectual curiosity about their domain
   - Evidence of self-directed learning
   - Explores topics outside their immediate job requirements

6. **multilingual_fluency** (weight: {w_multilingual})
   - Clarity and coherence of communication across languages
   - Comfort expressing technical ideas in non-English contexts
   - Note: High score even if entire interview is in one language,
     if that language is used fluently and precisely

7. **eq_score** (weight: {w_eq})
   - Tone and emotional intelligence derived from transcript semantics
   - Evidence of confidence, enthusiasm, and composure
   - Empathy and self-awareness in their responses

Also identify any red flags (e.g., inconsistencies, vague answers, overconfidence).

## Required JSON Response Format

{{
  "scores": {{
    "technical_depth": <float 0-10>,
    "first_principles": <float 0-10>,
    "shipping_velocity": <float 0-10>,
    "ownership_signals": <float 0-10>,
    "curiosity_depth": <float 0-10>,
    "multilingual_fluency": <float 0-10>,
    "eq_score": <float 0-10>
  }},
  "justifications": {{
    "technical_depth": "<1-2 sentence justification>",
    "first_principles": "<1-2 sentence justification>",
    "shipping_velocity": "<1-2 sentence justification>",
    "ownership_signals": "<1-2 sentence justification>",
    "curiosity_depth": "<1-2 sentence justification>",
    "multilingual_fluency": "<1-2 sentence justification>",
    "eq_score": "<1-2 sentence justification>"
  }},
  "flags": ["<flag1>", "<flag2>"],
  "hr_summary": "<2-3 sentence plain English summary for the HR team>"
}}
"""

# ─── Helper: build the filled prompt ──────────────────────────

def build_scoring_prompt(
    transcript: str,
    job_title: str,
    required_skills: list,
    weights: dict,
) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) with all variables filled.
    Pass these directly to your LLM API.
    """
    skills_str = ", ".join(required_skills) if required_skills else "General Software Engineering"

    system = SYSTEM_PROMPT.format(
        job_title=job_title,
        required_skills=skills_str,
    )
    user = USER_PROMPT.format(
        transcript=transcript,
        w_technical=weights.get("technical_depth", 0.25),
        w_first=weights.get("first_principles", 0.20),
        w_shipping=weights.get("shipping_velocity", 0.20),
        w_ownership=weights.get("ownership_signals", 0.15),
        w_curiosity=weights.get("curiosity_depth", 0.10),
        w_multilingual=weights.get("multilingual_fluency", 0.10),
        w_eq=weights.get("eq_score", 0.10),
    )
    return system, user
