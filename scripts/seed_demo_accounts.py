"""
Seeds two synthetic demo accounts into MySQL smarthire_test for user manual testing:
1. candidate.demo@smarthire.local (Password: CandidateDemo123!)
2. recruiter.demo@smarthire.local (Password: RecruiterDemo123!)
"""

import sys
import uuid
import hashlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.backend.database import SessionLocal
from src.backend.models.user import User
from src.backend.models.resume import Resume
from src.backend.security.hashing import hash_password

def seed_demo_accounts():
    db = SessionLocal()
    try:
        # Candidate
        cand = db.query(User).filter(User.email == 'candidate.demo@smarthire.local').first()
        if not cand:
            cand = User(
                id=str(uuid.uuid4()),
                email='candidate.demo@smarthire.local',
                hashed_password=hash_password('CandidateDemo123!'),
                full_name='Alice Candidate Demo',
                role='candidate',
                is_active=True
            )
            db.add(cand)
            db.flush()
            print('Created user: candidate.demo@smarthire.local')

        # Resume for Alice
        res = db.query(Resume).filter(Resume.candidate_id == cand.id).first()
        if not res:
            res_sha = hashlib.sha256(b'Senior Python engineer demo content').hexdigest()
            res = Resume(
                id=str(uuid.uuid4()),
                candidate_id=cand.id,
                original_filename='demo_software_engineer_resume.pdf',
                storage_path=f'demo/{res_sha}.pdf',
                file_size_bytes=45200,
                sha256=res_sha,
                clean_text='Senior Full Stack Engineer with 6+ years experience in Python, FastAPI, React, Docker, and SQL. Contact: [EMAIL MASKED], [PHONE MASKED]. Built microservices, recommendation engines, and high-performance APIs.',
                predicted_category='Data Science',
                category_confidence=0.92,
                extracted_skills='["Python", "FastAPI", "React", "Docker", "SQL"]'
            )
            db.add(res)
            print('Attached demo resume to Alice')

        # Recruiter
        rec = db.query(User).filter(User.email == 'recruiter.demo@smarthire.local').first()
        if not rec:
            rec = User(
                id=str(uuid.uuid4()),
                email='recruiter.demo@smarthire.local',
                hashed_password=hash_password('RecruiterDemo123!'),
                full_name='Bob Recruiter Demo',
                role='recruiter',
                is_active=True
            )
            db.add(rec)
            print('Created user: recruiter.demo@smarthire.local')

        db.commit()
        print('SUCCESS: Demo accounts and resume seeded successfully in MySQL smarthire_test!')
    finally:
        db.close()

if __name__ == '__main__':
    seed_demo_accounts()
