"""
Dedicated Resume & Document Validation Service for SmartHire 2.0.
Accurately distinguishes legitimate resumes from research papers, academic assignments,
invoices, standalone certificates, unreadable documents, and corrupted files.

Multi-signal evaluation criteria:
1. File format, file integrity, and successful text extraction.
2. Resume-like structure (Education, Experience, Skills, Projects, Certifications, Contact Info).
3. Candidate-specific career context, timeline indicators, and personal profiles.
4. Signals of non-resume documents (research paper IMRAD structure, dense citations,
   academic affiliations, arXiv/doi metadata, invoice billing fields, assignment prompts).
5. Robustness to various resume formats (functional, chronological, one-line summary, technical research resumes).
"""

import io
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field

from src.parsing.resume_parser import extract_resume_text
from src.features.text_features import extract_skills


class DocumentValidationResult(BaseModel):
    is_valid: bool
    confidence_category: str = Field(description="HIGH, MEDIUM, or LOW confidence category")
    confidence_score: float = Field(description="Heuristic index from 0.0 to 1.0 (not a calibrated probability)")
    score_label: str = "Heuristic Validation Index"
    is_calibrated_probability: bool = False
    document_type: str = Field(description="Detected document classification: resume, research_paper, invoice, etc.")
    rejection_reason: Optional[str] = None
    user_message: str
    detected_sections: List[str] = Field(default_factory=list)
    structural_signals: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


def extract_contact_info(text: str) -> Dict[str, Any]:
    """Extracts candidate contact markers (email, phone, links, location)."""
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    phone_pattern = r"(?:(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\+?\d{1,4}[-.\s]?\d{10}\b)"
    links_pattern = r"\b(?:linkedin\.com/(?:in|pub)/[a-zA-Z0-9_-]+|github\.com/[a-zA-Z0-9_-]+|gitlab\.com/[a-zA-Z0-9_-]+|[a-zA-Z0-9-]+\.github\.io)\b"
    location_pattern = r"\b(?:[A-Z][a-zA-Z\s]{2,20},\s*(?:[A-Z]{2}|[A-Za-z]{4,20})\b|\b\d{5}(?:-\d{4})?\b)"

    has_email = bool(re.search(email_pattern, text))
    has_phone = bool(re.search(phone_pattern, text))
    has_links = bool(re.search(links_pattern, text, re.IGNORECASE))
    has_location = bool(re.search(location_pattern, text))

    score = 0
    if has_email:
        score += 10
    if has_phone:
        score += 8
    if has_links:
        score += 7
    if has_location:
        score += 5

    return {
        "has_email": has_email,
        "has_phone": has_phone,
        "has_links": has_links,
        "has_location": has_location,
        "contact_score": min(25, score)
    }


def extract_resume_sections(text: str) -> Dict[str, Any]:
    """Detects standard functional resume section headings."""
    detected = []

    # Experience section headings
    exp_pattern = r"(?im)^\s*(?:professional\s+|work\s+|employment\s+|career\s+)?experience\s*[:\-]?\s*$|^\s*(?:work|employment|career)\s+history\s*[:\-]?\s*$"
    if re.search(exp_pattern, text):
        detected.append("Experience")

    # Education section headings and degree/graduation patterns
    edu_pattern = r"(?im)^\s*(?:education|academic\s+background|academic\s+history|educational\s+qualifications|degrees?)\s*[:\-]?\s*$"
    degree_mentions = r"\b(?:Bachelor(?:\s+of|\'s)?|Master(?:\s+of|\'s)?|B\.S\.|M\.S\.|B\.Tech|M\.Tech|Ph\.D\.|B\.A\.|M\.A\.|Associate\s+Degree|Degree\s+in|graduated\s+from|degree\s+from|alumnus\s+of)\b"
    if re.search(edu_pattern, text) or re.search(degree_mentions, text, re.IGNORECASE):
        detected.append("Education")

    # Skills section headings
    skills_pattern = r"(?im)^\s*(?:technical\s+|core\s+|key\s+)?(?:skills|competencies|technologies|tech\s+stack|tools\s+and\s+technologies)\s*[:\-]?\s*$"
    if re.search(skills_pattern, text):
        detected.append("Skills")

    # Projects section headings
    proj_pattern = r"(?im)^\s*(?:projects|personal\s+projects|academic\s+projects|key\s+projects|selected\s+projects)\s*[:\-]?\s*$"
    if re.search(proj_pattern, text):
        detected.append("Projects")

    # Certifications section headings
    cert_pattern = r"(?im)^\s*(?:certifications?|licenses?|credentials?|certificates?)\s*[:\-]?\s*$"
    if re.search(cert_pattern, text):
        detected.append("Certifications")

    # Summary or Objective section headings and candidate self-declarations
    sum_pattern = r"(?im)^\s*(?:professional\s+summary|executive\s+summary|summary|profile|about\s+me|career\s+objective|objective)\s*[:\-]?\s*$"
    objective_pattern = r"\b(?:seeking\s+(?:a\s+|new\s+|technical\s+)?(?:role|position|opportunities|job)|(?:enthusiastic|motivated|dedicated|results-driven)\s+professional)\b"
    if re.search(sum_pattern, text) or re.search(objective_pattern, text, re.IGNORECASE):
        detected.append("Summary")

    # Scoring: 1 section = 15, 2 sections = 25, 3+ sections = 35
    count = len(detected)
    if count >= 3:
        section_score = 35
    elif count == 2:
        section_score = 25
    elif count == 1:
        section_score = 15
    else:
        section_score = 0

    return {
        "detected_sections": detected,
        "section_count": count,
        "section_score": section_score
    }


