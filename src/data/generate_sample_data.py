"""
Sample Data Generator for SmartHire.
Generates realistic demo datasets for Resumes and Job Listings if raw external data is absent.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from src.config import RAW_DATA_DIR

JOB_CATEGORIES = [
    "Data Science", "HR", "Advocate", "Arts", "Web Designing",
    "Mechanical Engineer", "Sales", "Health and Fitness", "Civil Engineer",
    "Java Developer", "Business Analyst", "SAP Developer", "Automation Testing",
    "Electrical Engineering", "Operations Manager", "Python Developer",
    "DevOps Engineer", "Network Security Engineer", "PMO", "Database",
    "Hadoop", "ETL Developer", "DotNet Developer", "Blockchain", "Testing"
]

CATEGORY_SKILLS_MAP = {
    "Data Science": ["Python", "Machine Learning", "Pandas", "NumPy", "Scikit-Learn", "SQL", "Tableau", "Deep Learning", "PyTorch"],
    "HR": ["Recruitment", "Employee Relations", "HR Policies", "Talent Acquisition", "Onboarding", "Payroll", "Excel"],
    "Advocate": ["Legal Drafting", "Corporate Law", "Litigation", "Contract Negotiation", "Compliance", "Arbitration"],
    "Arts": ["Graphic Design", "Photoshop", "Illustrator", "UI/UX", "Creative Writing", "Fine Arts", "Animation"],
    "Web Designing": ["HTML", "CSS", "JavaScript", "React", "UI/UX", "Figma", "Web Design", "WordPress"],
    "Mechanical Engineer": ["CAD", "SolidWorks", "AutoCAD", "Thermodynamics", "Manufacturing", "Mechanical Design", "ANSYS"],
    "Sales": ["Sales Strategy", "Lead Generation", "B2B Sales", "Negotiation", "CRM", "Client Relationship", "Account Management"],
    "Health and Fitness": ["Nutrition", "Personal Training", "Wellness", "Kinesiology", "Health Assessment", "Diet Planning"],
    "Civil Engineer": ["AutoCAD", "Structural Analysis", "Site Management", "Construction Management", "Civil Engineering", "STAAD Pro"],
    "Java Developer": ["Java", "Spring", "Spring Boot", "Hibernate", "REST API", "SQL", "MySQL", "Microservices", "Git"],
    "Business Analyst": ["Requirements Gathering", "SQL", "Excel", "Power BI", "Tableau", "Agile", "Jira", "UML", "Business Analysis"],
    "SAP Developer": ["SAP ABAP", "SAP HANA", "SAP Fiori", "ERP", "Business Objects", "SAP MM", "SAP SD"],
    "Automation Testing": ["Selenium", "Java", "Python", "TestNG", "Automation Testing", "JUnit", "Jenkins", "API Testing"],
    "Electrical Engineering": ["Circuit Design", "PLC", "SCADA", "MATLAB", "Power Systems", "Electrical Engineering", "AutoCAD"],
    "Operations Manager": ["Operations Management", "Process Optimization", "Supply Chain", "Logistics", "Budgeting", "KPI Tracking"],
    "Python Developer": ["Python", "Django", "Flask", "REST API", "PostgreSQL", "Docker", "Git", "Celery", "Redis"],
    "DevOps Engineer": ["Docker", "Kubernetes", "AWS", "CI/CD", "Jenkins", "Terraform", "Linux", "Python", "Git"],
    "Network Security Engineer": ["Network Security", "Firewalls", "Cisco", "Cybersecurity", "VPN", "Wireshark", "Penetration Testing"],
    "PMO": ["Project Management", "Agile", "Scrum", "PMO", "Risk Management", "Jira", "MS Project", "Stakeholder Management"],
    "Database": ["SQL", "MySQL", "PostgreSQL", "Database Administration", "Oracle", "Query Optimization", "ETL", "NoSQL"],
    "Hadoop": ["Hadoop", "Hive", "Pig", "Spark", "Big Data", "Kafka", "MapReduce", "Java"],
    "ETL Developer": ["ETL", "Informatica", "SQL", "Data Warehousing", "SSIS", "Talend", "Python"],
    "DotNet Developer": ["C#", ".NET", "ASP.NET", "Entity Framework", "SQL Server", "REST API", "MVC"],
    "Blockchain": ["Solidity", "Blockchain", "Ethereum", "Smart Contracts", "Web3.js", "Cryptography", "Go"],
    "Testing": ["Manual Testing", "Test Cases", "Bug Tracking", "Jira", "Regression Testing", "Quality Assurance"]
}

COMPANIES = [
    "TechCorp Solutions", "DataGlobe Inc", "CloudScale Systems", "InnovateTech",
    "Apex Global", "NextGen Enterprise", "CyberShield Labs", "InfoSys Technologies",
    "Alpha Analytics", "Zenith Software", "Pinnacle Digital", "Vanguard Systems"
]

LOCATIONS = ["New York, NY", "San Francisco, CA", "Austin, TX", "Chicago, IL", "Seattle, WA", "Remote", "Boston, MA", "Bangalore, IN", "London, UK"]


def generate_synthetic_resumes(n_samples: int = 960) -> pd.DataFrame:
    """Generates synthetic resume dataset for classification benchmarking."""
    np.random.seed(42)
    records = []

    for i in range(n_samples):
        cat = np.random.choice(JOB_CATEGORIES)
        skills = CATEGORY_SKILLS_MAP[cat]
        selected_skills = np.random.choice(skills, size=min(len(skills), np.random.randint(3, 7)), replace=False)

        years_exp = np.random.randint(1, 12)
        degree = np.random.choice(["B.Tech in Computer Science", "B.S. in Information Technology", "M.S. in Data Science", "MBA", "B.E. Mechanical", "B.A. Communications"])

        text = (
            f"Experienced {cat} professional with {years_exp} years of experience in industry projects. "
            f"Education: {degree}. Proven track record in delivery and execution. "
            f"Key technical skills and competencies include: {', '.join(selected_skills)}. "
            f"Demonstrated proficiency in {selected_skills[0]} and {selected_skills[-1]}. "
            f"Worked on cross-functional teams to deliver high-quality solutions."
        )

        records.append({
            "Resume_id": f"RES_{i+1:04d}",
            "Category": cat,
            "Resume_str": text
        })

    return pd.DataFrame(records)


def generate_synthetic_jobs(n_samples: int = 300) -> pd.DataFrame:
    """Generates synthetic job postings dataset for recommendation & clustering."""
    np.random.seed(42)
    records = []

    for i in range(n_samples):
        cat = np.random.choice(JOB_CATEGORIES)
        skills = CATEGORY_SKILLS_MAP[cat]
        selected_skills = np.random.choice(skills, size=min(len(skills), np.random.randint(4, 8)), replace=False)

        min_exp = np.random.randint(1, 5)
        max_exp = min_exp + np.random.randint(2, 6)
        min_sal = np.random.choice([60000, 80000, 100000, 120000])
        max_sal = min_sal + 40000

        title = f"{cat} - {np.random.choice(['Senior', 'Junior', 'Lead', 'Specialist', 'Associate'])}"
        company = np.random.choice(COMPANIES)
        location = np.random.choice(LOCATIONS)

        description = (
            f"We are hiring a {title} at {company} located in {location}. "
            f"The ideal candidate must have {min_exp} to {max_exp} years of experience. "
            f"Key responsibilities include designing, developing, and maintaining systems in {cat} domain. "
            f"Required Skills: {', '.join(selected_skills)}. Strong background in {selected_skills[0]} required."
        )

        records.append({
            "job_id": f"JOB_{i+1:04d}",
            "job_title": title,
            "company_name": company,
            "job_location": location,
            "required_skills": ", ".join(selected_skills),
            "experience_required": f"{min_exp}-{max_exp} years",
            "salary_range": f"${min_sal:,} - ${max_sal:,}",
            "job_description": description,
            "job_category": cat
        })

    return pd.DataFrame(records)


def ensure_sample_datasets_exist():
    """Checks if raw data exists; if not, creates synthetic demo CSVs in data/raw."""
    resumes_file = RAW_DATA_DIR / "UpdatedResumeDataSet.csv"
    jobs_naukri_file = RAW_DATA_DIR / "naukri_com-job_sample.csv"
    jobs_linkedin_file = RAW_DATA_DIR / "linkedin_job_postings.csv"

    # Check if any raw csv file exists in data/raw
    raw_csvs = list(RAW_DATA_DIR.glob("*.csv"))

    if not raw_csvs:
        print("[DATA GENERATOR] No raw CSV files found in data/raw/. Generating synthetic demo datasets...")
        resumes_df = generate_synthetic_resumes(960)
        naukri_df = generate_synthetic_jobs(200)
        linkedin_df = generate_synthetic_jobs(150)

        resumes_df.to_csv(resumes_file, index=False)
        naukri_df.to_csv(jobs_naukri_file, index=False)
        linkedin_df.to_csv(jobs_linkedin_file, index=False)
        print(f"[DATA GENERATOR] Generated {len(resumes_df)} resumes and {len(naukri_df) + len(linkedin_df)} job postings.")
    else:
        print(f"[DATA GENERATOR] Found existing raw dataset files: {[f.name for f in raw_csvs]}")


if __name__ == "__main__":
    ensure_sample_datasets_exist()
