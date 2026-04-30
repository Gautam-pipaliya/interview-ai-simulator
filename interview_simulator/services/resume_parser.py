import json
import re

from PyPDF2 import PdfReader
import requests

_REQUESTS_SESSION = requests.Session()
_REQUESTS_SESSION.trust_env = False


DEFAULT_ROLE_OPTIONS = [
    "Software Engineer",
    "Backend Developer",
    "Frontend Developer",
    "Full Stack Developer",
    "Data Scientist",
    "AI/ML Engineer",
    "DevOps Engineer",
    "Cloud Engineer",
    "Product Manager",
    "UI/UX Designer",
    "Data Analyst",
    "Cybersecurity Engineer",
    "Mobile Developer",
]


class AIResumeAnalysisError(RuntimeError):
    pass


GROQ_FALLBACK_MODEL_PREFERENCE = [
    "llama-3.3-70b-versatile",
    "qwen/qwen3-32b",
    "llama-3.1-8b-instant",
    "groq/compound-mini",
]


_SCHEMA = (
    "overall_score (number 0-100), "
    "role_fit (string), "
    "experience_level (string: Junior/Mid/Senior/Lead), "
    "summary (string, 2-3 sentences), "
    "detected_skills (array of strings, up to 15), "
    "strengths (array of strings, up to 6), "
    "improvement_areas (array of strings, up to 6), "
    "recommended_skills (array of strings, up to 8), "
    "ats_tips (array of strings, up to 6), "
    "ats_accuracy_score (number 0-100), "
    "jd_alignment_score (number 0-100), "
    "jd_gap_summary (string), "
    "jd_recommendations (array of strings, up to 6), "
    "recruiter_highlights (array of strings, up to 5)"
)


_SYSTEM_PROMPT = (
    "You are a senior technical recruiter and resume expert with 15+ years of experience "
    "hiring for top technology companies. Analyze resumes objectively, identify real "
    "strengths and gaps, and give actionable, specific advice. "
    "Return only valid JSON with no markdown or extra text."
)


def _build_user_prompt(resume_text: str, role: str, job_description: str) -> str:
    jd_part = f"Job Description:\n{job_description[:5000]}" if job_description.strip() else "Job Description: Not provided."
    return (
        f"Analyze this resume for the target role: {role}\n\n"
        f"{jd_part}\n\n"
        f"Resume Text:\n{resume_text[:12000]}\n\n"
        f"Return a JSON object with these keys: {_SCHEMA}\n"
        "Be specific and actionable. Score honestly based on real standards."
    )


# ── PDF extraction ──────────────────────────────────────────────────────────

def extract_text_from_pdf(file_stream) -> str:
    reader = PdfReader(file_stream)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


# ── JSON helpers ─────────────────────────────────────────────────────────────

def _extract_json_object(text: str) -> dict:
    candidate = (text or "").strip()
    if not candidate:
        raise AIResumeAnalysisError("AI returned an empty response.")

    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?", "", candidate).strip()
        candidate = re.sub(r"```$", "", candidate).strip()

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise AIResumeAnalysisError("Could not parse AI response as JSON.")
        try:
            parsed = json.loads(candidate[start : end + 1])
        except json.JSONDecodeError as exc:
            raise AIResumeAnalysisError("AI response JSON is invalid.") from exc

    if not isinstance(parsed, dict):
        raise AIResumeAnalysisError("AI response must be a JSON object.")

    return parsed


def _normalize_string_list(values, *, max_items: int = 8) -> list:
    if not isinstance(values, list):
        return []

    output = []
    seen = set()
    for item in values:
        text = str(item).strip()
        key = text.casefold()
        if not text or key in seen:
            continue
        seen.add(key)
        output.append(text)
        if len(output) >= max_items:
            break
    return output


def _normalize_score(value) -> float:
    try:
        return round(max(0.0, min(float(value), 100.0)), 2)
    except (TypeError, ValueError):
        return 0.0


# ── Anthropic (Claude) provider ─────────────────────────────────────────────

