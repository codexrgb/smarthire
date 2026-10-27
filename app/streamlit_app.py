"""
SmartHire Streamlit Web Application.
Resume-to-Job Matching & Career Guidance Engine (Classical Machine Learning).
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Streamlit Page Config MUST be the very first Streamlit command
st.set_page_config(
    page_title="SmartHire | Resume Matching & Career Guidance",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

from src.config import FIGURES_DIR, METRICS_DIR, MASTER_SKILLS, MODELS_DIR, DEMO_WARNING_MESSAGE
from src.parsing.resume_parser import extract_resume_text
from src.features.text_features import extract_skills, calculate_skill_match, generate_skill_gap
from src.models.classifier import predict_resume_category
from src.models.recommender import recommend_jobs
from src.models.clustering import extract_nmf_topics
from src.utils.security import (
    escape_html_text, render_skill_pill, render_skill_pills, sanitize_job_card_meta
)
from app.utils import (
    load_trained_models, load_processed_datasets, load_metrics_and_status,
    apply_custom_css, SAMPLE_RESUMES
)

# Apply Styling
apply_custom_css()

# Header Banner
st.markdown("""
<div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 24px; border-radius: 12px; color: white; margin-bottom: 20px;">
    <h1 style="margin: 0; font-size: 2.3rem; color: #ffffff;">💼 SmartHire</h1>
    <p style="margin: 5px 0 0 0; font-size: 1.1rem; opacity: 0.9;">
        Resume-to-Job Matching & Career Guidance Engine (Classical Machine Learning)
    </p>
</div>
""", unsafe_allow_html=True)

# Load Artifacts
models = load_trained_models()
resumes_df, jobs_df = load_processed_datasets()
metrics, pipeline_status = load_metrics_and_status()

# Dataset Provenance & Demo Mode Warning Banner across App
prov = pipeline_status.get("provenance", {})
prov_status = prov.get("overall_status", "demo_synthetic")

if prov_status == "demo_synthetic":
    banner_msg = prov.get("banner_message", f"⚠️ {DEMO_WARNING_MESSAGE}")
    st.markdown(f'<div class="demo-warning-banner">{escape_html_text(banner_msg)}</div>', unsafe_allow_html=True)
elif prov_status == "unknown_unverified":
    banner_msg = prov.get("banner_message", "⚠️ UNVERIFIED DATASET: Dataset provenance has not been cryptographically verified. Results cannot be certified.")
    st.markdown(f'<div class="unverified-warning-banner">{escape_html_text(banner_msg)}</div>', unsafe_allow_html=True)
elif prov_status == "verified_authentic":
    banner_msg = prov.get("banner_message", "🟢 VERIFIED DATA MODE ACTIVE: All models trained on verified authentic datasets.")
    st.markdown(f'<div class="real-mode-banner">{escape_html_text(banner_msg)}</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="demo-warning-banner">⚠️ {escape_html_text(DEMO_WARNING_MESSAGE)}</div>', unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "📊 Dashboard",
        "📄 Resume Analysis",
        "🎯 Job Recommendations",
        "🧩 Skill Gap",
        "🔍 Job Explorer",
        "📌 Job Clustering",
        "📈 Model Analytics",
        "ℹ️ About"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("""
