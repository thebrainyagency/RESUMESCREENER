import os
from PyPDF2 import PdfReader
import docx

def _parse_pdf(path: str) -> str:
    try:
        reader = PdfReader(path)
        return " ".join((page.extract_text() or "") for page in reader.pages).strip()
    except Exception as e:
        return f"ERROR_PDF_PARSE: {e}"

def _parse_docx(path: str) -> str:
    try:
        d = docx.Document(path)
        return " ".join(p.text for p in d.paragraphs).strip()
    except Exception as e:
        return f"ERROR_DOCX_PARSE: {e}"

def _parse_txt(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        return f"ERROR_TXT_PARSE: {e}"

def parse_resumes(folder: str):
    """
    Return list of {"filename","path","text"} for .pdf/.docx/.txt files.
    """
    resumes = []
    for file in sorted(os.listdir(folder)):
        path = os.path.join(folder, file)
        if not os.path.isfile(path):
            continue
        lower = file.lower()
        if not (lower.endswith(".pdf") or lower.endswith(".docx") or lower.endswith(".txt")):
            continue

        if lower.endswith(".pdf"):
            text = _parse_pdf(path)
        elif lower.endswith(".docx"):
            text = _parse_docx(path)
        else:
            text = _parse_txt(path)

        if not text:
            text = ""

        resumes.append({
            "filename": file,
            "path": path,
            "text": text
        })
    return resumes
