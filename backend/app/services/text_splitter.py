import re
import jieba


def split_text_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    if not text or not text.strip():
        return []

    text = re.sub(r'\n{3,}', '\n\n', text.strip())

    paragraphs = re.split(r'\n\n+', text)
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += ("\n\n" + para if current_chunk else para)
        else:
            if current_chunk:
                chunks.append(current_chunk)
            if len(para) > chunk_size:
                sentences = re.split(r'[。！？；\n]', para)
                sub_chunk = ""
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue
                    if len(sub_chunk) + len(sent) <= chunk_size:
                        sub_chunk += ("。" + sent if sub_chunk else sent)
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk)
                        sub_chunk = sent
                if sub_chunk:
                    current_chunk = sub_chunk
                else:
                    current_chunk = ""
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    if overlap > 0 and len(chunks) > 1:
        overlapped_chunks = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i-1][-overlap:] if len(chunks[i-1]) > overlap else chunks[i-1]
            overlapped_chunks.append(prev_tail + chunks[i])
        chunks = overlapped_chunks

    return chunks


def extract_keywords(text: str, topk: int = 10) -> list[str]:
    words = jieba.lcut(text)
    stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
    keywords = [w for w in words if len(w) >= 2 and w not in stopwords]
    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)
    return unique_keywords[:topk]


def chunk_document(text: str, chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    chunks = split_text_into_chunks(text, chunk_size, overlap)
    result = []
    for i, chunk in enumerate(chunks):
        keywords = extract_keywords(chunk)
        result.append({
            "content": chunk,
            "keywords": ",".join(keywords),
            "index": i
        })
    return result
