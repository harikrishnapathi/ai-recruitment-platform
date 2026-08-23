from pathlib import Path

import pymupdf
from docx import Document


def extract_text_from_pdf(file_path: str) -> str:
    document = pymupdf.open(file_path)
    try:
        pages = [page.get_text() for page in document if page.get_text()]
        return "\n".join(pages).strip()
    finally:
        document.close()


def extract_text_from_docx(file_path: str) -> str:
    document = Document(file_path)
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(paragraphs).strip()


def extract_resume_text(file_path: str) -> str:
    extension = Path(file_path).suffix.lower()
    if extension == ".pdf":
        return extract_text_from_pdf(file_path)
    if extension == ".docx":
        return extract_text_from_docx(file_path)
    raise ValueError(f"Unsupported resume format: {extension}")
