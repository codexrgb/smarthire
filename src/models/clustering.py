"""
Job Clustering, PCA 2D Visualization, and NMF Topic Modeling Module for SmartHire.

Operates on classical TF-IDF matrices using:
- KMeans clustering
- PCA for 2D visualization
- NMF topic modeling

Provides:
- K evaluation from K=2 to K=10
- Inertia / Elbow Method
- Silhouette Score analysis
- Best Silhouette K
- Maximum Silhouette Score
- Elbow-selected K
- 2D PCA visualization
- NMF topic extraction
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List, Tuple, Any

from sklearn.cluster import KMeans
from sklearn.decomposition import PCA, NMF
from sklearn.metrics import silhouette_score
from sklearn.feature_extraction.text import TfidfVectorizer

from src.config import FIGURES_DIR, DEFAULT_N_CLUSTERS


def find_optimal_k(
    X: Any,
    k_range: range = range(2, 11),
    save_plots: bool = True
) -> Dict[str, Any]:
    """
    Evaluate KMeans clustering for K=2..10.

    Calculates:
        - KMeans inertia for every K
        - Silhouette score for every K
        - Best Silhouette K
        - Maximum Silhouette Score

    The selected K for the actual clustering model remains
    DEFAULT_N_CLUSTERS and is reported separately from the
    best silhouette K.

    Returns:
        Dictionary containing all clustering evaluation results.
    """

    # ---------------------------------------------------------
    # Initialize
    # ---------------------------------------------------------

    requested_k_values = list(k_range)

    evaluated_k_values = []
    inertias = []
    silhouette_scores_list = []
    k_details = []

    n_samples = X.shape[0]

    # ---------------------------------------------------------
    # Evaluate KMeans for each K
    # ---------------------------------------------------------

    for k in requested_k_values:

        # K cannot be equal to or greater than number of samples
        if k >= n_samples:
            break

        kmeans = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=10
        )

        labels = kmeans.fit_predict(X)

        inertia = float(kmeans.inertia_)

        # Calculate silhouette score
        if len(np.unique(labels)) > 1:
            sil = float(
                silhouette_score(
                    X,
                    labels
                )
            )
        else:
            sil = 0.0

        evaluated_k_values.append(int(k))
        inertias.append(inertia)
        silhouette_scores_list.append(sil)

        k_details.append(
            {
                "k": int(k),
                "inertia": round(inertia, 2),
                "silhouette_score": round(sil, 4)
            }
        )

    # ---------------------------------------------------------
    # Convert silhouette scores to authoritative NumPy array
    # ---------------------------------------------------------

    scores_arr = np.asarray(
        silhouette_scores_list,
        dtype=float
    )

    evaluated_k_array = np.asarray(
        evaluated_k_values,
        dtype=int
    )

    # ---------------------------------------------------------
    # Find maximum silhouette score
    # ---------------------------------------------------------

    if scores_arr.size > 0:

        best_idx = int(
            np.argmax(scores_arr)
        )

        best_silhouette_k = int(
            evaluated_k_array[best_idx]
        )

        max_silhouette_score = float(
            scores_arr[best_idx]
        )

    else:

        best_idx = None
        best_silhouette_k = None
        max_silhouette_score = 0.0

    # ---------------------------------------------------------
    # Debug information
    # ---------------------------------------------------------

    print(
        "DEBUG evaluated K values:",
        evaluated_k_values
    )

    print(
        "DEBUG silhouette scores:",
        silhouette_scores_list
    )

    print(
        "DEBUG best silhouette K:",
        best_silhouette_k
    )

    print(
        "DEBUG max silhouette score:",
        max_silhouette_score
    )

    # ---------------------------------------------------------
    # Generate plots
    # ---------------------------------------------------------

    if save_plots:

        FIGURES_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        # =====================================================
        # 1. Elbow Curve
        # =====================================================

        plt.figure(
            figsize=(8, 4.5)
        )

        plt.plot(
            evaluated_k_values,
            inertias,
            marker="o",
            color="#1e3a8a",
            linewidth=2
        )

        plt.title(
            "K-Means Elbow Method (Inertia vs. Clusters K)",
            fontsize=12,
            fontweight="bold"
        )

        plt.xlabel(
            "Number of Clusters (K)"
        )

        plt.ylabel(
            "Inertia (Sum of Squared Distances)"
        )

        plt.grid(
            True,
            linestyle="--",
            alpha=0.5
        )

        plt.tight_layout()

        plt.savefig(
            FIGURES_DIR / "elbow_curve.png",
            dpi=300
        )

        plt.close()

        # =====================================================
        # 2. Silhouette Score Curve
        # =====================================================

        plt.figure(
            figsize=(8, 4.5)
        )

        plt.plot(
            evaluated_k_values,
            silhouette_scores_list,
            marker="s",
            color="#dc2626",
            linewidth=2
        )

        plt.title(
            "Silhouette Score vs. Clusters K",
            fontsize=12,
            fontweight="bold"
        )

        plt.xlabel(
            "Number of Clusters (K)"
        )

        plt.ylabel(
            "Silhouette Score"
        )

        plt.grid(
            True,
            linestyle="--",
            alpha=0.5
        )

        plt.tight_layout()

        plt.savefig(
            FIGURES_DIR / "silhouette_scores.png",
            dpi=300
        )

        plt.close()

    # ---------------------------------------------------------
    # Build final result dictionary
    # ---------------------------------------------------------

    result_dict = {
        "k_values": evaluated_k_values,

        "inertias": inertias,

        "silhouette_scores": silhouette_scores_list,

        "k_details": k_details,

        # Maximum silhouette information
        "best_silhouette_k": best_silhouette_k,

        "max_silhouette_score": round(
            max_silhouette_score,
            4
        ),

        # Backward-compatible key
        "best_silhouette_score": round(
            max_silhouette_score,
            4
        ),

        # Actual K selected for clustering
        "selected_elbow_k": DEFAULT_N_CLUSTERS,

        "explanation": (
            "Elbow Method and Silhouette Score may suggest "
            "different K values. The selected K is based on "
            "the declared selection criterion."
        )
    }

    # ---------------------------------------------------------
    # Final debug output
    # ---------------------------------------------------------

    print(
        "DEBUG RESULT KEYS:",
        list(result_dict.keys())
    )

    print(
        "DEBUG RESULT SILHOUETTE SCORES:",
        result_dict["silhouette_scores"]
    )

    print(
        "DEBUG RESULT BEST K:",
        result_dict["best_silhouette_k"]
    )

    print(
        "DEBUG RESULT MAX SCORE:",
        result_dict["max_silhouette_score"]
    )

    # ---------------------------------------------------------
    # Return
    # ---------------------------------------------------------

    return result_dict


def cluster_jobs(
    X: Any,
    n_clusters: int = DEFAULT_N_CLUSTERS
) -> Tuple[KMeans, np.ndarray, float, float]:
    """
    Cluster job TF-IDF matrix X using KMeans.

    Returns:
        Tuple containing:
            - KMeans model
            - cluster labels
            - inertia
            - silhouette score
    """

    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10
    )

    labels = kmeans.fit_predict(X)

    if len(np.unique(labels)) > 1:
        sil = float(
            silhouette_score(
                X,
                labels
            )
        )
    else:
        sil = 0.0

    inertia = float(
        kmeans.inertia_
    )

    return (
        kmeans,
        labels,
        inertia,
        sil
    )


def create_cluster_visualization(
    X: Any,
    cluster_labels: np.ndarray,
    save_figure: bool = True
) -> np.ndarray:
    """
    Reduce TF-IDF feature matrix X to 2D using PCA
    strictly for visualization.

    PCA is NOT used as the primary clustering representation.

    Saves:
        reports/figures/job_clusters_pca.png

    Returns:
        2D PCA coordinates.
    """

    pca = PCA(
        n_components=2,
        random_state=42
    )

    # Convert sparse TF-IDF matrix to dense matrix if required
    X_dense = (
        X.toarray()
        if hasattr(X, "toarray")
        else X
    )

    pca_coords = pca.fit_transform(
        X_dense
    )

    if save_figure:

        FIGURES_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        plt.figure(
            figsize=(9, 6)
        )

        hue_labels = [
            f"Cluster {c}"
            for c in cluster_labels
        ]

        sns.scatterplot(
            x=pca_coords[:, 0],
            y=pca_coords[:, 1],
            hue=hue_labels,
            palette="tab10",
            style=hue_labels,
            alpha=0.85,
            s=60
        )

        plt.title(
            "2D PCA Projection of Job Clusters",
            fontsize=12,
            fontweight="bold"
        )

        plt.xlabel(
            "PCA Component 1"
        )

        plt.ylabel(
            "PCA Component 2"
        )

        plt.legend(
            bbox_to_anchor=(1.05, 1),
            loc="upper left"
        )

        plt.tight_layout()

        plt.savefig(
            FIGURES_DIR / "job_clusters_pca.png",
            dpi=300
        )

        plt.close()

    return pca_coords


def extract_nmf_topics(
    tfidf_matrix: Any,
    vectorizer: TfidfVectorizer,
    n_topics: int = 5,
    top_words: int = 10
) -> Dict[int, List[str]]:
    """
    Extract top keywords per topic using NMF.

    Does not manually invent topic names.

    Returns:
        Dictionary:
            topic_index -> list of top words
    """

    nmf = NMF(
        n_components=n_topics,
        random_state=42,
        init="nndsvda",
        max_iter=500
    )

    nmf.fit(
        tfidf_matrix
    )

    feature_names = np.array(
        vectorizer.get_feature_names_out()
    )

    topics = {}

    for topic_idx, topic in enumerate(
        nmf.components_
    ):

        top_indices = topic.argsort()[
            :-top_words - 1:-1
        ]

        topics[topic_idx] = (
            feature_names[top_indices]
            .tolist()
        )

    return topics
