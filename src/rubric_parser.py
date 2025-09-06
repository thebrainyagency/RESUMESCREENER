import os, json
from typing import Dict, Any
from openai import OpenAI
from src.utils import atomic_write_json, sha256_text

RUBRIC_PATH = os.getenv("RUBRIC_PATH", "data/rubric.txt")
OPENAI_MODEL_PARSE = os.getenv("OPENAI_MODEL_PARSE", "gpt-4o")
RUBRIC_CACHE_ROOT = os.getenv("RUBRIC_CACHE_ROOT", "out/cache/rubric")

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

_SYSTEM_PROMPT_PARSE = """You are a precise rubric parser.
Input: free-form rubric text with multiple dimensions (e.g., "A. Projects ... (30 points)").
Output: strict JSON.
Rules:
- Extract each dimension's letter id (A,B,...), title, and max_points.
- For each dimension, extract bands: min_points, max_points, description (verbatim if possible).
- Convert ranges like "25–30" to min=25, max=30 (inclusive).
- Do not invent data. Return valid JSON only.
Schema:
{
  "dimensions":[
    {
      "id":"A","title":"Projects / Initiatives","max_points":30,
      "bands":[{"min_points":25,"max_points":30,"description":"..."}]
    }
  ]
}"""

def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _slugify(title: str) -> str:
    s = "".join(ch if ch.isalnum() else "_" for ch in title.strip().lower())
    while "__" in s: s = s.replace("__", "_")
    return s.strip("_") or "dimension"

def _cache_paths(rubric_text: str):
    rub_sha = sha256_text(rubric_text)[:16]
    os.makedirs(RUBRIC_CACHE_ROOT, exist_ok=True)
    return rub_sha, os.path.join(RUBRIC_CACHE_ROOT, f"{rub_sha}.json")

def parse_rubric(rubric_path: str = RUBRIC_PATH) -> Dict[str, Any]:
    """LLM-parse rubric text (no regex). Cached by rubric hash."""
    rubric_text = _read(rubric_path)
    rub_sha, cache_path = _cache_paths(rubric_text)

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["cache_hit"] = True
        return data

    try:
        resp = _client.chat.completions.create(
            model=OPENAI_MODEL_PARSE,
            temperature=0,
            response_format={"type":"json_object"},
            messages=[
                {"role":"system","content":_SYSTEM_PROMPT_PARSE},
                {"role":"user","content":f"Rubric text:\n\n{rubric_text}\n\nReturn only JSON."},
            ],
        )
        parsed = json.loads(resp.choices[0].message.content)
        dims = parsed.get("dimensions", [])
        for d in dims:
            d["key"] = _slugify(d.get("title",""))
            d["max_points"] = int(d.get("max_points", 0))
            for b in d.get("bands", []):
                b["min_points"] = int(b.get("min_points", 0))
                b["max_points"] = int(b.get("max_points", 0))
        data = {
            "dimensions": dims,
            "total_max_points": sum(d["max_points"] for d in dims),
            "rubric_sha": rub_sha,
            "cache_hit": False,
        }
    except Exception as e:
        data = {
            "dimensions": [],
            "total_max_points": 0,
            "rubric_sha": "error",
            "error": str(e),
            "cache_hit": False,
        }

    atomic_write_json(cache_path, data)
    return data