def extract_career_markers(text: str) -> Dict[str, Any]:
    """Detects employment timelines, candidate headers, job titles, and action verbs."""
    # Timeline patterns: e.g. "2019 - 2022", "2020 - Present", "May 2018 - Aug 2021"
    date_range_pattern = r"\b(?:(?:19|20)\d{2}\s*[-–—to]+\s*(?:(?:19|20)\d{2}|present|current)|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(?:19|20)\d{2})\b"
    date_matches = re.findall(date_range_pattern, text, re.IGNORECASE)

    # Job titles / roles
    job_titles_pattern = r"\b(?:senior\s+|lead\s+|principal\s+|staff\s+|junior\s+)?(?:software\s+engineer|data\s+scientist|data\s+engineer|devops\s+engineer|web\s+developer|developer|architect|consultant|analyst|administrator|coordinator|lead|director|intern|specialist|designer|researcher)\b"
    title_matches = re.findall(job_titles_pattern, text, re.IGNORECASE)

    # Candidate Name - Role or Name, Role header pattern: e.g., "Alice Smith, Data Engineer" or "John Doe - Senior Software Engineer"
    candidate_header_pattern = r"(?i)^[A-Z][a-z]+\s+[A-Z][a-z]+[\s\-–—,]+(?:senior\s+|lead\s+|principal\s+|staff\s+|junior\s+)?(?:software\s+engineer|data\s+scientist|data\s+engineer|developer|architect|consultant|analyst)"
    has_candidate_header = bool(re.search(candidate_header_pattern, text.strip()))

    # Candidate bio introduction: e.g., "Alice Candidate is an enthusiastic professional with experience in..."
    candidate_bio_pattern = r"(?i)^[A-Z][a-z]+\s+[A-Z][a-z]+\s+is\s+an?\s+(?:[a-z\s]+)?(?:professional|specialist|engineer|developer|manager|consultant|analyst|coordinator|administrator)\b"
    has_candidate_bio = bool(re.search(candidate_bio_pattern, text.strip()))

    # Direct role title header at start of text: e.g. "Senior Data Scientist proficient in..."
    role_header_pattern = r"(?i)^(?:senior\s+|lead\s+|principal\s+|staff\s+|junior\s+)?(?:software\s+engineer|data\s+scientist|data\s+engineer|web\s+developer|developer|architect|consultant|analyst)\b"
    has_role_header = bool(re.search(role_header_pattern, text.strip()))

    # Experience duration / domain statement: e.g. "4 years experience", "with experience in office administration"
    exp_statement_pattern = r"\b(?:\d+\+?\s*(?:years?|yrs?)(?:\s+of)?\s+experience|(?:with|extensive|hands-on)\s+experience\s+in)\b"
    has_exp_statement = bool(re.search(exp_statement_pattern, text, re.IGNORECASE))

    # Professional proficiency statement: e.g. "proficient in", "specialized in", "experienced with"
    proficient_pattern = r"\b(?:proficient|skilled|specialized|experienced)\s+(?:in|with)\b"
    has_proficient_statement = bool(re.search(proficient_pattern, text, re.IGNORECASE))

    # Work responsibilities statement: e.g. "responsibilities included...", "responsible for..."
    responsibilities_pattern = r"\b(?:responsibilities\s+included|duties\s+included|responsible\s+for|accountable\s+for)\b"
    has_responsibilities = bool(re.search(responsibilities_pattern, text, re.IGNORECASE))

    # Action verbs in bullet points (e.g., "- Developed...", "• Managed...")
    action_bullet_pattern = r"(?im)^[\s*•\-\–]\s*(?:developed|built|designed|implemented|managed|led|created|maintained|architected|spearheaded|improved|optimized|collaborated|conducted|engineered|delivered)\b"
    bullet_matches = re.findall(action_bullet_pattern, text)

    score = 0
    if len(date_matches) >= 2:
        score += 15
    elif len(date_matches) == 1:
        score += 8

    if has_candidate_header or has_candidate_bio:
        score += 15
    elif has_role_header:
        score += 10

    if has_exp_statement:
        score += 10
    elif has_proficient_statement:
        score += 6

    if has_responsibilities:
        score += 8

    if len(title_matches) >= 2:
        score += 10
    elif len(title_matches) == 1:
        score += 6

    if len(bullet_matches) >= 2:
        score += 10
    elif len(bullet_matches) == 1:
        score += 5

    return {
        "date_ranges_count": len(date_matches),
        "job_titles_count": len(title_matches),
        "has_candidate_header": has_candidate_header,
        "has_exp_statement": has_exp_statement,
        "action_bullets_count": len(bullet_matches),
        "career_score": min(30, score)
    }


