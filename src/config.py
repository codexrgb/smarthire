"""
Configuration file for SmartHire project.
Defines paths, constants, schema column aliases, skill dictionary, and model hyper-parameters.
"""

from pathlib import Path

# Paths
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
METRICS_DIR = REPORTS_DIR / "metrics"

# Ensure essential directories exist
for folder in [
    DATA_DIR, RAW_DATA_DIR, INTERIM_DATA_DIR, PROCESSED_DATA_DIR,
    MODELS_DIR, REPORTS_DIR, FIGURES_DIR, METRICS_DIR
]:
    folder.mkdir(parents=True, exist_ok=True)

# Dataset Column Aliases for Dynamic Schema Detection
COLUMN_ALIASES = {
    "title": ["title", "job_title", "jobtitle", "position", "role", "job_role", "Job Title"],
    "description": ["description", "job_description", "jobdescription", "details", "summary", "Job Description", "job_details"],
    "skills": ["skills", "skill", "required_skills", "key_skills", "Key Skills", "skills_required", "tags"],
    "company": ["company", "company_name", "organization", "Company", "employer"],
    "location": ["location", "job_location", "city", "Location", "place", "state"],
    "experience": ["experience", "experience_required", "years_experience", "Experience", "exp_required"],
    "salary": ["salary", "salary_range", "ctc", "pay", "Salary", "remuneration"],
    "resume_text": ["resume_text", "resume", "Text", "Resume", "Resume_str", "resume_content", "text"],
    "category": ["category", "job_category", "Category", "label", "target", "domain"]
}

# Skill Alias Dictionary Mapping
SKILL_ALIAS_MAP = {
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "html": "HTML",
    "html5": "HTML",
    "css": "CSS",
    "css3": "CSS",
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "angular": "Angular",
    "angularjs": "Angular",
    "vue": "Vue",
    "vuejs": "Vue",
    "vue.js": "Vue",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "express": "Express",
    "expressjs": "Express",
    "express.js": "Express",
    "flask": "Flask",
    "django": "Django",
    "spring": "Spring",
    "springboot": "Spring Boot",
    "spring boot": "Spring Boot",
    "spring-boot": "Spring Boot",
    "sql": "SQL",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "redis": "Redis",
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "dl": "Deep Learning",
    "deep learning": "Deep Learning",
    "ai": "Artificial Intelligence",
    "artificial intelligence": "Artificial Intelligence",
    "a.i.": "Artificial Intelligence",
    "ds": "Data Science",
    "data science": "Data Science",
    "nlp": "NLP",
    "natural language processing": "NLP",
    "cv": "Computer Vision",
    "computer vision": "Computer Vision",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "sklearn": "Scikit-learn",
    "scikit-learn": "Scikit-learn",
    "scikit learn": "Scikit-learn",
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    "keras": "Keras",
    "opencv": "OpenCV",
    "git": "Git",
    "github": "GitHub",
    "docker": "Docker",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "amazon web services": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "google cloud": "GCP",
    "power bi": "Power BI",
    "powerbi": "Power BI",
    "tableau": "Tableau",
    "excel": "Excel",
    "ms excel": "Excel",
    "linux": "Linux",
    "unix": "Linux",
    "rest api": "REST API",
    "rest": "REST API",
    "graphql": "GraphQL",
    "python": "Python",
    "java": "Java",
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "csharp": "C#"
}

# Master List of Required Skills
MASTER_SKILLS = sorted(list(set(SKILL_ALIAS_MAP.values())))

# Model Training Parameters
CLASSIFIER_TFIDF_PARAMS = {
    "max_features": 10000,
    "ngram_range": (1, 2),
    "sublinear_tf": True,
    "min_df": 2
}

RECOMMENDER_TFIDF_PARAMS = {
    "max_features": 15000,
    "ngram_range": (1, 2),
    "stop_words": "english",
    "sublinear_tf": True
}

DEFAULT_N_CLUSTERS = 5
DEMO_WARNING_MESSAGE = (
    "DEMO MODE: Synthetic data is being used. These metrics must not be used as final project results."
)
