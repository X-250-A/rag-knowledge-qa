"""手写 parser"""
from pathlib import Path

import fitz
from docx import Document

from backend.app.exceptions import BadRequestError


def parse_file(file_path: str):
    suffix = Path(file_path).suffix.lower()
    if suffix == ".docx":
        return parse_docx(file_path)
    elif suffix == ".pdf":
        return parse_pdf(file_path)
    elif suffix == ".md":
        return parse_md(file_path)
    else:
        raise BadRequestError("未支持的文件类型")

def parse_pdf(file_path: str) -> str:
    # 打开文件
    pdf = fitz.open(file_path)
    # 提取文本
    text = []
    for page in pdf:
        text.append(page.get_text())
    # 关闭文件
    pdf.close()
    return "\n\n".join(text)

def parse_docx(file_path: str) -> str:
    docx = Document(file_path)
    texts = []
    for para in docx.paragraphs:
        texts.append(para.text)
    return "\n\n".join(texts)

def parse_md(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()





