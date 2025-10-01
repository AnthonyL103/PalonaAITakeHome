from llama_index.core import load_index_from_storage, StorageContext
from llama_index.embeddings.clip import ClipEmbedding
from typing import List, Dict, Any, Optional
import os
import base64
from io import BytesIO
from PIL import Image
import logging
import time

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import is_retryable_error, retry_operation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_STORAGE_PATH = os.path.join(BASE_DIR, "storage", "image_index")




class ImageProductSearch:
    def __init__(self):
        self.index = None
        self.embed_model = None
        self._load_index()
    
    def _load_index(self):
        if not os.path.exists(IMAGE_STORAGE_PATH):
            raise FileNotFoundError(
                f"Image index not found at {IMAGE_STORAGE_PATH}. "
                "Please run llama_search_config.py first to create indexes."
            )
        
        def _load():
            self.embed_model = ClipEmbedding()
            storage_context = StorageContext.from_defaults(persist_dir=IMAGE_STORAGE_PATH)
            self.index = load_index_from_storage(storage_context, embed_model=self.embed_model)
            logger.info("Image index loaded successfully")
        
        try:
            retry_operation(_load, max_retries=2)
        except Exception as e:
            logger.error(f"Failed to load image index after retries: {e}")
            raise
    
    def _process_image_input(self, image_input: str) -> Image.Image:
        try:
            if os.path.exists(image_input):
                return Image.open(image_input)
            
            elif image_input.startswith('data:image'):
                image_data = image_input.split(',')[1]
                image_bytes = base64.b64decode(image_data)
                return Image.open(BytesIO(image_bytes))
            
            elif image_input.startswith('http://') or image_input.startswith('https://'):
                import requests
                response = requests.get(image_input, timeout=10)
                return Image.open(BytesIO(response.content))
            
            else:
                image_bytes = base64.b64decode(image_input)
                return Image.open(BytesIO(image_bytes))
                
        except Exception as e:
            logger.error(f"Failed to process image input: {e}")
            raise ValueError(f"Could not process image input: {e}")
    
    def search(
        self, 
        image_input: str, 
        limit: int = 5,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        brand: Optional[str] = None,
        in_stock: bool = False
    ) -> List[Dict[str, Any]]:
        if not image_input:
            raise ValueError("Image input cannot be empty")
        
        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")
        
        def _search():
            from sentence_transformers import SentenceTransformer
            from llama_index.core.schema import QueryBundle
            from llama_index.core.vector_stores import MetadataFilters, MetadataFilter
            
            img = Image.open(image_input).convert('RGB')
            
            clip_model = SentenceTransformer('clip-ViT-B-32')
            query_embedding = clip_model.encode(img)
            
            query_bundle = QueryBundle(
                query_str="",
                embedding=query_embedding.tolist()
            )
            
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
            nodes = retriever.retrieve(query_bundle)
            
            results = []
            for node in nodes:
                result = {
                    "product_id": node.metadata.get("product_id"),
                    "title": node.metadata.get("title"),
                    "price": node.metadata.get("price"),
                    "category": node.metadata.get("category"),
                    "thumbnail": node.metadata.get("thumbnail"),
                    "similarity_score": node.score,
                    "rating": node.metadata.get("rating"),
                    "stock": node.metadata.get("stock"),
                    "brand": node.metadata.get("brand")
                }
                results.append(result)
            
            logger.info(f"Image search found {len(results)} results")
            return results
        
        try:
            return retry_operation(_search, max_retries=2)
        except Exception as e:
            error_type = "retryable" if is_retryable_error(e) else "non-retryable"
            logger.error(f"Image search failed ({error_type}): {e}", exc_info=True)
            raise


_image_search_instance = None

def get_image_search() -> ImageProductSearch:
    global _image_search_instance
    if _image_search_instance is None:
        _image_search_instance = ImageProductSearch()
    return _image_search_instance


def search_products_by_image(
    image_input: str,
    limit: int = 5,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    brand: Optional[str] = None,
    in_stock: bool = False
) -> List[Dict[str, Any]]:
    searcher = get_image_search()
    return searcher.search(
        image_input,
        limit=limit,
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        brand=brand,
        in_stock=in_stock
    )