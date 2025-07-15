try:
    from sentence_transformers.cross_encoder import CrossEncoder
except ImportError:
    print("Sentence Transformers is not installed. Please install it with 'pip install sentence-transformers'")
    CrossEncoder = None

class CrossEncoderReranker:
    def __init__(self, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"):
        if CrossEncoder is not None:
            self.model = CrossEncoder(model_name)
        else:
            self.model = None

    def rerank(self, query: str, candidates: list[str]):
        if self.model is None:
            return candidates
        
        pairs = [(query, candidate) for candidate in candidates]
        scores = self.model.predict(pairs)
        
        ranked_results = sorted(
            zip(candidates, scores), 
            key=lambda x: x[1], 
            reverse=True
        )
        return [res[0] for res in ranked_results] 