"""
Automated Document Validation Test Suite for SmartHire 2.0.
Verifies multi-signal resume validation across all required scenarios:
1. Valid resume in PDF format.
2. Valid resume in DOCX format.
3. Research paper with technical skills and job-related keywords (rejected).
4. Academic assignment (rejected).
5. Invoice or unrelated report (rejected).
6. Corrupted or empty file (rejected).
7. Scanned PDF with no extractable text (rejected).
8. Resume with unusual format or missing conventional sections (accepted).
9. Ambiguous document (rejected with guidance).
10. Regression test proving rejected documents never trigger job matching.
"""

import io
import json
import pytest
import docx
import pypdf
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.main import app
from src.backend.database import get_db, Base
from src.backend.models.resume import Resume
from src.backend.models.user import User
from src.backend.security.hashing import hash_password
from src.backend.security.auth import create_access_token
from src.backend.services.document_validation import validate_document


# Set up isolated in-memory SQLite database
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_validation_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def candidate_auth_header(db_session):
    user = User(
        email="candidate.valid@example.com",
        hashed_password=hash_password("ValidPassword123!"),
        full_name="Valid Candidate",
        role="candidate",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role, "full_name": user.full_name}
    )
    return {"Authorization": f"Bearer {token}"}


# --- Document Generation Helpers ---

def create_synthetic_pdf(lines: list) -> bytes:
    """Creates a valid text-searchable PDF binary in memory."""
    stream_content = "BT\n/F1 12 Tf\n"
    y = 720
    for line in lines:
        safe_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_content += f"72 {y} Td\n({safe_line}) Tj\n0 -16 Td\n"
        y -= 16
    stream_content += "ET"
    stream_bytes = stream_content.encode("latin1", errors="replace")

    body = f"""%PDF-1.4
1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj
2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj
3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources <</Font <</F1 4 0 R>>>> /Contents 5 0 R>> endobj
4 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj
5 0 obj <</Length {len(stream_bytes)}>>
stream
""".encode("latin1") + stream_bytes + b"""
endstream
endobj
xref
0 6
0000000000 65535 f 
trailer <</Size 6 /Root 1 0 R>>
startxref
0
%%EOF
"""
    return body


def create_synthetic_docx(paragraphs: list) -> bytes:
    """Creates a valid DOCX document in memory."""
    doc = docx.Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def create_scanned_pdf() -> bytes:
    """Creates a valid PDF with blank pages (0 extractable text characters)."""
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


# --- Test Cases ---

