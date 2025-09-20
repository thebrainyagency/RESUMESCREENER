# src/scorer.py
import os
import json
from typing import Dict, Any, List
from openai import OpenAI

from src.rubric_parser import parse_rubric
from src.contact_norm import (
    detect_contacts,
    append_detected_block,
    postprocess_extracted,
)

OPENAI_MODEL_SCORE = os.getenv("OPENAI_MODEL_SCORE", "gpt-4o")
MAX_RESUME_CHARS = int(os.getenv("MAX_RESUME_CHARS", "5000"))

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

_SYSTEM_PROMPT_SCORE = """You are a precise resume screener and rubric-driven scorer.
Use ONLY the resume text and the DETECTED_CONTACTS block for evidence. Do NOT invent data.
Score strictly against the provided rubric JSON (dimensions, max points, bands).

Rules:
- For each dimension, pick one band that best matches evidence; choose an integer within that band's min..max.
- Provide a short reason per dimension referencing resume evidence.
- Evidence = 1–3 short literal quotes copied from the resume (no paraphrases).
- total_score = sum(all dimension scores).
- If resume lacks data, score conservatively and state so.
- When extracting URLs/emails/phones, prefer canonical values listed in the DETECTED_CONTACTS block if they appear.
"""

def _base_profile_schema() -> Dict[str, Any]:
    return {
        "resume_file_name": {"type": "string"},
        "applicant_name": {"type": ["string", "null"]},
        "email": {"type": ["string", "null"]},
        "phone": {"type": ["string", "null"]},
        "city_location": {"type": ["string", "null"]},
        "college": {"type": ["string", "null"]},
        "education_level": {"type": ["string", "null"], "enum": ["UG", "PG", "PhD", None]},
        "graduation_year": {"type": ["integer", "null"]},
        "total_experience_years": {"type": ["number", "null"]},
        "relevant_experience_years": {"type": ["number", "null"]},
        "current_or_last_company": {"type": ["string", "null"]},
        "key_roles": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": ["string", "null"]},
                    "company": {"type": ["string", "null"]},
                    "start_month": {"type": ["integer", "null"]},
                    "start_year": {"type": ["integer", "null"]},
                    "end_month": {"type": ["integer", "null"]},
                    "end_year": {"type": ["integer", "null"]},
                    "duration_months": {"type": ["integer", "null"]},
                },
            },
        },
        "portfolio_github_links": {"type": "array", "items": {"type": "string"}},
        "linkedin_link": {"type": ["string", "null"]},
        "achievements": {"type": "array", "items": {"type": "string"}},
    }

def _dynamic_schema(dimensions: List[Dict[str, Any]]) -> Dict[str, Any]:
    props = _base_profile_schema()
    for d in dimensions:
        letter, key, max_pts = d["id"], d["key"], d["max_points"]
        props[f"{letter}_{key}_score"] = {"type": "integer"}   # will clamp later
        props[f"{letter}_{key}_reason"] = {"type": "string"}
    props.update({
        "total_score": {"type": "integer"},
        "rationale": {"type": "string"},
        "evidence": {"type": "array", "items": {"type": "string"}},
    })
    return {"type": "object", "properties": props, "required": ["resume_file_name", "total_score", "evidence"]}

def _schema_text(schema: Dict[str, Any]) -> str:
    return json.dumps(schema, separators=(",", ":"), ensure_ascii=False)