**Engine Specs:**
- Classical ML & NLP Only
- TF-IDF + Logistic Regression / LinearSVC
- Cosine Similarity Recommender
- KMeans Clustering & 2D PCA
- NMF Topic Modeling
- No LLMs / Generative AI
""")

# Initialize Session State
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "selected_job" not in st.session_state:
    st.session_state.selected_job = None


# ==============================================================================
# PAGE 1: DASHBOARD
# ==============================================================================
if page == "📊 Dashboard":
    st.subheader("System Overview & Dataset Status")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(jobs_df)}</div>
            <div class="metric-label">Total Job Listings</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        n_cats = resumes_df["category"].nunique() if not resumes_df.empty and "category" in resumes_df.columns else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{n_cats}</div>
            <div class="metric-label">Resume Categories</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(MASTER_SKILLS)}</div>
            <div class="metric-label">Master Tech Skills</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        if prov_status == "verified_authentic":
            mode_label = "Verified Real 🟢"
        elif prov_status == "unknown_unverified":
            mode_label = "Unverified 🟡"
        else:
            mode_label = "Demo / Synthetic 🔴"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{escape_html_text(mode_label)}</div>
            <div class="metric-label">Dataset Engine Mode</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if not resumes_df.empty and "category" in resumes_df.columns:
        st.subheader("Resume Category Distribution")
        cat_counts = resumes_df["category"].value_counts().head(15)

        fig, ax = plt.subplots(figsize=(10, 4.5))
        sns.barplot(x=cat_counts.values, y=cat_counts.index, palette="Blues_r", ax=ax)
        ax.set_title("Top Resume Categories in Processed Dataset", fontsize=12, fontweight="bold")
        ax.set_xlabel("Number of Resumes")
        ax.set_ylabel("Category")
        st.pyplot(fig)
        plt.close()

    st.markdown("### Quick Demo Profiles")
    st.write("Click any profile preset to test the engine:")
    p_cols = st.columns(4)
    for idx, (p_title, p_text) in enumerate(SAMPLE_RESUMES.items()):
        with p_cols[idx % 4]:
            if st.button(f"Load {p_title}", key=f"btn_p_{idx}"):
                st.session_state.resume_text = p_text
                st.success(f"Loaded {p_title}! Navigate to 'Resume Analysis' or 'Job Recommendations'.")


# ==============================================================================
# PAGE 2: RESUME ANALYSIS
# ==============================================================================
elif page == "📄 Resume Analysis":
    st.subheader("Resume Parsing, Category Prediction & Skill Extraction")

    tab1, tab2 = st.tabs(["📤 File Upload (PDF/DOCX/TXT)", "✍️ Manual Text Input"])

    with tab1:
        uploaded_file = st.file_uploader(
            "Upload Resume",
            type=["pdf", "docx", "txt"],
            help="Extract text using pypdf or python-docx"
        )
        if uploaded_file is not None:
            extracted_txt, msg = extract_resume_text(uploaded_file)
            if extracted_txt:
                st.success(f"Successfully extracted text! ({msg})")
                st.session_state.resume_text = extracted_txt
            else:
                st.error(msg)

    with tab2:
        manual_input = st.text_area(
            "Paste Resume Text",
            value=st.session_state.resume_text,
            height=200,
            placeholder="Paste raw resume text here..."
        )
        if st.button("Use Manual Text"):
            st.session_state.resume_text = manual_input
            st.success("Updated resume text!")

    if st.session_state.resume_text.strip():
        st.markdown("---")
        st.markdown("### 🔍 Analysis Results")

        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.markdown("#### 📖 1. Extracted Resume Text")
            with st.expander("View Extracted Text", expanded=True):
                st.text(st.session_state.resume_text[:2000] + ("..." if len(st.session_state.resume_text) > 2000 else ""))

            extracted_skills = extract_skills(st.session_state.resume_text)
            st.markdown("#### 🛠️ 3. Extracted Skills")
            if extracted_skills:
                pills_html = render_skill_pills(extracted_skills, pill_class="skill-pill")
                st.markdown(pills_html, unsafe_allow_html=True)
            else:
                st.warning("No standard technical skills detected from master dictionary.")

        with col_right:
            st.markdown("#### 🎯 2. Predicted Job Category")
            if "classifier" in models and "classifier_vectorizer" in models:
                cat_pred, conf, top_probs = predict_resume_category(
                    st.session_state.resume_text,
                    models["classifier"],
                    models["classifier_vectorizer"]
                )

                cat_pred_esc = escape_html_text(cat_pred)
                st.markdown(f"""
                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 16px; margin-bottom: 15px;">
                    <div style="font-size: 0.9rem; color: #166534; font-weight: 600;">PREDICTED CATEGORY</div>
                    <div style="font-size: 1.8rem; color: #15803d; font-weight: 700;">{cat_pred_esc}</div>
                    <div style="font-size: 0.85rem; color: #166534;">Confidence: <b>{conf*100:.1f}%</b></div>
                </div>
                """, unsafe_allow_html=True)

                if top_probs:
                    st.markdown("**Category Probability Distribution:**")
                    prob_df = pd.DataFrame(list(top_probs.items()), columns=["Category", "Probability"])
                    fig, ax = plt.subplots(figsize=(6, 3))
                    sns.barplot(x="Probability", y="Category", data=prob_df, palette="crest", ax=ax)
                    ax.set_xlim(0, 1.0)
                    st.pyplot(fig)
                    plt.close()
            else:
                st.warning("Classifier not loaded. Run `python train.py` first.")

        st.markdown("---")
        st.markdown("#### 🎯 4-7. Quick Recommendations & Skill Gap Preview")
        if not jobs_df.empty:
            recs = recommend_jobs(
                st.session_state.resume_text,
                jobs_df,
                vectorizer=models.get("job_vectorizer"),
                job_vectors=models.get("job_vectors"),
                top_n=3
            )
            if not recs.empty:
                top_job = recs.iloc[0]
                st.markdown(f"**Top Match Position:** `{top_job.get('title', 'N/A')}` at `{top_job.get('company', 'N/A')}`")
                st.markdown(f"**ML-Based Fit Score:** `{top_job.get('ml_fit_score', 0.0):.1f}%`")

                gap = generate_skill_gap(st.session_state.resume_text, top_job.get("skills", ""))
                st.markdown(f"**Matched Skills:** {', '.join(gap['matched_skills']) if gap['matched_skills'] else 'None'}")
                st.markdown(f"**Missing Skills:** {', '.join(gap['missing_skills']) if gap['missing_skills'] else 'None'}")
                st.markdown(f"**Recommended Skills to Improve:** {', '.join(gap['missing_skills']) if gap['missing_skills'] else 'None'}")
    else:
        st.info("Upload a resume or select a preset to analyze.")


# ==============================================================================
# PAGE 3: JOB RECOMMENDATIONS
# ==============================================================================
elif page == "🎯 Job Recommendations":
    st.subheader("TF-IDF Cosine Similarity Job Recommendation Engine")

    if not st.session_state.resume_text.strip():
        st.warning("Please upload a resume in 'Resume Analysis' page first.")
    elif jobs_df.empty:
        st.error("No job listings found in dataset. Run `python train.py`.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            top_n = st.selectbox("Top N Recommendations", [5, 10, 20], index=1)
        with c2:
            cats = ["All"] + sorted(jobs_df["category"].dropna().unique().tolist()) if "category" in jobs_df.columns else ["All"]
            selected_cat = st.selectbox("Category Filter", cats)

        recs = recommend_jobs(
            st.session_state.resume_text,
            jobs_df,
            vectorizer=models.get("job_vectorizer"),
            job_vectors=models.get("job_vectors"),
            top_n=top_n,
            category_filter=selected_cat
        )

        if recs.empty:
            st.warning("No matching jobs found for filter criteria.")
        else:
            st.markdown(f"### Top {len(recs)} Recommended Jobs")

            for idx, row in recs.iterrows():
                fit_score = row.get("ml_fit_score", 0.0)
                sim_score = row.get("similarity_score", 0.0) * 100.0
                skill_pct = row.get("skill_match_pct", 0.0)

                # Format and sanitize dataset fields cleanly
                meta = sanitize_job_card_meta(
                    title=row.get("title", "N/A"),
                    company=row.get("company", "N/A"),
                    location=row.get("location", "N/A"),
                    experience=row.get("experience", "N/A"),
                    salary=row.get("salary", "N/A")
                )
                j_title_raw = str(row.get("title", "N/A"))
                j_skills = str(row.get("skills", "N/A"))

                st.markdown(f"""
                <div class="job-card">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <div class="job-title">{meta['title']}</div>
                            <div class="job-meta">🏢 <b>{meta['company']}</b> &nbsp;|&nbsp; 📍 {meta['location']} &nbsp;|&nbsp; 💼 {meta['experience']} &nbsp;|&nbsp; 💵 {meta['salary']}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.6rem; font-weight: 800; color: #2563eb;">{fit_score:.1f}%</div>
                            <div style="font-size: 0.78rem; color: #64748b; font-weight: 600;">ML-Based Fit Score</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                st.progress(min(1.0, fit_score / 100.0))
                st.caption(f"Text Similarity: **{sim_score:.1f}%** | Skill Overlap: **{skill_pct:.1f}%**")

                if j_skills != "N/A":
                    skill_list = [s.strip() for s in j_skills.split(",") if s.strip()]
                    pills = render_skill_pills(skill_list[:8], pill_class="skill-pill")
                    st.markdown(f"**Required Skills:** {pills}", unsafe_allow_html=True)
                else:
                    st.markdown("**Required Skills:** N/A")

                if st.button(f"Analyze Skill Gap for '{j_title_raw}'", key=f"btn_rec_{idx}"):
                    st.session_state.selected_job = row.to_dict()
                    st.success(f"Selected '{j_title_raw}'! Head over to 'Skill Gap'.")

                st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# PAGE 4: SKILL GAP
