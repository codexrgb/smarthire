"""
Resume File Parser Module for SmartHire.
Extracts raw text safely from PDF, DOCX, and TXT documents.
"""

import io
from pathlib import Path
from typing import Union, Tuple

from pypdf import PdfReader
import docx


def extract_text_from_pdf(file_bytes_or_path: Union[bytes, str, Path, io.BytesIO]) -> str:
    """
    Extracts plain text from a PDF file buffer or path using pypdf.
    """
    try:
        if isinstance(file_bytes_or_path, bytes):
            stream = io.BytesIO(file_bytes_or_path)
        elif isinstance(file_bytes_or_path, (str, Path)):
            stream = open(file_bytes_or_path, "rb")
        else:
            stream = file_bytes_or_path

        reader = PdfReader(stream)
        text_pages = []
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text_pages.append(extracted)

        return "\n".join(text_pages).strip()
    except Exception as e:
        raise ValueError(f"Failed to read PDF file: {str(e)}")


def extract_text_from_docx(file_bytes_or_path: Union[bytes, str, Path, io.BytesIO]) -> str:
    """
    Extracts plain text from a DOCX file buffer or path using python-docx.
    """
    try:
        if isinstance(file_bytes_or_path, bytes):
            stream = io.BytesIO(file_bytes_or_path)
        elif isinstance(file_bytes_or_path, (str, Path)):
            stream = file_bytes_or_path
        else:
            stream = file_bytes_or_path

        doc = docx.Document(stream)
        text_paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(text_paragraphs).strip()
    except Exception as e:
        raise ValueError(f"Failed to read DOCX file: {str(e)}")


def extract_text_from_txt(file_bytes_or_path: Union[bytes, str, Path, io.BytesIO]) -> str:
    """
    Extracts plain text from a TXT file buffer or path handling various encodings.
    """
    try:
        if isinstance(file_bytes_or_path, bytes):
            # Try UTF-8 first, fallback to latin-1
            try:
                return file_bytes_or_path.decode("utf-8").strip()
            except UnicodeDecodeError:
                return file_bytes_or_path.decode("latin-1").strip()
        elif isinstance(file_bytes_or_path, (str, Path)):
            with open(file_bytes_or_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()
        elif hasattr(file_bytes_or_path, "read"):
            content = file_bytes_or_path.read()
            if isinstance(content, bytes):
                return content.decode("utf-8", errors="ignore").strip()
            return str(content).strip()
        return str(file_bytes_or_path).strip()
    except Exception as e:
        raise ValueError(f"Failed to read TXT file: {str(e)}")


def extract_resume_text(uploaded_file, filename: str = None) -> Tuple[str, str]:
    """
    Main entry point for extracting text from uploaded resume files.

    Args:
        uploaded_file: Streamlit UploadedFile object, file path, or bytes
        filename (str, optional): Name of the file for extension checking

    Returns:
        Tuple[str, str]: (extracted_text, status_message)
    """
    if uploaded_file is None:
        return ("", "No file uploaded.")

    # Determine filename
    if not filename and hasattr(uploaded_file, "name"):
        filename = uploaded_file.name
    elif not filename and isinstance(uploaded_file, (str, Path)):
        filename = str(uploaded_file)

    if not filename:
        filename = "document.txt"

    ext = Path(filename).suffix.lower()

    # Read bytes buffer if Streamlit file
    if hasattr(uploaded_file, "getvalue"):
        content_bytes = uploaded_file.getvalue()
    elif hasattr(uploaded_file, "read"):
        content_bytes = uploaded_file.read()
    elif isinstance(uploaded_file, (str, Path)):
        with open(uploaded_file, "rb") as f:
            content_bytes = f.read()
    elif isinstance(uploaded_file, bytes):
        content_bytes = uploaded_file
    else:
        return ("", f"Unsupported file type or buffer: {type(uploaded_file)}")

    if not content_bytes or len(content_bytes) == 0:
        return ("", "Error: Uploaded file is empty (0 bytes).")

    try:
        if ext == ".pdf":
            extracted = extract_text_from_pdf(content_bytes)
        elif ext in [".docx", ".doc"]:
            extracted = extract_text_from_docx(content_bytes)
        elif ext == ".txt":
            extracted = extract_text_from_txt(content_bytes)
        else:
            return ("", f"Unsupported file extension '{ext}'. Supported formats: .pdf, .docx, .txt")

        if not extracted or not extracted.strip():
            return ("", "Warning: File uploaded successfully, but no readable text could be extracted.")

        return (extracted.strip(), "Success")

    except ValueError as ve:
        return ("", f"Parsing Error: {str(ve)}")
    except Exception as e:
        return ("", f"Unexpected error reading file: {str(e)}")