def _analyze_with_anthropic(*, api_key: str, resume_text: str, role: str, job_description: str) -> dict:
    endpoint = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 2048,
        "system": _SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": _build_user_prompt(resume_text, role, job_description)}
        ],
    }

    try:
        response = _REQUESTS_SESSION.post(endpoint, headers=headers, json=payload, timeout=60, proxies={"http": None, "https": None})
    except requests.RequestException as exc:
        raise AIResumeAnalysisError(f"Could not reach Anthropic API: {exc}") from exc

    if response.status_code >= 400:
        raise AIResumeAnalysisError(
            f"Anthropic API error ({response.status_code}): {response.text[:400]}"
        )

    try:
        data = response.json()
        content = data["content"][0]["text"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise AIResumeAnalysisError("Unexpected Anthropic response format.") from exc

    return _extract_json_object(content)


# ── Groq provider ────────────────────────────────────────────────────────────

def _fetch_available_model_ids(api_base_url: str, api_key: str) -> list:
    try:
        r = _REQUESTS_SESSION.get(
            api_base_url.rstrip("/") + "/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
            proxies={"http": None, "https": None},
        )
    except requests.RequestException:
        return []

    if r.status_code >= 400:
        return []

    try:
        items = r.json().get("data", [])
    except (TypeError, ValueError, AttributeError):
        return []

    return [str(item.get("id", "")).strip() for item in items if item.get("id")]


def _pick_best_groq_fallback(model_ids: list):
    if not model_ids:
        return None

    available = set(model_ids)
    for pref in GROQ_FALLBACK_MODEL_PREFERENCE:
        if pref in available:
            return pref

    for model_id in model_ids:
        lowered = model_id.lower()
        if any(kw in lowered for kw in ["whisper", "guard", "orpheus"]):
            continue
        return model_id
    return None


def _analyze_with_groq(*, api_key: str, api_base_url: str, model: str, resume_text: str, role: str, job_description: str) -> dict:
    endpoint = api_base_url.rstrip("/") + "/chat/completions"
    model_candidates = [m for m in [model or ""] if m.strip()]
    normalized_base = (api_base_url or "").strip().lower()

    if "api.groq.com" in normalized_base:
        available_ids = _fetch_available_model_ids(api_base_url, api_key)
        if available_ids:
            if not any(candidate in available_ids for candidate in model_candidates):
                fallback = _pick_best_groq_fallback(available_ids)
                if fallback and fallback not in model_candidates:
                    model_candidates.append(fallback)

    if not model_candidates:
        raise AIResumeAnalysisError("Model name is missing. Configure GROQ_MODEL.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    last_error = ""

    for model_name in model_candidates:
        payload = {
            "model": model_name,
            "temperature": 0.3,
            "max_tokens": 2048,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(resume_text, role, job_description)},
            ],
        }
        try:
            r = _REQUESTS_SESSION.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=60,
                proxies={"http": None, "https": None},
            )
        except requests.RequestException as exc:
            raise AIResumeAnalysisError(f"Could not reach Groq API: {exc}") from exc

        if r.status_code < 400:
            try:
                return _extract_json_object(r.json()["choices"][0]["message"]["content"])
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                raise AIResumeAnalysisError("Unexpected Groq response format.") from exc

        last_error = r.text[:300]
        lowered_detail = last_error.lower()
        if r.status_code in {400, 404} and ("model_not_found" in lowered_detail or "model not found" in lowered_detail):
            continue
        raise AIResumeAnalysisError(f"Groq API error ({r.status_code}): {last_error}")

    raise AIResumeAnalysisError(f"All Groq models failed. Last error: {last_error}")


# ── Public interface ─────────────────────────────────────────────────────────
def analyze_resume_with_ai(
    *,
    api_key: str = "",
    api_base_url: str = "https://api.groq.com/openai/v1",
    model: str = "llama-3.3-70b-versatile",
    resume_text: str,
    role: str,
    job_description: str = "",
    anthropic_api_key: str = "",
) -> dict:
    cleaned = (resume_text or "").strip()
    job_desc = (job_description or "").strip()
    anthropic_key = (anthropic_api_key or "").strip()
    groq_key = (api_key or "").strip()

    if not cleaned:
        raise AIResumeAnalysisError("Resume text is empty. Please upload a text-based PDF.")

    if anthropic_key:
        raw = _analyze_with_anthropic(
            api_key=anthropic_key,
            resume_text=cleaned,
            role=role,
            job_description=job_desc,
        )
        provider_used = "anthropic"
    elif groq_key:
        base = api_base_url or "https://api.groq.com/openai/v1"
        if groq_key.startswith("gsk_") and "api.x.ai" in base:
            base = "https://api.groq.com/openai/v1"
        raw = _analyze_with_groq(
            api_key=groq_key,
            api_base_url=base,
            model=model or "llama-3.3-70b-versatile",
            resume_text=cleaned,
            role=role,
            job_description=job_desc,
        )
        provider_used = "groq"
    else:
        raise AIResumeAnalysisError(
            "No AI API key configured. Set ANTHROPIC_API_KEY (recommended) or GROQ_API_KEY."
        )

    overall = _normalize_score(raw.get("overall_score", 0))
    has_jd = bool(job_desc)

    return {
        "overall_score": overall,
        "role_fit": str(raw.get("role_fit", "Unknown")).strip() or "Unknown",
        "experience_level": str(raw.get("experience_level", "Unknown")).strip() or "Unknown",
        "summary": str(raw.get("summary", "")).strip(),
        "detected_skills": _normalize_string_list(raw.get("detected_skills", []), max_items=15),
        "strengths": _normalize_string_list(raw.get("strengths", []), max_items=6),
        "improvement_areas": _normalize_string_list(raw.get("improvement_areas", []), max_items=6),
        "recommended_skills": _normalize_string_list(raw.get("recommended_skills", []), max_items=8),
        "ats_tips": _normalize_string_list(raw.get("ats_tips", []), max_items=6),
        "ats_accuracy_score": _normalize_score(raw.get("ats_accuracy_score", overall)),
        "jd_alignment_score": _normalize_score(
            raw.get("jd_alignment_score", overall if not has_jd else 0)
        ),
        "jd_gap_summary": str(
            raw.get(
                "jd_gap_summary",
                "Add a job description to receive a targeted hiring-gap summary." if not has_jd else "",
            )
        ).strip(),
        "jd_recommendations": _normalize_string_list(raw.get("jd_recommendations", []), max_items=6),
        "recruiter_highlights": _normalize_string_list(raw.get("recruiter_highlights", []), max_items=5),
        "provider": provider_used,
    }