def detect_research_paper_signals(text: str) -> Dict[str, Any]:
    """
    Detects signals indicating an academic research paper or scientific publication:
    - Academic structural sections (Abstract, Introduction, Related Work, Methodology, Results, Conclusion, References)
    - Dense numbered or author-year citations throughout text
    - Academic publishing identifiers (arXiv, DOI, IEEE, ACM, Department of ..., Corresponding author)
    - Captions (Figure, Table, Equation, Algorithm)
    """
    detected_academic_sections = []

    # Abstract header or abstract paragraph
    if re.search(r"(?im)^\s*abstract\s*[:\-]?\s*$", text) or re.search(r"(?im)\babstract\b[\s\S]{1,60}\b(?:we\s+propose|in\s+this\s+paper|this\s+paper|we\s+present|we\s+introduce|our\s+approach|novel\s+method)\b", text):
        detected_academic_sections.append("Abstract")

    if re.search(r"(?im)^\s*(?:\d+\.?\s+)?introduction\s*[:\-]?\s*$", text):
        detected_academic_sections.append("Introduction")

    if re.search(r"(?im)^\s*(?:\d+\.?\s+)?(?:related\s+work|literature\s+review|background\s+and\s+related\s+work)\s*[:\-]?\s*$", text):
        detected_academic_sections.append("Related Work")

    if re.search(r"(?im)^\s*(?:\d+\.?\s+)?(?:methodology|proposed\s+method(?:ology)?|methods|proposed\s+approach|system\s+architecture|experimental\s+setup)\s*[:\-]?\s*$", text):
        detected_academic_sections.append("Methodology")

    if re.search(r"(?im)^\s*(?:\d+\.?\s+)?(?:results(?:\s+and\s+discussion)?|discussion|experiments?\s+and\s+results)\s*[:\-]?\s*$", text):
        detected_academic_sections.append("Results")

    if re.search(r"(?im)^\s*(?:\d+\.?\s+)?(?:conclusions?(?:\s+and\s+future\s+work)?|concluding\s+remarks)\s*[:\-]?\s*$", text):
        detected_academic_sections.append("Conclusion")

    if re.search(r"(?im)^\s*(?:references|bibliography|works\s+cited)\s*[:\-]?\s*$", text):
        detected_academic_sections.append("References")

    # Citations count
    numbered_citations = re.findall(r"\[\s*\d+(?:\s*,\s*\d+)*\s*\]|\[\s*\d+\s*[-–]\s*\d+\s*\]", text)
    author_year_citations = re.findall(r"\([A-Z][a-zA-Z\s]+(?:et\s+al\.?)?,\s*(?:19|20)\d{2}\)", text)
    et_al_count = len(re.findall(r"\bet\s+al\.(?:\s+\[\d+\])?\b", text, re.IGNORECASE))

    # Academic metadata
    has_arxiv_or_doi = bool(re.search(r"\b(?:arXiv:\s*\d{4}\.\d{4,5}|doi:\s*10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b", text, re.IGNORECASE))
    has_proceedings = bool(re.search(r"\b(?:proceedings\s+of\s+the|transactions\s+on|journal\s+of|conference\s+on\s+neural\s+information|cvpr|icml|neurips|iclr|emnlp|acl|ieee|acm)\b", text, re.IGNORECASE))
    has_affiliation = bool(re.search(r"\bDepartment\s+of\s+[A-Za-z\s]+,\s*(?:University|Institute|College|School|Laborator)\b|\{.*?\}@[\w.-]+|\bCorresponding\s+author\b", text, re.IGNORECASE))
    has_captions = bool(re.search(r"\b(?:Figure\s+\d+|Fig\.\s*\d+|Table\s+\d+|Equation\s+\(?\d+\)?|Algorithm\s+\d+)\s*[:\.]", text))

    paper_score = 0
    if "Abstract" in detected_academic_sections:
        paper_score += 25
    if "References" in detected_academic_sections:
        paper_score += 25
    if "Methodology" in detected_academic_sections:
        paper_score += 20
    if "Results" in detected_academic_sections:
        paper_score += 20
    if "Introduction" in detected_academic_sections:
        paper_score += 15
    if "Related Work" in detected_academic_sections:
        paper_score += 20
    if "Conclusion" in detected_academic_sections:
        paper_score += 15

    cit_count = len(numbered_citations) + len(author_year_citations)
    if cit_count >= 5:
        paper_score += 35
    elif cit_count >= 2:
        paper_score += 20
    elif cit_count == 1:
        paper_score += 10

    if et_al_count >= 2:
        paper_score += 15

    if has_arxiv_or_doi:
        paper_score += 25
    if has_proceedings:
        paper_score += 20
    if has_affiliation:
        paper_score += 15
    if has_captions:
        paper_score += 15

    return {
        "detected_academic_sections": detected_academic_sections,
        "academic_section_count": len(detected_academic_sections),
        "numbered_citations_count": len(numbered_citations),
        "author_year_citations_count": len(author_year_citations),
        "et_al_count": et_al_count,
        "has_arxiv_or_doi": has_arxiv_or_doi,
        "has_proceedings": has_proceedings,
        "has_affiliation": has_affiliation,
        "has_captions": has_captions,
        "paper_score": paper_score
    }


