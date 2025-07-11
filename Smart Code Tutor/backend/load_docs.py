import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

class SimpleVectorStore:
    def __init__(self):
        self.client = OpenAI()
        self.documents = []
        self.embeddings = []

    def add_texts(self, texts):
        for text in texts:
            # Get embeddings from OpenAI
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            embedding = response.data[0].embedding
            
            # Store text and its embedding
            self.documents.append(text)
            self.embeddings.append(embedding)
        
        # Save to disk
        self.save("vector_store")
    
    def save(self, directory):
        os.makedirs(directory, exist_ok=True)
        with open(os.path.join(directory, "store.json"), "w") as f:
            json.dump({
                "documents": self.documents,
                "embeddings": self.embeddings
            }, f)
        print("Vector store saved successfully!")
    
    @classmethod
    def load(cls, directory):
        store = cls()
        try:
            with open(os.path.join(directory, "store.json"), "r") as f:
                data = json.load(f)
                store.documents = data["documents"]
                store.embeddings = data["embeddings"]
        except FileNotFoundError:
            print("No existing vector store found.")
        return store

def split_text(text, chunk_size=1000, overlap=200):
    chunks = []
    start = 0
    
    while start < len(text):
        # Find the end of this chunk
        end = start + chunk_size
        
        # If we're not at the end of the text, try to find a good break point
        if end < len(text):
            # Try to find the last period or newline before the end
            last_break = max(
                text.rfind("\n", start, end),
                text.rfind(". ", start, end)
            )
            if last_break != -1:
                end = last_break + 1
        
        # Add the chunk to our list
        chunks.append(text[start:end].strip())
        
        # Move the start pointer, accounting for overlap
        start = end - overlap
    
    return chunks

def load_documentation():
    # Read the documentation file
    with open("docs/programming_docs.txt", "r") as f:
        raw_docs = f.read()

    # Split the text into chunks
    texts = split_text(raw_docs)

    # Create vector store and add texts
    vector_store = SimpleVectorStore()
    vector_store.add_texts(texts)

if __name__ == "__main__":
    load_documentation() 