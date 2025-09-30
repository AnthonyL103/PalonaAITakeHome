from llama_index.core import load_index_from_storage, StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from typing import List, Dict, Any
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEXT_STORAGE_PATH = os.path.join(BASE_DIR, "storage", "text_index")


class TextProductSearch:
    def __init__(self):
        self.index = None
        self.embed_model = None
        self._load_index()
    
    def _load_index(self):
        if not os.path.exists(TEXT_STORAGE_PATH):
            raise FileNotFoundError(
                f"Text index not found at {TEXT_STORAGE_PATH}. "
                "Please run llama_search_config.py first to create indexes."
            )
        
        self.embed_model = HuggingFaceEmbedding(
            model_name="BAAI/bge-small-en-v1.5"
        )
        
        storage_context = StorageContext.from_defaults(
            persist_dir=TEXT_STORAGE_PATH
        )
        self.index = load_index_from_storage(
            storage_context,
            embed_model=self.embed_model
        )
        print("Text index loaded successfully")
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        retriever = self.index.as_retriever(similarity_top_k=limit)
        nodes = retriever.retrieve(query)
        
        results = []
        for node in nodes:
            result = {
                "product_id": node.metadata.get("product_id"),
                "title": node.metadata.get("title"),
                "price": node.metadata.get("price"),
                "category": node.metadata.get("category"),
                "rating": node.metadata.get("rating"),
                "stock": node.metadata.get("stock"),
                "brand": node.metadata.get("brand"),
                "thumbnail": node.metadata.get("thumbnail"),
                "similarity_score": node.score,
                "text_snippet": node.text[:200] + "..." if len(node.text) > 200 else node.text
            }
            results.append(result)
        
        return results


_text_search_instance = None

def get_text_search() -> TextProductSearch:
    global _text_search_instance
    if _text_search_instance is None:
        _text_search_instance = TextProductSearch()
    return _text_search_instance


def search_products_by_text(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    searcher = get_text_search()
    return searcher.search(query, limit)