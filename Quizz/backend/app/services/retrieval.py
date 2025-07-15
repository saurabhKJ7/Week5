try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Sentence Transformers is not installed. Please install it with 'pip install sentence-transformers'")
    SentenceTransformer = None

try:
    import faiss
except ImportError:
    print("FAISS is not installed. Please install it with 'pip install faiss-cpu'")
    faiss = None

try:
    import numpy as np
except ImportError:
    print("NumPy is not installed. Please install it with 'pip install numpy'")
    np = None

from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
import os
import shutil

class DenseRetriever:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        if SentenceTransformer is not None:
            self.encoder = SentenceTransformer(model_name)
        else:
            self.encoder = None
        self.index = None
        self.documents = []

    def encode_documents(self, documents: list[str]):
        if self.encoder is None or faiss is None or np is None:
            return
        
        self.documents = documents
        embeddings = self.encoder.encode(documents)
        embeddings = np.array(embeddings, dtype=np.float32)
        
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)

    def search(self, query: str, k: int = 10):
        if self.index is None or self.encoder is None or np is None:
            return []
        
        query_embedding = self.encoder.encode([query])
        query_embedding = np.array(query_embedding, dtype=np.float32)

        scores, indices = self.index.search(query_embedding, k)
        
        results = []
        for i, score in zip(indices[0], scores[0]):
            if i != -1:
                results.append({"document": self.documents[i], "score": score})
        return results 

class SparseRetriever:
    def __init__(self, index_dir="whoosh_index"):
        self.index_dir = index_dir
        self.schema = Schema(id=ID(stored=True), content=TEXT)
        self.ix = None
        if not os.path.exists(self.index_dir):
            os.mkdir(self.index_dir)
            self.ix = create_in(self.index_dir, self.schema)
        else:
            self.ix = open_dir(self.index_dir)

    def add_documents(self, documents: dict[int, str]):
        writer = self.ix.writer()
        for doc_id, content in documents.items():
            writer.add_document(id=str(doc_id), content=content)
        writer.commit()

    def search(self, query_str: str, k: int = 10):
        results = []
        with self.ix.searcher() as searcher:
            query = QueryParser("content", self.ix.schema).parse(query_str)
            hits = searcher.search(query, limit=k)
            for hit in hits:
                results.append({"document": hit['id'], "score": hit.score})
        return results

    def cleanup(self):
        """Deletes the index directory."""
        if os.path.exists(self.index_dir):
            shutil.rmtree(self.index_dir) 

class HybridRetriever:
    def __init__(self, dense_retriever: DenseRetriever, sparse_retriever: SparseRetriever):
        self.dense_retriever = dense_retriever
        self.sparse_retriever = sparse_retriever

    def search(self, query: str, k: int = 10, dense_weight=0.5, sparse_weight=0.5):
        dense_results = self.dense_retriever.search(query, k * 2)
        sparse_results = self.sparse_retriever.search(query, k * 2)

        # Simple weighted fusion for now. RRF is more complex to implement.
        combined_results = {}

        for res in dense_results:
            doc_id = res["id"]
            if doc_id not in combined_results:
                combined_results[doc_id] = {"score": 0, "document": res["document"]}
            combined_results[doc_id]["score"] += res["score"] * dense_weight
        
        for res in sparse_results:
            doc_id = int(res["document"]) # whoosh returns string id
            if doc_id not in combined_results:
                # This case should be rare if the same docs are in both retrievers
                continue 
            combined_results[doc_id]["score"] += res["score"] * sparse_weight
            
        
        sorted_results = sorted(combined_results.values(), key=lambda x: x["score"], reverse=True)
        return sorted_results[:k] 