def detect_invoice_signals(text: str) -> Dict[str, Any]:
    """Detects signals of financial invoices or commercial bills."""
    has_invoice_num = bool(re.search(r"\b(?:invoice\s+(?:number|no|#)|invoice\s*#?\s*\d+)\b", text, re.IGNORECASE))
    has_bill_to = bool(re.search(r"\b(?:bill\s+to|ship\s+to|billed\s+to)\b", text, re.IGNORECASE))
    has_totals = bool(re.search(r"\b(?:subtotal|total\s+due|balance\s+due|amount\s+due|grand\s+total|payment\s+due)\b", text, re.IGNORECASE))
    has_line_items = bool(re.search(r"\b(?:unit\s+price|qty|quantity|item\s+description)\b", text, re.IGNORECASE))
    has_payment_terms = bool(re.search(r"\b(?:payment\s+terms|tax\s+invoice|remit\s+to|bank\s+transfer|due\s+within\s+\d+\s+days)\b", text, re.IGNORECASE))

    invoice_score = 0
    if has_invoice_num:
        invoice_score += 30
    if has_bill_to:
        invoice_score += 25
    if has_totals:
        invoice_score += 25
    if has_line_items:
        invoice_score += 20
    if has_payment_terms:
        invoice_score += 15

    return {
        "has_invoice_num": has_invoice_num,
        "has_bill_to": has_bill_to,
        "has_totals": has_totals,
        "has_line_items": has_line_items,
        "has_payment_terms": has_payment_terms,
        "invoice_score": invoice_score
    }


