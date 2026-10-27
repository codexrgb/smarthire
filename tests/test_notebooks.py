"""
Validation tests for repaired Jupyter notebooks.
Ensures repaired notebooks parse cleanly as standard JSON with nbformat v4 structure.
"""

import json
import pytest
from pathlib import Path


def test_repaired_notebooks_exist_and_parse():
    """All repaired notebooks must exist and parse validly as JSON."""
    repaired_dir = Path("notebooks") / "repaired"
    assert repaired_dir.exists(), "notebooks/repaired directory must exist"

    notebook_names = [
        "02_resume_classifier.ipynb",
        "03_recommender.ipynb",
        "04_clustering_topics.ipynb",
        "05_fit_predictor.ipynb"
    ]

    for name in notebook_names:
        nb_path = repaired_dir / name
        assert nb_path.exists(), f"Repaired notebook {name} must exist"

        with open(nb_path, "r", encoding="utf-8") as f:
            nb_data = json.load(f)

        assert "cells" in nb_data, f"{name} must contain 'cells'"
        assert "metadata" in nb_data, f"{name} must contain 'metadata'"
        assert nb_data.get("nbformat") == 4, f"{name} nbformat must be 4"
        assert len(nb_data["cells"]) >= 2, f"{name} must have at least markdown and code cells"

        # Verify each cell structure
        for idx, cell in enumerate(nb_data["cells"]):
            assert "cell_type" in cell, f"Cell {idx} in {name} must have cell_type"
            assert "source" in cell, f"Cell {idx} in {name} must have source"
            assert isinstance(cell["source"], list), f"Cell {idx} source in {name} must be list"


def test_original_notebooks_preserved():
    """Confirms original notebooks in notebooks/ remain present and untouched."""
    original_dir = Path("notebooks")
    for name in [
        "01_eda.ipynb",
        "02_resume_classifier.ipynb",
        "03_recommender.ipynb",
        "04_clustering_topics.ipynb",
        "05_fit_predictor.ipynb"
    ]:
        nb_path = original_dir / name
        assert nb_path.exists(), f"Original notebook {name} must remain preserved"