def test_1_valid_resume_pdf(client, candidate_auth_header, db_session):
    """
    Scenario 1: Valid resume in PDF format.
    Must pass multi-signal validation, persist in database, and extract skills/category.
    """
    pdf_bytes = create_synthetic_pdf([
        "Jane Doe",
        "Email: jane.doe@example.com | Phone: (555) 123-4567 | San Francisco, CA",
        "LinkedIn: linkedin.com/in/janedoe | GitHub: github.com/janedoe",
        "PROFESSIONAL SUMMARY",
        "Experienced Software Engineer with 5 years building scalable web services in Python.",
        "EXPERIENCE",
        "Senior Backend Engineer - DataCorp (2021 - Present)",
        "- Architected REST microservices with FastAPI, PostgreSQL, and Docker.",
        "- Reduced API latency by 35% using Redis caching strategies.",
        "Software Engineer - StartupLab (2019 - 2021)",
        "- Implemented AWS Lambda pipelines and data transformations using Python and SQL.",
        "EDUCATION",
        "B.S. in Computer Science - University of California, Berkeley (2015 - 2019)",
        "SKILLS",
        "Python, FastAPI, SQL, PostgreSQL, Docker, AWS, Redis, Git, Linux"
    ])

    response = client.post(
        "/api/v1/resumes/parse",
        files={"file": ("jane_doe_resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers=candidate_auth_header
    )
    assert response.status_code == 200
    data = response.json()
    assert "resume_id" in data
    assert data["original_filename"] == "jane_doe_resume.pdf"
    assert "validation" in data
    assert data["validation"]["is_valid"] is True
    assert data["validation"]["confidence_category"] in ["HIGH", "MEDIUM"]
    assert data["validation"]["document_type"] == "resume"

    # Verify record exists in DB
    resume = db_session.query(Resume).filter(Resume.id == data["resume_id"]).first()
    assert resume is not None
    assert resume.original_filename == "jane_doe_resume.pdf"


def test_2_valid_resume_docx(client, candidate_auth_header, db_session):
    """
    Scenario 2: Valid resume in DOCX format.
    Must pass multi-signal validation, persist in database, and extract skills.
    """
    docx_bytes = create_synthetic_docx([
        "Marcus Vance",
        "Email: marcus.vance@example.com | Phone: 555-890-1234 | Seattle, WA",
        "GitHub: github.com/marcusvance | Portfolio: marcusvance.github.io",
        "Summary",
        "Full stack engineer with 4 years experience developing modern web applications.",
        "Work Experience",
        "Full Stack Developer - Pacific Cloud (2020 - Present)",
        "- Developed microservices in Python and Node.js with MongoDB and PostgreSQL.",
        "- Built responsive React dashboards and internal analytics tools.",
        "Education",
        "Bachelor of Science in Software Engineering, University of Washington (2016 - 2020)",
        "Technical Skills",
        "Python, React, TypeScript, Node.js, PostgreSQL, Docker, Git"
    ])

    response = client.post(
        "/api/v1/resumes/parse",
        files={"file": ("marcus_vance_resume.docx", io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=candidate_auth_header
    )
    assert response.status_code == 200
    data = response.json()
    assert data["validation"]["is_valid"] is True
    assert data["validation"]["document_type"] == "resume"


def test_3_research_paper_with_technical_skills_rejected(client, db_session):
    """
    Scenario 3: Research paper with technical skills and job-related keywords.
    SmartHire must NOT mistake it for a resume despite heavy technical vocabulary (Python, PyTorch, SQL).
    Must be rejected with 400 and NOT saved in database.
    """
    count_before = db_session.query(Resume).count()

    paper_pdf_bytes = create_synthetic_pdf([
        "Deep Residual Learning for Large-Scale Visual Recognition",
        "Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun",
        "Microsoft Research, Beijing, China",
        "{kahe, xiangz, v-shren, jiansun}@microsoft.com",
        "Abstract",
        "Deeper neural networks are more difficult to train. We present a residual learning framework",
        "to ease the training of networks that are substantially deeper than those used previously.",
        "We evaluate residual networks on the ImageNet dataset with a depth of up to 152 layers.",
        "1. Introduction",
        "Deep convolutional neural networks [1, 2] have led to a series of breakthroughs.",
        "Driven by the significance of depth, an obstacle is vanishing gradients [3, 4, 5].",
        "2. Related Work",
        "Residual representations have been widely used in computer vision [6, 7].",
        "3. Proposed Methodology",
        "We hypothesize that multiple nonlinear layers can asymptotically approximate residual functions.",
        "All models were trained in Python and PyTorch using distributed GPU computing.",
        "4. Experiments and Results",
        "Our ResNet models achieved a top-5 error rate of 3.57% on the ImageNet 2012 test set.",
        "5. Conclusion",
        "We have presented residual networks that overcome the degradation problem.",
        "References",
        "[1] Y. LeCun et al. Gradient-based learning applied to document recognition. IEEE, 1998.",
        "[2] A. Krizhevsky et al. ImageNet classification with deep CNNs. NeurIPS, 2012.",
        "[3] K. Simonyan and A. Zisserman. Very deep convolutional networks. ICLR, 2015.",
        "[4] C. Szegedy et al. Going deeper with convolutions. CVPR, 2015."
    ])

    response = client.post(
        "/api/v1/resumes/parse",
        files={"file": ("resnet_paper.pdf", io.BytesIO(paper_pdf_bytes), "application/pdf")}
    )
    assert response.status_code == 400
    assert "does not appear to be a resume" in response.json()["detail"]

    # Verify no resume record was created
    count_after = db_session.query(Resume).count()
    assert count_after == count_before


def test_4_academic_assignment_rejected(client, db_session):
    """
    Scenario 4: An academic assignment / problem set.
    Must be rejected with 400.
    """
    hw_text = (
        "CS 229: Machine Learning - Homework Assignment 2\n"
        "Instructor: Prof. Andrew Ng | Due Date: November 15, 2026\n"
        "Total Points: 100\n\n"
        "Submission Guidelines: Submit your Python solution to Gradescope.\n\n"
        "Problem 1: Logistic Regression and Newton's Method (35 points)\n"
        "Implement binary logistic regression in Python with NumPy. Plot the cost curve.\n\n"
        "Problem 2: Support Vector Machines (35 points)\n"
        "Derive the dual Lagrangian formulation for the soft-margin SVM.\n\n"
        "Problem 3: Neural Network Backpropagation (30 points)\n"
        "Compute gradients for a multilayer perceptron with ReLU activations."
    )

    response = client.post(
        "/api/v1/resumes/parse",
        data={"raw_text": hw_text, "filename": "cs229_hw2.txt"}
    )
    assert response.status_code == 400
    assert "does not appear to be a resume" in response.json()["detail"]


def test_5_invoice_or_unrelated_report_rejected(client, db_session):
    """
    Scenario 5: An invoice and an unrelated meeting report.
    Both must be rejected with 400.
    """
    # 5A: Financial Invoice
    invoice_text = (
        "Acme Cloud Technologies Inc.\n"
        "INVOICE #INV-2026-9041\n"
        "Invoice Date: October 20, 2026 | Due Date: November 20, 2026\n"
        "Bill To: Enterprise Systems LLC\n"
        "Description              Qty    Unit Price    Amount\n"
        "Python Backend Hosting    1     $1,200.00    $1,200.00\n"
        "Database Maintenance      1       $500.00      $500.00\n"
        "Subtotal: $1,700.00\n"
        "Tax (10%): $170.00\n"
        "Total Due: $1,870.00\n"
        "Payment Terms: Net 30 days. Remit to Acme Bank Transfer."
    )
    resp_inv = client.post(
        "/api/v1/resumes/parse",
        data={"raw_text": invoice_text, "filename": "invoice_9041.txt"}
    )
    assert resp_inv.status_code == 400
    assert "does not appear to be a resume" in resp_inv.json()["detail"]

    # 5B: Unrelated Meeting Report
    report_text = (
        "Executive Strategy Committee - Meeting Minutes\n"
        "Date: October 22, 2026 | Attendees: CEO, CTO, CFO, VP Sales\n"
        "Agenda: Q4 Cloud Budget and Technology Infrastructure\n"
        "Action Items:\n"
        "- Upgrade server clusters to Python 3.12 by end of month.\n"
        "- Review AWS budget allocations with engineering leads.\n"
        "- Next meeting scheduled for next Thursday at 10:00 AM."
    )
    resp_rep = client.post(
        "/api/v1/resumes/parse",
        data={"raw_text": report_text, "filename": "meeting_minutes.txt"}
    )
    assert resp_rep.status_code == 400
    assert "does not appear to be a resume" in resp_rep.json()["detail"]


def test_6_corrupted_and_empty_file_rejected(client):
    """
    Scenario 6: Corrupted or 0-byte file.
    Must be rejected with 400.
    """
    # 6A: Empty file (0 bytes)
    resp_empty = client.post(
        "/api/v1/resumes/parse",
        files={"file": ("empty_resume.pdf", io.BytesIO(b""), "application/pdf")}
    )
    assert resp_empty.status_code == 400
    assert "empty" in resp_empty.json()["detail"].lower()

    # 6B: Corrupted PDF file
    corrupted_bytes = b"%PDF-1.4\ncorrupted gibberish not a real pdf\x00\xff%%EOF"
    resp_corrupt = client.post(
        "/api/v1/resumes/parse",
        files={"file": ("corrupted_resume.pdf", io.BytesIO(corrupted_bytes), "application/pdf")}
    )
    assert resp_corrupt.status_code == 400
    assert ("corrupted" in resp_corrupt.json()["detail"].lower() or "failed to extract" in resp_corrupt.json()["detail"].lower())


def test_7_scanned_pdf_no_extractable_text(client):
    """
    Scenario 7: Scanned PDF with no extractable text.
    Must return clear user message explaining readable text could not be extracted.
    """
    scanned_bytes = create_scanned_pdf()
    response = client.post(
        "/api/v1/resumes/parse",
        files={"file": ("scanned_resume.pdf", io.BytesIO(scanned_bytes), "application/pdf")}
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "readable text could not be extracted" in detail.lower()


def test_8_resume_unusual_format_accepted(client, candidate_auth_header):
    """
    Scenario 8: Resume with unusual format or missing conventional sections.
    Should NOT be rejected simply because it lacks standard headers or contains research experience.
    """
    # 8A: Narrative style resume without uppercase "WORK EXPERIENCE" section header
    narrative_resume = (
        "Devon Riley\n"
        "devon.riley@gmail.com | (555) 765-4321 | Denver, CO\n"
        "Software engineer with 4 years experience specializing in cloud backend infrastructure.\n"
        "At DataStream Corp from 2021 to 2024, I designed microservices in Python, FastAPI, and PostgreSQL.\n"
        "Prior to that, at StartupWorks (2019 - 2021), I developed React and Node.js web applications.\n"
        "Graduated with a Bachelor of Science in Information Technology from State University in 2019.\n"
        "Skills: Python, FastAPI, PostgreSQL, Docker, AWS, React, TypeScript."
    )
    resp_narrative = client.post(
        "/api/v1/resumes/parse",
        data={"raw_text": narrative_resume, "filename": "devon_resume.txt"},
        headers=candidate_auth_header
    )
    assert resp_narrative.status_code == 200
    assert resp_narrative.json()["validation"]["is_valid"] is True

    # 8B: ML Researcher resume with publications section
    researcher_resume = (
        "Dr. Sarah Lin\n"
        "sarah.lin@email.com | (555) 321-7654 | Boston, MA | github.com/sarahlin-ai\n"
        "Summary:\n"
        "AI Research Scientist with 4 years experience developing deep learning architectures.\n"
        "Experience:\n"
        "Senior AI Researcher - DeepMind (2022 - Present)\n"
        "- Developed large language model evaluation frameworks using Python and PyTorch.\n"
        "- Optimized multi-GPU training clusters reducing training compute by 30%.\n"
        "Research Assistant - MIT AI Lab (2018 - 2022)\n"
        "- Researched transformer attention mechanisms in Python.\n"
        "Education:\n"
        "Ph.D. in Computer Science - Massachusetts Institute of Technology (2018 - 2022)\n"
        "B.S. in Computer Science - Carnegie Mellon University (2014 - 2018)\n"
        "Skills: Python, PyTorch, JAX, C++, CUDA, Distributed Systems, Git\n"
        "Selected Publications:\n"
        "- Lin, S., et al. 'Efficient Transformer Attention', NeurIPS 2021.\n"
        "- Lin, S., et al. 'Scaling Laws for Multi-Modal Models', ICML 2022."
    )
    resp_researcher = client.post(
        "/api/v1/resumes/parse",
        data={"raw_text": researcher_resume, "filename": "sarah_lin_cv.txt"},
        headers=candidate_auth_header
    )
    assert resp_researcher.status_code == 200
    assert resp_researcher.json()["validation"]["is_valid"] is True


def test_9_ambiguous_document_rejected(client):
    """
    Scenario 9: Ambiguous document lacking resume structure.
    Must return 400 asking user to upload a clearer resume.
    """
    ambiguous_text = (
        "Notes from today's discussion: Need to learn more Python and SQL for the upcoming project. "
        "Also check the schedule for next Wednesday afternoon."
    )
    response = client.post(
        "/api/v1/resumes/parse",
        data={"raw_text": ambiguous_text, "filename": "random_notes.txt"}
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "could not be verified as a resume" in detail.lower() or "clearer or more complete resume" in detail.lower()


def test_10_regression_rejected_document_never_triggers_job_matching(client, db_session):
    """
    Scenario 10: Regression test proving that rejected documents NEVER trigger job matching.
    Ensures that invalid documents (e.g. research papers, invoices):
    1. Are rejected at the upload/parse stage with HTTP 400.
    2. Never create a Resume entity in the database.
    3. Cannot trigger /jobs/recommend when rejected text is supplied.
    4. Cannot trigger /matching/score when rejected text is supplied.
    """
    research_paper_text = (
        "Attention Is All You Need\n"
        "Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit\n"
        "Google Brain, Google Research\n"
        "Abstract\n"
        "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.\n"
        "We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.\n"
        "1. Introduction\n"
        "Recurrent models typically factor computation along symbol positions [1, 2].\n"
        "2. Related Work\n"
        "The goal of reducing sequential computation forms the foundation of Extended Neural GPU [3].\n"
        "3. Model Architecture and Methodology\n"
        "The Transformer follows this overall architecture using stacked self-attention and point-wise layers.\n"
        "4. Experiments and Results\n"
        "We train our models on the standard WMT 2014 English-German dataset using Python and PyTorch.\n"
        "5. Conclusion\n"
        "In this work, we presented the Transformer, the first sequence transduction model based entirely on attention.\n"
        "References\n"
        "[1] S. Hochreiter et al. Long short-term memory. Neural Computation, 1997.\n"
        "[2] D. Bahdanau et al. Neural machine translation by jointly learning to align and translate. ICLR, 2015.\n"
        "[3] I. Sutskever et al. Sequence to sequence learning with neural networks. NeurIPS, 2014."
    )

    # 1. Attempt upload/parse -> Must fail with 400
    parse_resp = client.post(
        "/api/v1/resumes/parse",
        data={"raw_text": research_paper_text, "filename": "transformer_paper.txt"}
    )
    assert parse_resp.status_code == 400

    # 2. Verify no resume record exists in database
    persisted = db_session.query(Resume).filter(Resume.original_filename == "transformer_paper.txt").first()
    assert persisted is None

    # 3. Attempt direct job recommendations using rejected text -> Must fail with 400
    rec_resp = client.post(
        "/api/v1/jobs/recommend",
        json={"resume_text": research_paper_text, "top_n": 5}
    )
    assert rec_resp.status_code == 400
    assert "Cannot recommend jobs" in rec_resp.json()["detail"]

    # 4. Attempt direct job matching calculation using rejected text -> Must fail with 400
    match_resp = client.post(
        "/api/v1/matching/score",
        json={
            "resume_text": research_paper_text,
            "job_text": "Looking for a Senior Python and PyTorch Machine Learning Engineer with AWS experience.",
            "job_skills": "Python, PyTorch, AWS"
        }
    )
    assert match_resp.status_code == 400
    assert "Cannot compute match score" in match_resp.json()["detail"]


def test_11_dedicated_validate_endpoint(client):
    """
    Scenario 11: Direct verification of the POST /api/v1/resumes/validate endpoint.
    Returns structured validation result without persisting anything.
    """
    # 11A: Valid resume
    valid_text = (
        "Alice Smith\n"
        "alice@example.com | (555) 123-4567\n"
        "Experience\n"
        "Data Engineer at TechCorp (2020 - Present)\n"
        "- Built Spark pipelines in Python and SQL\n"
        "Education\n"
        "B.S. in Computer Science\n"
        "Skills: Python, SQL, Spark, Docker"
    )
    resp_val = client.post(
        "/api/v1/resumes/validate",
        data={"raw_text": valid_text, "filename": "resume.txt"}
    )
    assert resp_val.status_code == 200
    val_data = resp_val.json()
    assert val_data["is_valid"] is True
    assert val_data["confidence_category"] in ["HIGH", "MEDIUM"]
    assert val_data["is_calibrated_probability"] is False
    assert val_data["document_type"] == "resume"

    # 11B: Research paper
    paper_text = (
        "Paper Title: Novel Methods in Deep Learning\n"
        "Abstract\n"
        "We propose a new approach to representation learning in neural networks.\n"
        "1. Introduction\n"
        "Deep learning models [1, 2] have shown strong performance.\n"
        "2. Methodology\n"
        "Our method optimizes gradient flow.\n"
        "3. Results\n"
        "We evaluate on benchmark datasets.\n"
        "References\n"
        "[1] Author A, 2020. [2] Author B, 2021."
    )
    resp_paper = client.post(
        "/api/v1/resumes/validate",
        data={"raw_text": paper_text, "filename": "paper.txt"}
    )
    assert resp_paper.status_code == 200
    paper_val = resp_paper.json()
    assert paper_val["is_valid"] is False
    assert paper_val["document_type"] == "research_paper"
    assert "research paper" in paper_val["rejection_reason"].lower()
    assert "This document does not appear to be a resume" in paper_val["user_message"]