def detect_assignment_signals(text: str) -> Dict[str, Any]:
    """Detects signals of student homework, academic problem sets, or course syllabi."""
    has_hw_header = bool(re.search(r"\b(?:assignment\s*#?\s*\d+|homework\s*#?\s*\d+|problem\s+set\s*#?\s*\d+|lab\s+assignment\s*#?\s*\d+|course\s+syllabus)\b", text, re.IGNORECASE))
    has_course_prompts = bool(re.search(r"\b(?:due\s+date|submission\s+deadline|grading\s+rubric|points\s+possible|submit\s+your\s+solution|instructor:)\b", text, re.IGNORECASE))
    has_questions = bool(re.search(r"(?im)\b(?:problem\s+\d+|question\s+\d+|exercise\s+\d+|task\s+\d+)\s*[:\.]", text))

    assignment_score = 0
    if has_hw_header:
        assignment_score += 40
    if has_course_prompts:
        assignment_score += 30
    if has_questions:
        assignment_score += 25

    return {
        "has_hw_header": has_hw_header,
        "has_course_prompts": has_course_prompts,
        "has_questions": has_questions,
        "assignment_score": assignment_score
    }


def detect_certificate_signals(text: str) -> Dict[str, Any]:
    """Detects standalone certificates or course completion awards."""
    has_cert_title = bool(re.search(r"\b(?:certificate\s+of\s+(?:completion|achievement|appreciation|participation|excellence)|this\s+is\s+to\s+certify\s+that)\b", text, re.IGNORECASE))
    has_completion_verb = bool(re.search(r"\b(?:has\s+successfully\s+completed\s+the\s+course|awarded\s+this\s+certificate|authorized\s+signature|credential\s+id)\b", text, re.IGNORECASE))

    words = len(text.split())
    is_short = words < 180

    certificate_score = 0
    if has_cert_title:
        certificate_score += 40
    if has_completion_verb:
        certificate_score += 35
    if is_short and has_cert_title:
        certificate_score += 25

    return {
        "has_cert_title": has_cert_title,
        "has_completion_verb": has_completion_verb,
        "is_short": is_short,
        "certificate_score": certificate_score
    }


def detect_unrelated_report_signals(text: str) -> Dict[str, Any]:
    """Detects signals of meeting notes, legal agreements, or manuals."""
    has_notes = bool(re.search(r"\b(?:meeting\s+notes?|meeting\s+minutes|attendees:|agenda:|action\s+items:)\b", text, re.IGNORECASE))
    has_legal = bool(re.search(r"\b(?:non-disclosure\s+agreement|this\s+agreement\s+is\s+entered\s+into|terms\s+and\s+conditions|confidentiality\s+agreement)\b", text, re.IGNORECASE))
    has_manual = bool(re.search(r"\b(?:user\s+manual|instruction\s+manual|operating\s+instructions)\b", text, re.IGNORECASE))

    score = 0
    if has_notes:
        score += 45
    if has_legal:
        score += 50
    if has_manual:
        score += 40

    return {
        "has_notes": has_notes,
        "has_legal": has_legal,
        "has_manual": has_manual,
        "unrelated_score": score
    }


