import re


def chunk_text(text: str, chunk_size: int, overlap: int = 50) -> list:
    paragraphs = [p for p in text.split("\n\n") if p.strip()]

    chunks = []
    chunk = ""

    for paragraph in paragraphs:
        if len(paragraph) <= chunk_size:
            chunks.append(paragraph)
        else:
            sentences = [s for s in re.split(r"(?<=[？。！；．])", paragraph) if s.strip()]
            for sentence in sentences:
                if len(chunk) + len(sentence) >= chunk_size:
                    if chunk:
                        chunks.append(chunk)
                    chunk = chunk[-overlap:]
                chunk += sentence
            if chunk:
                chunks.append(chunk)
    return chunks
