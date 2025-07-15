from nltk.tokenize import sent_tokenize

def chunk_text_by_sentence(text: str, sentences_per_chunk: int = 5) -> list[str]:
    """
    Chunks a given text into smaller pieces, with each chunk containing a specified number of sentences.
    """
    sentences = sent_tokenize(text)
    chunks = []
    for i in range(0, len(sentences), sentences_per_chunk):
        chunk = " ".join(sentences[i:i + sentences_per_chunk])
        chunks.append(chunk)
    return chunks 