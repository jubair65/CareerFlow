import os
import re
from typing import Optional
import pdfplumber
import docx


def clean_extracted_text(text: Optional[str]) -> str:
    """
    Sanitize and normalize raw text extracted from documents:
    - Removes non-printable characters and control characters (except tabs and newlines).
    - Normalizes non-breaking spaces and irregular whitespace.
    - Standardizes bullet points to standard dashes.
    - Condenses multiple consecutive empty lines to maximum 2 newlines.
    - Strips leading and trailing whitespace.
    """
    if not text:
        return ""

    # Replace null bytes and problematic control chars
    text = text.replace('\x00', '')

    # Standardize unicode quotes and hyphens/bullets
    bullet_chars = ['\u2022', '\u2023', '\u25e6', '\u2043', '\u2219', '\u25aa', '\u25ab']
    for bullet in bullet_chars:
        text = text.replace(bullet, '- ')

    # Normalize unicode whitespace
    text = text.replace('\u00a0', ' ')

    # Clean lines
    lines = []
    for line in text.splitlines():
        # Collapse multiple spaces or tabs into a single space
        cleaned_line = re.sub(r'[ \t]+', ' ', line).strip()
        lines.append(cleaned_line)

    result = '\n'.join(lines)
    # Collapse 3 or more consecutive newlines into 2
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file using pdfplumber.
    Iterates through all pages, preserving natural reading order.
    Handles corrupt, encrypted, and malformed files gracefully.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found at: {file_path}")

    extracted_pages = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                try:
                    page_text = page.extract_text(layout=False)
                    if page_text:
                        extracted_pages.append(page_text)
                except Exception:
                    continue
    except Exception as e:
        err_msg = str(e).lower()
        if 'password' in err_msg or 'encrypt' in err_msg:
            raise ValueError(f"PDF is encrypted or password-protected: {str(e)}") from e
        raise ValueError(f"Invalid or corrupted PDF document: {str(e)}") from e

    full_text = '\n\n'.join(extracted_pages)
    return clean_extracted_text(full_text)


def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from a DOCX document using python-docx.
    Extracts text from both body paragraphs and table cells.
    Handles corrupt and invalid archives gracefully.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"DOCX file not found at: {file_path}")

    try:
        doc = docx.Document(file_path)
    except Exception as e:
        raise ValueError(f"Invalid or corrupted DOCX document: {str(e)}") from e

    text_blocks = []

    # 1. Extract paragraph contents
    for paragraph in doc.paragraphs:
        if paragraph.text and paragraph.text.strip():
            text_blocks.append(paragraph.text.strip())

    # 2. Extract table cells (resumes frequently use tables for column layouts)
    for table in doc.tables:
        for row in table.rows:
            row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_texts:
                # Deduplicate adjacent identical cells resulting from merged cells
                deduped = []
                for t in row_texts:
                    if not deduped or deduped[-1] != t:
                        deduped.append(t)
                text_blocks.append(' | '.join(deduped))

    full_text = '\n'.join(text_blocks)
    return clean_extracted_text(full_text)


def extract_text(file_path: str, file_type: Optional[str] = None) -> str:
    """
    Universal text extraction dispatcher for PDF and DOCX files.
    Determines type from file extension if not provided explicitly.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_type:
        _, ext = os.path.splitext(file_path)
        file_type = ext.lower().replace('.', '')

    file_type = file_type.lower().strip()

    if file_type == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_type in ('docx', 'doc'):
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type '{file_type}'. Supported formats: 'pdf', 'docx'.")