# ==============================================================================
elif page == "🧩 Skill Gap":
    st.subheader("Candidate vs. Job Skill Gap Report")

    if not st.session_state.resume_text.strip():
        st.warning("Please upload a resume first.")
    elif jobs_df.empty:
        st.error("No jobs loaded. Run `python train.py`.")
    else:
        job_options = jobs_df["title"].dropna().tolist()
        default_idx = 0
        if st.session_state.selected_job and st.session_state.selected_job.get("title") in job_options:
            default_idx = job_options.index(st.session_state.selected_job["title"])

        selected_title = st.selectbox("Select Target Position", job_options, index=default_idx)
        target_row = jobs_df[jobs_df["title"] == selected_title].iloc[0]

        job_desc = str(target_row.get("description", "N/A"))
        job_skills = str(target_row.get("skills", "N/A"))

        gap_res = generate_skill_gap(st.session_state.resume_text, job_skills if job_skills != "N/A" else job_desc)

        match_pct = gap_res["match_percentage"]
        matched_skills = gap_res["matched_skills"]
        missing_skills = gap_res["missing_skills"]

        target_title_esc = escape_html_text(selected_title)
        target_comp_esc = escape_html_text(str(target_row.get('company', 'N/A')))
        target_loc_esc = escape_html_text(str(target_row.get('location', 'N/A')))

        st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px;">
            <h3>Target Role: <span style="color: #2563eb;">{target_title_esc}</span></h3>
            <p style="color: #475569;">Company: <b>{target_comp_esc}</b> | Location: <b>{target_loc_esc}</b></p>
            <h2 style="color: {'#16a34a' if match_pct >= 70 else '#d97706' if match_pct >= 40 else '#dc2626'};">
                Skill Match Percentage: {match_pct:.1f}%
            </h2>
        </div>
        """, unsafe_allow_html=True)

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown("#### ✅ Matched Skills")
            if matched_skills:
                st.markdown(render_skill_pills(matched_skills, pill_class="matched-skill-pill", prefix="✓ "), unsafe_allow_html=True)
            else:
                st.warning("No overlapping skills detected.")

        with col_g2:
            st.markdown("#### ❌ Missing Skills")
            if missing_skills:
                st.markdown(render_skill_pills(missing_skills, pill_class="missing-skill-pill", prefix="✗ "), unsafe_allow_html=True)
            else:
                st.success("No missing skills detected!")

        st.markdown("---")
        st.markdown("### 💡 Recommended Skills to Improve")
        if missing_skills:
            st.write("Based **strictly** on detected missing skills for this target role:")
            for s in missing_skills:
                st.markdown(f"- **{s}**: Build hands-on projects and practice coding exercises.")
        else:
            st.write("You possess all key technical skills listed for this position.")


# ==============================================================================
# PAGE 5: JOB EXPLORER
# ==============================================================================
elif page == "🔍 Job Explorer":
    st.subheader("Interactive Filterable Job Dataset")

    if jobs_df.empty:
        st.error("No dataset loaded. Run `python train.py`.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            f_title = st.text_input("Title Filter", "")
        with c2:
            f_loc = st.text_input("Location Filter", "")
        with c3:
            f_comp = st.text_input("Company Filter", "")

        df_fil = jobs_df.copy()
        if f_title:
            df_fil = df_fil[df_fil["title"].astype(str).str.contains(f_title, case=False, na=False)]
        if f_loc:
            df_fil = df_fil[df_fil["location"].astype(str).str.contains(f_loc, case=False, na=False)]
        if f_comp:
            df_fil = df_fil[df_fil["company"].astype(str).str.contains(f_comp, case=False, na=False)]

        st.markdown(f"**Showing {len(df_fil)} of {len(jobs_df)} jobs**")
        display_cols = ["job_id", "title", "company", "location", "skills", "experience", "salary", "category", "source"]
        existing = [c for c in display_cols if c in df_fil.columns]

        st.dataframe(df_fil[existing], use_container_width=True, height=450)

        csv_bytes = df_fil.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Filtered Jobs CSV",
            data=csv_bytes,
            file_name="smarthire_filtered_jobs.csv",
            mime="text/csv"
        )


# ==============================================================================
# PAGE 6: JOB CLUSTERING (DEDICATED PAGE)
# ==============================================================================

elif page == "📌 Job Clustering":
    st.subheader("Unsupervised Job Family Clustering & PCA Visualization")

    # Load clustering metrics
    clst_m = metrics.get("clustering", {})

    st.info(
        "Elbow Method and Silhouette Score may suggest different K values. "
        "The selected K is based on the declared selection criterion."
    )

    if clst_m:
        # ------------------------------------------------------------------
        # Selected K from Elbow Method
        # ------------------------------------------------------------------
        sel_k = clst_m.get(
            "selected_k_elbow",
            clst_m.get("n_clusters", 5)
        )

        # ------------------------------------------------------------------
        # Get K values and silhouette scores
        # ------------------------------------------------------------------
        k_values = clst_m.get("k_values")
        silhouette_scores = clst_m.get("silhouette_scores")

        # If they are not stored directly, build them from k_details
        if not k_values or not silhouette_scores:
            k_details = clst_m.get("k_details", [])

            k_values = [
                int(item["k"])
                for item in k_details
                if "k" in item and "silhouette_score" in item
            ]

            silhouette_scores = [
                float(item["silhouette_score"])
                for item in k_details
                if "k" in item and "silhouette_score" in item
            ]

        # ------------------------------------------------------------------
        # Calculate best silhouette K and maximum silhouette score
        # ------------------------------------------------------------------
        if k_values and silhouette_scores:
            # Make sure both arrays have equal length
            valid_length = min(
                len(k_values),
                len(silhouette_scores)
            )

            k_values = k_values[:valid_length]
            silhouette_scores = silhouette_scores[:valid_length]

            scores_arr = np.asarray(
                silhouette_scores,
                dtype=float
            )

            best_index = int(
                np.argmax(scores_arr)
            )

            best_silhouette_k = int(
                k_values[best_index]
            )

            max_silhouette_score = float(
                scores_arr[best_index]
            )

        else:
            # Fallback to values saved in clustering_metrics.json
            best_silhouette_k = int(
                clst_m.get(
                    "best_silhouette_k",
                    10
                )
            )

            max_silhouette_score = float(
                clst_m.get(
                    "max_silhouette_score",
                    clst_m.get(
                        "best_silhouette_score",
                        0.0
                    )
                )
            )

        # ------------------------------------------------------------------
        # Display clustering metrics
        # ------------------------------------------------------------------
        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Selected K (Elbow Method)",
            sel_k
        )

        c2.metric(
            "Best Silhouette K",
            best_silhouette_k
        )

        c3.metric(
            "Max Silhouette Score",
            f"{max_silhouette_score:.4f}"
        )

        c4.metric(
            f"KMeans Inertia (K={sel_k})",
            f"{clst_m.get('inertia', 0.0):.1f}"
        )

    else:
        st.warning(
            "Clustering metrics not found. "
            "Please run `python train.py` first."
        )

    # ==========================================================================
    # 1. K-OPTIMIZATION CURVES
    # ==========================================================================
    st.markdown(
        "### 1. K-Optimization Curves (K=2 to 10)"
    )

    c_img1, c_img2 = st.columns(2)

    # Elbow curve
    with c_img1:
        elbow_path = FIGURES_DIR / "elbow_curve.png"

        if elbow_path.exists():
            st.image(
                str(elbow_path),
                caption="KMeans Elbow Method (Inertia vs K)",
                use_container_width=True
            )
        else:
            st.warning(
                "Elbow curve not found. Run `python train.py`."
            )

    # Silhouette curve
    with c_img2:
        sil_path = FIGURES_DIR / "silhouette_scores.png"

        if sil_path.exists():
            st.image(
                str(sil_path),
                caption="Silhouette Score Curve vs K",
                use_container_width=True
            )
        else:
            st.warning(
                "Silhouette curve not found. Run `python train.py`."
            )

    # ==========================================================================
    # 2. PCA VISUALIZATION
    # ==========================================================================
    st.markdown(
        "### 2. 2D PCA Cluster Scatter Plot"
    )

    st.caption(
        "PCA (n_components=2) is used strictly for 2D visualization. "
        "Clustering operates on the raw TF-IDF matrix."
    )

    pca_path = FIGURES_DIR / "job_clusters_pca.png"

    if pca_path.exists():
        st.image(
            str(pca_path),
            caption="2D PCA Visualization of Job Clusters",
            use_container_width=True
        )
    else:
        st.warning(
            "PCA cluster visualization not found. "
            "Run `python train.py`."
        )

    # ==========================================================================
    # 3. NMF TOPIC MODELING
    # ==========================================================================
    st.markdown(
        "### 3. NMF Topic Modeling Keywords"
    )

    if (
        not jobs_df.empty
        and "job_vectorizer" in models
        and "job_vectors" in models
    ):
        topics = extract_nmf_topics(
            models["job_vectors"],
            models["job_vectorizer"],
            n_topics=5,
            top_words=10
        )

        if topics:
            for t_idx, words in topics.items():
                st.markdown(
                    f"**Topic {t_idx + 1}:** "
                    f"`{', '.join(words)}`"
                )
        else:
            st.info(
                "No NMF topics could be generated."
            )
    else:
        st.warning(
            "Job vectorizer or job vectors are unavailable. "
            "Run `python train.py` first."
        )


# ==============================================================================
# PAGE 7: MODEL ANALYTICS
# ==============================================================================
elif page == "📈 Model Analytics":
    st.subheader("Model Benchmark & Actual Calculated Evaluation Metrics")

    cls_m = metrics.get("classifier", {})
    if cls_m:
        st.markdown("### Supervised Classifier Metrics")
        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Selected Model", cls_m.get("model_name", "N/A"))
        a2.metric("Accuracy", f"{cls_m.get('accuracy', 0.0)*100:.1f}%")
        a3.metric("Weighted Precision", f"{cls_m.get('precision_weighted', 0.0)*100:.1f}%")
        a4.metric("Weighted F1-Score", f"{cls_m.get('f1_weighted', 0.0)*100:.1f}%")

        cm_path = FIGURES_DIR / "confusion_matrix.png"
        if cm_path.exists():
            st.markdown("#### Classifier Confusion Matrix")
            st.image(str(cm_path), caption="Resume Classifier Confusion Matrix Heatmap", use_container_width=True)

        if "classification_report" in cls_m:
            with st.expander("View Full Classification Report JSON", expanded=False):
                st.json(cls_m["classification_report"])
    else:
        st.info("Metrics not found. Run `python train.py` to calculate.")


# ==============================================================================
# PAGE 8: ABOUT
# ==============================================================================
elif page == "ℹ️ About":
    st.subheader("About SmartHire")

    st.markdown("""
    **SmartHire** is a classical machine learning application built for resume classification, job matching, skill-gap detection, and job family clustering.

    ### ⚙️ Classical ML Stack
    - **Classifier:** Logistic Regression vs. LinearSVC on TF-IDF n-grams.
    - **Recommender:** Vector space TF-IDF with Cosine Similarity.
    - **Fit Score:** Transparent multi-factor formula ($0.50 \times \text{TextSim} + 0.30 \times \text{SkillOverlap} + 0.20 \times \text{ExpMatch}$).
    - **Clustering:** KMeans with Elbow & Silhouette metrics.
    - **PCA Plot:** 2D Principal Component Analysis visualization.
    - **Topic Modeling:** Non-Negative Matrix Factorization (NMF).

    ### 🛡️ Academic Integrity Notice
    This project uses classical machine learning techniques including TF-IDF, Logistic Regression/Linear SVM, cosine similarity, K-Means, PCA and NMF. No generative AI or LLM is used.
    """)
