"""
Security, Sanitization, and PII Redaction Utilities for SmartHire 2.0.
Prevents XSS vulnerabilities in UI renderings and redacts sensitive candidate PII in logs.
"""

import html
import re
from typing import Dict, Any, List


def escape_html_text(text: Any) -> str:
    """Safely escapes HTML special characters to prevent XSS injection."""
    if text is None:
        return ""
    return html.escape(str(text), quote=True)


def render_skill_pill(skill: str, pill_class: str = "skill-pill", prefix: str = "") -> str:
    """Renders a single safe HTML skill badge with escaped content."""
    safe_skill = escape_html_text(skill)
    safe_prefix = escape_html_text(prefix) if prefix else ""
    return f'<span class="{escape_html_text(pill_class)}">{safe_prefix}{safe_skill}</span>'


def render_skill_pills(skills: List[str], pill_class: str = "skill-pill", prefix: str = "") -> str:
    """Renders a collection of safe HTML skill pills joined by space."""
    return " ".join([render_skill_pill(s, pill_class=pill_class, prefix=prefix) for s in skills if s])


def sanitize_job_card_meta(
    title: Any,
    company: Any,
    location: Any,
    experience: Any,
    salary: Any
) -> Dict[str, str]:
    """Escapes all job card metadata strings before insertion into HTML templates."""
    return {
        "title": escape_html_text(title if title is not None else "N/A"),
        "company": escape_html_text(company if company is not None else "N/A"),
        "location": escape_html_text(location if location is not None else "N/A"),
        "experience": escape_html_text(experience if experience is not None else "N/A"),
        "salary": escape_html_text(salary if salary is not None else "N/A"),
    }


def redact_pii(text: str) -> str:
    """
    Redacts personal identifiers (emails, phone numbers) from strings
    for secure logging and diagnostic output.
    """
    if not text or not isinstance(text, str):
        return ""

    # Redact Email addresses
    redacted = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "[EMAIL_REDACTED]",
        text
    )

    # Redact Phone numbers (standard international and US/India formats)
    redacted = re.sub(
        r"\b(?:\+?\d{1,4}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}\b",
        "[PHONE_REDACTED]",
        redacted
    )

    return redacted
