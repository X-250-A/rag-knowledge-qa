def chunk_text(text: str, chunk_size: int, overlap: int = 50) -> list:
    paragraphs = [p for p in text.split("\n\n") if p.strip()]

    chunks = []
    chunk = ""

    for paragraph in paragraphs:
        if len(paragraph) <= chunk_size:
            chunks.append(paragraph)
        else:
            sentences = paragraph.split("。")
            sentences = [s + "。" for s in sentences if s.strip()]
            for sentence in sentences:
                if len(chunk) + len(sentence) >= chunk_size:
                    chunks.append(chunk)
                    chunk = chunk[-overlap:]
                chunk += sentence
            if chunk:
                chunks.append(chunk)
    return chunks