def validate_document(
    content_bytes: Optional[bytes] = None,
    filename: Optional[str] = None,
    raw_text: Optional[str] = None
) -> DocumentValidationResult:
    """
    Main entrypoint for document validation.
    Performs multi-signal validation to distinguish legitimate resumes from research papers,
    invoices, academic assignments, certificates, and unreadable files.

    Returns:
        DocumentValidationResult
    """
    target_filename = filename or "document.txt"
    ext = Path(target_filename).suffix.lower()

    # 1. Format validation
    allowed_extensions = [".pdf", ".docx", ".doc", ".txt"]
    if ext and ext not in allowed_extensions:
        return DocumentValidationResult(
            is_valid=False,
            confidence_category="HIGH",
            confidence_score=0.99,
            document_type="unsupported_format",
            rejection_reason=f"Unsupported file format '{ext}'. Only PDF, DOCX, and TXT are supported.",
            user_message="This document does not appear to be a resume. Please upload your resume in PDF or DOCX format."
        )

    # 2. File size and integrity check
    if content_bytes is not None:
        if len(content_bytes) == 0:
            return DocumentValidationResult(
                is_valid=False,
                confidence_category="HIGH",
                confidence_score=1.0,
                document_type="empty",
                rejection_reason="Uploaded file is empty (0 bytes).",
                user_message="Uploaded file is empty (0 bytes). Please upload your resume in PDF or DOCX format."
            )

        # Extract text via parser module
        extracted_text, msg = extract_resume_text(content_bytes, target_filename)

        # Corrupted file detection
        if "Parsing Error" in msg or "Unexpected error reading file" in msg:
            return DocumentValidationResult(
                is_valid=False,
                confidence_category="HIGH",
                confidence_score=0.95,
                document_type="corrupted",
                rejection_reason=f"File appears corrupted and could not be decoded: {msg}",
                user_message="The uploaded file appears to be corrupted or invalid. Please check the file and try again."
            )

        # Unreadable text detection (e.g., scanned PDF with no text layer)
        if not extracted_text or not extracted_text.strip():
            return DocumentValidationResult(
                is_valid=False,
                confidence_category="HIGH",
                confidence_score=0.95,
                document_type="unreadable",
                rejection_reason="Readable text could not be extracted from the document (scanned image or empty text layer).",
                user_message="Readable text could not be extracted from this document. If this is a scanned PDF, please provide a text-searchable PDF, DOCX, or TXT file."
            )
    elif raw_text:
        extracted_text = raw_text.strip()
    else:
        return DocumentValidationResult(
            is_valid=False,
            confidence_category="HIGH",
            confidence_score=1.0,
            document_type="empty",
            rejection_reason="No document content or text provided.",
            user_message="No document content provided. Please upload your resume in PDF or DOCX format."
        )

    # Text length minimum check
    text_clean = extracted_text.strip()
    word_count = len(text_clean.split())
    if len(text_clean) < 40 or word_count < 8:
        return DocumentValidationResult(
            is_valid=False,
            confidence_category="LOW",
            confidence_score=0.20,
            document_type="ambiguous",
            rejection_reason="The document content is too brief to verify as a professional resume.",
            user_message="The document could not be verified as a resume. Please upload a clearer or more complete resume in PDF or DOCX format."
        )

    # 3. Extract Multi-Dimensional Signals
    contact_data = extract_contact_info(text_clean)
    section_data = extract_resume_sections(text_clean)
    career_data = extract_career_markers(text_clean)

    paper_data = detect_research_paper_signals(text_clean)
    invoice_data = detect_invoice_signals(text_clean)
    assignment_data = detect_assignment_signals(text_clean)
    cert_data = detect_certificate_signals(text_clean)
    unrelated_data = detect_unrelated_report_signals(text_clean)

    # Technical skills extracted
    skills = extract_skills(text_clean)
    skill_points = min(15, len(skills) * 3)

    # Compute Positive Resume Score (0 - 100)
    length_bonus = 15 if (80 <= word_count <= 2500) else (5 if word_count < 80 else 8)
    resume_score = (
        contact_data["contact_score"]
        + section_data["section_score"]
        + career_data["career_score"]
        + skill_points
        + length_bonus
    )
    resume_score = min(100, resume_score)

    # Compute Negative Document Scores
    paper_score = paper_data["paper_score"]
    invoice_score = invoice_data["invoice_score"]
    assignment_score = assignment_data["assignment_score"]
    cert_score = cert_data["certificate_score"]
    unrelated_score = unrelated_data["unrelated_score"]

    structural_signals = {
        "contact": contact_data,
        "sections": section_data,
        "career": career_data,
        "extracted_skills_count": len(skills),
        "research_paper": paper_data,
        "invoice": invoice_data,
        "assignment": assignment_data,
        "certificate": cert_data,
        "unrelated": unrelated_data,
        "word_count": word_count,
        "resume_score": resume_score
    }

    # 4. Multi-Signal Decision Rules

    # A. Research Paper Rejection:
    if paper_score >= 45 and (
        ("Abstract" in paper_data["detected_academic_sections"] and (
            "Methodology" in paper_data["detected_academic_sections"]
            or "Results" in paper_data["detected_academic_sections"]
            or "References" in paper_data["detected_academic_sections"]
            or paper_data["academic_section_count"] >= 3
        ))
        or (paper_data["numbered_citations_count"] >= 4 and paper_data["academic_section_count"] >= 2)
        or (paper_data["academic_section_count"] >= 3 and paper_score > resume_score)
    ):
        confidence_cat = "HIGH" if paper_score >= 65 else "MEDIUM"
        heuristic_conf = min(0.98, max(0.70, round(paper_score / 100.0, 2)))
        return DocumentValidationResult(
            is_valid=False,
            confidence_category=confidence_cat,
            confidence_score=heuristic_conf,
            document_type="research_paper",
            rejection_reason="Academic research paper detected (contains academic sections like Abstract/Methodology/Results, citations, and formal references).",
            user_message="This document does not appear to be a resume. Please upload your resume in PDF or DOCX format.",
            detected_sections=section_data["detected_sections"],
            structural_signals=structural_signals
        )

    # B. Financial Invoice Rejection:
    if invoice_score >= 45 and invoice_score > resume_score:
        return DocumentValidationResult(
            is_valid=False,
            confidence_category="HIGH",
            confidence_score=min(0.98, max(0.75, round(invoice_score / 100.0, 2))),
            document_type="invoice",
            rejection_reason="Financial billing or invoice document detected.",
            user_message="This document does not appear to be a resume. Please upload your resume in PDF or DOCX format.",
            detected_sections=section_data["detected_sections"],
            structural_signals=structural_signals
        )

    # C. Academic Assignment / Coursework Rejection:
    if assignment_score >= 45 and assignment_score > resume_score:
        return DocumentValidationResult(
            is_valid=False,
            confidence_category="HIGH",
            confidence_score=min(0.98, max(0.75, round(assignment_score / 100.0, 2))),
            document_type="academic_assignment",
            rejection_reason="Academic assignment, homework problem set, or course syllabus detected.",
            user_message="This document does not appear to be a resume. Please upload your resume in PDF or DOCX format.",
            detected_sections=section_data["detected_sections"],
            structural_signals=structural_signals
        )

    # D. Standalone Certificate Rejection:
    if cert_score >= 50 and cert_data["is_short"] and section_data["section_count"] == 0 and career_data["career_score"] < 10:
        return DocumentValidationResult(
            is_valid=False,
            confidence_category="HIGH",
            confidence_score=0.85,
            document_type="certificate",
            rejection_reason="Standalone certificate or course award detected rather than a comprehensive resume.",
            user_message="This document appears to be a single certificate rather than a full resume. Please upload your complete resume.",
            detected_sections=section_data["detected_sections"],
            structural_signals=structural_signals
        )

    # E. Unrelated Report / Meeting Notes / Legal Agreement:
    if unrelated_score >= 40 and unrelated_score > resume_score:
        return DocumentValidationResult(
            is_valid=False,
            confidence_category="HIGH",
            confidence_score=0.85,
            document_type="unrelated_report",
            rejection_reason="Unrelated report, meeting notes, or legal agreement detected.",
            user_message="This document does not appear to be a resume. Please upload your resume in PDF or DOCX format.",
            detected_sections=section_data["detected_sections"],
            structural_signals=structural_signals
        )

    # F. Positive Resume Validation:
    has_contact = contact_data["contact_score"] >= 8
    has_sections = section_data["section_count"] >= 1
    has_career = career_data["career_score"] >= 8
    has_candidate_header = career_data["has_candidate_header"]
    has_skills = len(skills) >= 2

    # Standard multi-section resume
    if resume_score >= 45 and section_data["section_count"] >= 2:
        return DocumentValidationResult(
            is_valid=True,
            confidence_category="HIGH",
            confidence_score=min(0.98, max(0.80, round(resume_score / 100.0, 2))),
            document_type="resume",
            user_message="Resume validated successfully.",
            detected_sections=section_data["detected_sections"],
            structural_signals=structural_signals
        )

    # Resume with unusual format, concise summary, or missing conventional sections (Task 4)
    # E.g. Candidate header (Name - Role) with experience/skills, or sections + contact
    if (
        (has_candidate_header and (has_career or has_skills or has_contact))
        or (has_sections and (has_contact or has_career or has_skills))
        or (has_contact and (has_career or has_skills))
        or (resume_score >= 30 and (has_career or has_sections or (has_skills and word_count >= 15)))
    ):
        confidence_cat = "HIGH" if resume_score >= 40 else "MEDIUM"
        return DocumentValidationResult(
            is_valid=True,
            confidence_category=confidence_cat,
            confidence_score=min(0.90, max(0.55, round(resume_score / 100.0, 2))),
            document_type="resume",
            user_message="Resume validated successfully.",
            detected_sections=section_data["detected_sections"],
            structural_signals=structural_signals
        )

    # G. Uncertain / Ambiguous Document
    return DocumentValidationResult(
        is_valid=False,
        confidence_category="LOW",
        confidence_score=min(0.40, max(0.10, round(resume_score / 100.0, 2))),
        document_type="ambiguous",
        rejection_reason="The document lacks sufficient resume structure (contact details, work experience, education, or skills).",
        user_message="The document could not be verified as a resume. Please upload a clearer or more complete resume in PDF or DOCX format.",
        detected_sections=section_data["detected_sections"],
        structural_signals=structural_signals
    )