def _build_prompt(jd_text: str, resume: Dict[str, Any], rubric: Dict[str, Any], schema_text: str, detected_block_text: str) -> str:
    # rubric JSON as truth source for dimensions/bands
    rubric_json = json.dumps(rubric, ensure_ascii=False)

    return (
        f"JOB DESCRIPTION:\n{jd_text}\n\n"
        f"PARSED_RUBRIC_JSON:\n{rubric_json}\n\n"
        f"RESUME ({resume.get('filename')}):\n{detected_block_text}\n\n"
        "Instructions:\n"
        "- Use ONLY the resume text and DETECTED_CONTACTS for evidence.\n"
        "- Score each dimension by selecting the best-fitting band; choose an integer within that band's range.\n"
        "- Provide a short justification per dimension.\n"
        "- Compute total_score as the sum of all dimension scores.\n"
        "- Evidence must be 1–3 literal quotes from the resume text.\n"
        "- If resume lacks data for a dimension, score low and state so.\n\n"
        "Return ONLY JSON matching this schema (no extra text):\n"
        f"{schema_text}\n"
        "Hard requirements:\n"
        '- "resume_file_name" must equal the provided file name exactly.\n'
        '- "education_level" must be one of ["UG","PG","PhD"] or null.\n'
        "- Numeric fields must be numbers (not strings).\n"
        "- Evidence must be literal quotes from the resume.\n"
    )

def score_with_llm(resume: Dict[str, Any], jd_text: str) -> Dict[str, Any]:
    """
    Returns LLM extraction + rubric-driven scores.
    """
    # 1) Parse rubric
    rubric = parse_rubric()  # reads RUBRIC_PATH internally
    dims = rubric.get("dimensions", [])

    # 2) Build dynamic schema & prompt
    schema = _dynamic_schema(dims)
    schema_text = _schema_text(schema)

    raw_resume_text = (resume.get("text") or "")
    # Detect contacts on raw text
    detected = detect_contacts(raw_resume_text)
    # Append machine-readable hints to the resume for the model
    enriched_text = append_detected_block(raw_resume_text, detected)
    # Truncate after enrichment
    rtext_bounded = enriched_text[:MAX_RESUME_CHARS]

    user_prompt = _build_prompt(
        jd_text=jd_text,
        resume=resume,
        rubric=rubric,
        schema_text=schema_text,
        detected_block_text=rtext_bounded,
    )

    # 3) LLM call
    try:
        resp = _client.chat.completions.create(
            model=OPENAI_MODEL_SCORE,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT_SCORE},
                {"role": "user", "content": user_prompt},
            ],
        )
        data = json.loads(resp.choices[0].message.content)

        # Defensive fills
        if not data.get("resume_file_name"):
            data["resume_file_name"] = resume.get("filename")
        data.setdefault("key_roles", [])
        data.setdefault("portfolio_github_links", [])
        data.setdefault("achievements", [])
        data.setdefault("evidence", [])

        # Clamp per-dimension scores and recompute total
        total = 0
        for d in dims:
            letter, key, max_pts = d["id"], d["key"], int(d["max_points"])
            f = f"{letter}_{key}_score"
            v = data.get(f)
            val = int(v) if isinstance(v, (int, float, str)) and str(v).isdigit() else int(v) if isinstance(v, int) else 0
            if val < 0:
                val = 0
            if val > max_pts:
                val = max_pts
            data[f] = val
            total += val
        data["total_score"] = int(total)

        # Post-process canonical contacts using detection hints
        data = postprocess_extracted(data, detected)

    except Exception as e:
        data = {
            "resume_file_name": resume.get("filename"),
            "applicant_name": None,
            "email": None,
            "phone": None,
            "city_location": None,
            "college": None,
            "education_level": None,
            "graduation_year": None,
            "total_experience_years": None,
            "relevant_experience_years": None,
            "current_or_last_company": None,
            "key_roles": [],
            "portfolio_github_links": [],
            "linkedin_link": None,
            "achievements": [],
            "rationale": f"Error during scoring: {e}",
            "evidence": [],
            "total_score": 0,
        }

    # 5) Add metadata
    data.update({
        "prefilter_score": resume.get("prefilter_score", 0.0)
    })
    return data

# Backwards-compatible alias
def score_resume(resume: Dict[str, Any], jd_text: str):
    return score_with_llm(resume, jd_text)
