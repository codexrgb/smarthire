"""
Skill Extraction, Normalization, and Skill-Gap Module for SmartHire.
Uses regex word boundary matching, span tracking for phrase precedence, and canonical alias mappings.
"""

import re
from typing import List, Set, Dict, Any, Union
from src.config import SKILL_ALIAS_MAP, MASTER_SKILLS


def normalize_skill(skill: str) -> str:
    """
    Normalizes a single skill string to standard master format using SKILL_ALIAS_MAP.

    Examples:
        'js' -> 'JavaScript'
        'reactjs' -> 'React'
        'springboot' -> 'Spring Boot'
        'spring boot' -> 'Spring Boot'
        'spring' -> 'Spring'
        'ai' -> 'Artificial Intelligence'
        'sklearn' -> 'Scikit-learn'
        'postgres' -> 'PostgreSQL'
    """
    if not skill or not isinstance(skill, str):
        return ""

    cleaned = skill.strip().lower()
    if cleaned in SKILL_ALIAS_MAP:
        return SKILL_ALIAS_MAP[cleaned]

    return skill.strip().title()


def extract_skills(text: str) -> List[str]:
    """
    Extracts known normalized skills from candidate or job text using regex matching.
    Uses length-descending span tracking so longer phrases like 'Spring Boot' take precedence
    over shorter sub-phrases like 'Spring' when contained in the same span.
    """
    if not text or not isinstance(text, str):
        return []

    text_lower = text.lower()
    extracted = set()
    occupied_spans = []  # List of (start, end) tuples for matched phrases

    # Sort SKILL_ALIAS_MAP items by length of alias descending so longer phrases match first
    sorted_aliases = sorted(SKILL_ALIAS_MAP.items(), key=lambda item: len(item[0]), reverse=True)

    for alias, canonical_name in sorted_aliases:
        # Special word boundary handling for tech symbols like +, #, .
        if alias in ["c++", "cpp"]:
            pattern = r"(?i)(?:^|[\s,.\/;:\(\)\[\]\-])c\+\+(?:$|[\s,.\/;:\(\)\[\]\-])"
        elif alias in ["c#", "csharp"]:
            pattern = r"(?i)(?:^|[\s,.\/;:\(\)\[\]\-])c#(?:$|[\s,.\/;:\(\)\[\]\-])"
        elif alias in [".net", "dotnet"]:
            pattern = r"(?i)(?:^|[\s,.\/;:\(\)\[\]\-])\.net(?:$|[\s,.\/;:\(\)\[\]\-])"
        elif alias in ["node.js", "nodejs"]:
            pattern = r"(?i)\bnode\.?js\b"
        elif alias in ["react.js", "reactjs"]:
            pattern = r"(?i)\breact\.?js\b"
        elif alias in ["vue.js", "vuejs"]:
            pattern = r"(?i)\bvue\.?js\b"
        elif alias in ["express.js", "expressjs"]:
            pattern = r"(?i)\bexpress\.?js\b"
        elif alias in ["ai"]:
            # Strict uppercase or standalone 'AI' / 'A.I.'
            pattern = r"\b(?:AI|A\.I\.)\b"
            for m in re.finditer(pattern, text):
                span = m.span()
                if not any(sp[0] <= span[0] and span[1] <= sp[1] for sp in occupied_spans):
                    extracted.add(canonical_name)
                    occupied_spans.append(span)
            continue
        else:
            escaped = re.escape(alias)
            pattern = rf"\b{escaped}\b"

        # Search all matches of current alias
        for m in re.finditer(pattern, text_lower):
            span = m.span()
            # Check if this span is already inside a previously matched longer phrase
            is_subspan = any(sp[0] <= span[0] and span[1] <= sp[1] for sp in occupied_spans)
            if not is_subspan:
                extracted.add(canonical_name)
                occupied_spans.append(span)

    return sorted(list(extracted))


def extract_normalized_skills(text: str) -> List[str]:
    """
    Alias for extract_skills for consistent pipeline interface.
    """
    return extract_skills(text)


def calculate_skill_match(
    candidate_skills: Union[List[str], Set[str]],
    required_skills: Union[List[str], Set[str]]
) -> Dict[str, Any]:
    """
    Calculates match percentage, matched skills, and missing skills.

    Formula:
    matched = candidate_skills ∩ required_skills
    missing = required_skills - candidate_skills
    skill_match_percentage = (len(matched) / len(required_skills)) * 100

    If required_skills is empty:
    returns 0 and explains required skill information is unavailable.
    """
    cand_set = set(normalize_skill(s) for s in candidate_skills if s and s != "N/A")
    req_set = set(normalize_skill(s) for s in required_skills if s and s != "N/A")

    if not req_set:
        return {
            "matched_skills": [],
            "missing_skills": [],
            "match_percentage": 0.0,
            "explanation": "Required skill information is unavailable."
        }

    matched = cand_set.intersection(req_set)
    missing = req_set.difference(cand_set)
    percentage = round((len(matched) / len(req_set)) * 100.0, 2)

    return {
        "matched_skills": sorted(list(matched)),
        "missing_skills": sorted(list(missing)),
        "match_percentage": percentage,
        "explanation": "Success"
    }


def generate_skill_gap(resume_text: str, job_text_or_skills: Union[str, List[str]]) -> Dict[str, Any]:
    """
    High-level skill gap analysis helper between raw resume text and job text or skill list.
    """
    candidate_skills = extract_skills(resume_text)

    if isinstance(job_text_or_skills, list):
        required_skills = [normalize_skill(s) for s in job_text_or_skills]
    elif isinstance(job_text_or_skills, str):
        if "," in job_text_or_skills and len(job_text_or_skills) < 300:
            raw_splits = [s.strip() for s in job_text_or_skills.split(",")]
            required_skills = [normalize_skill(s) for s in raw_splits if s.strip()]
        else:
            required_skills = extract_skills(job_text_or_skills)
    else:
        required_skills = []

    res = calculate_skill_match(candidate_skills, required_skills)
    res["candidate_skills"] = candidate_skills
    res["job_skills"] = required_skills
    return res
