"""
Application Runner Script for SmartHire.
Launches the Streamlit Web Application.
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    app_path = Path(__file__).resolve().parent / "app" / "streamlit_app.py"
    if not app_path.exists():
        print(f"Error: Could not find application entry file at {app_path}")
        sys.exit(1)

    print("==================================================")
    print("      LAUNCHING SMART HIRE STREAMLIT APP          ")
    print("==================================================")
    print(f" Target File: {app_path.name}")
    print(" URL: http://localhost:8501")
    print(" Press Ctrl+C in terminal to stop the server.")
    print("==================================================\n")

    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nSmartHire App stopped by user.")
    except Exception as e:
        print(f"Error launching Streamlit app: {e}")

if __name__ == "__main__":
    main()
