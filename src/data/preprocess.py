"""
Text Preprocessing Module for SmartHire.
Cleans raw text while preserving key programming/technical tokens.
"""

import re
import string


PROTECTED_TOKENS_MAP = {
    r"(?i)(?:^|[\s,.\/;:\(\)\[\]\-])c\+\+(?:$|[\s,.\/;:\(\)\[\]\-])": " cplusplus ",
    r"(?i)(?:^|[\s,.\/;:\(\)\[\]\-])c#(?:$|[\s,.\/;:\(\)\[\]\-])": " csharp ",
    r"(?i)(?:^|[\s,.\/;:\(\)\[\]\-])\.net(?:$|[\s,.\/;:\(\)\[\]\-])": " dotnet ",
    r"(?i)(?:^|[\s,.\/;:\(\)\[\]\-])node\.js(?:$|[\s,.\/;:\(\)\[\]\-])": " nodejs ",
    r"(?i)(?:^|[\s,.\/;:\(\)\[\]\-])react\.js(?:$|[\s,.\/;:\(\)\[\]\-])": " reactjs ",
    r"(?i)(?:^|[\s,.\/;:\(\)\[\]\-])vue\.js(?:$|[\s,.\/;:\(\)\[\]\-])": " vuejs ",
    r"(?i)(?:^|[\s,.\/;:\(\)\[\]\-])express\.js(?:$|[\s,.\/;:\(\)\[\]\-])": " expressjs ",
    r"(?i)(?:^|[\s,.\/;:\(\)\[\]\-])angular\.js(?:$|[\s,.\/;:\(\)\[\]\-])": " angularjs ",
    r"(?i)(?:^|[\s,.\/;:\(\)\[\]\-])pl/sql(?:$|[\s,.\/;:\(\)\[\]\-])": " plsql ",
    r"(?i)(?:^|[\s,.\/;:\(\)\[\]\-])rest api(?:$|[\s,.\/;:\(\)\[\]\-])": " restapi ",
}

REVERSE_PROTECTED_MAP = {
    "cplusplus": "c++",
    "csharp": "c#",
    "dotnet": ".net",
    "nodejs": "node.js",
    "reactjs": "react.js",
    "vuejs": "vue.js",
    "expressjs": "express.js",
    "angularjs": "angular.js",
    "plsql": "pl/sql",
    "restapi": "rest api",
}


def clean_text(text: str, preserve_tech_terms: bool = True) -> str:
    """
    Cleans input resume or job description text.

    Operations:
    1. Lowercase text
    2. Remove URLs, email addresses, phone numbers
    3. Protect technical terms (e.g., C++, C#, .NET, Node.js)
    4. Remove non-alphanumeric punctuation (except protected tokens)
    5. Remove excessive whitespace

    Args:
        text (str): Input text
        preserve_tech_terms (bool): Whether to protect technical terms

    Returns:
        str: Cleaned text
    """
    if not text or not isinstance(text, str):
        return ""

    text = text.lower()

    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # Remove Email addresses
    text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", " ", text)

    # Remove Phone Numbers / Long digit sequences
    text = re.sub(r"\b\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b", " ", text)

    if preserve_tech_terms:
        # Protect specific tech tokens before general punctuation stripping
        for pattern, replacement in PROTECTED_TOKENS_MAP.items():
            text = re.sub(pattern, f" {replacement} ", text, flags=re.IGNORECASE)

    # Remove non-alphanumeric characters except space
    # Keep alphanumeric characters and whitespace
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)

    # Remove excess whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text
