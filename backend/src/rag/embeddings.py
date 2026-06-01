"""
src/rag/embeddings.py
"""

import os
from chromadb.utils import embedding_functions

def get_embedding_function():
    # We are reverting to the default local SentenceTransformers model.
    # The Hugging Face Inference API is too aggressively rate-limited for bulk DB operations.
    return embedding_functions.DefaultEmbeddingFunction()
