"""
Security regression tests for SmartHire 2.0.
Verifies HTML escaping, XSS prevention, and PII redaction.
"""

import pytest
from src.utils.security import (
    escape_html_text,
    render_skill_pill,
    render_skill_pills,
    sanitize_job_card_meta,
    redact_pii
)


def test_escape_html_text_xss_vectors():
    """Validates escaping of common XSS payload vectors."""
    assert escape_html_text("<script>alert('XSS')</script>") == "&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;"
    assert escape_html_text('" onmouseover="alert(1)"') == "&quot; onmouseover=&quot;alert(1)&quot;"
    assert escape_html_text("<img src=x onerror=alert(1)>") == "&lt;img src=x onerror=alert(1)&gt;"
    assert escape_html_text("Normal Plain Text") == "Normal Plain Text"
    assert escape_html_text(None) == ""
    assert escape_html_text(123) == "123"


def test_render_skill_pill_sanitization():
    """Validates that skill pill HTML generation properly sanitizes untrusted skill text."""
    malicious_skill = "<script>alert('pwned')</script>"
    rendered = render_skill_pill(malicious_skill)
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered
    assert '<span class="skill-pill">' in rendered


def test_render_skill_pills_multiple():
    """Validates multi-pill generation with both benign and malicious skills."""
    skills = ["Python", "<img src=x onerror=alert(1)>", "SQL & Databases"]
    rendered = render_skill_pills(skills)
    assert "<img" not in rendered
    assert "&lt;img" in rendered
    assert "&amp;" in rendered
    assert '<span class="skill-pill">Python</span>' in rendered


def test_sanitize_job_card_meta():
    """Validates that all job metadata fields are safely escaped."""
    meta = sanitize_job_card_meta(
        title="<b onfocus=alert(1)>Senior Lead</b>",
        company='Corp" & Co',
        location="<script>Seattle</script>",
        experience="3-5 <years>",
        salary="$100k < $120k"
    )
    for field, val in meta.items():
        assert "<" not in val or "&lt;" in val
        assert ">" not in val or "&gt;" in val
        assert '"' not in val or "&quot;" in val


def test_redact_pii_emails_and_phones():
    """Validates redaction of candidate emails and phone numbers in diagnostics."""
    diagnostic_text = (
        "Candidate John Doe (email: john.doe@example.com, alt: j_doe99@sub.domain.org) "
        "called from +1-555-867-5309 or 9876543210 regarding application."
    )
    redacted = redact_pii(diagnostic_text)
    assert "john.doe@example.com" not in redacted
    assert "j_doe99@sub.domain.org" not in redacted
    assert "[EMAIL_REDACTED]" in redacted
    assert "555-867-5309" not in redacted
    assert "[PHONE_REDACTED]" in redacted
