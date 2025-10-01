from llama_index.core import load_index_from_storage, StorageContext
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from typing import List, Dict, Any, Optional
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
    
    def search(
        self, 
        query: str, 
        limit: int = 5,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        brand: Optional[str] = None,
        in_stock: bool = False
    ) -> List[Dict[str, Any]]:
       
        filters = []
        
        if category:
            filters.append(MetadataFilter(key="category", value=category, operator="=="))
        
        if min_price is not None:
            filters.append(MetadataFilter(key="price", value=min_price, operator=">="))
        
        if max_price is not None:
            filters.append(MetadataFilter(key="price", value=max_price, operator="<="))
        
        if min_rating is not None:
            filters.append(MetadataFilter(key="rating", value=min_rating, operator=">="))
        
        if brand:
            filters.append(MetadataFilter(key="brand", value=brand, operator="=="))
        
        if in_stock:
            filters.append(MetadataFilter(key="stock", value=0, operator=">"))
        
        retriever_kwargs = {"similarity_top_k": limit}
        
        if filters:
            retriever_kwargs["filters"] = MetadataFilters(filters=filters)
        
        retriever = self.index.as_retriever(**retriever_kwargs)
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


def search_products_by_text(
    query: str, 
    limit: int = 5,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    brand: Optional[str] = None,
    in_stock: bool = False
) -> List[Dict[str, Any]]:
    
    searcher = get_text_search()
    return searcher.search(
        query=query,
        limit=limit,
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        brand=brand,
        in_stock=in_stock
    )