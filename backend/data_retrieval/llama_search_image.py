from llama_index.core import load_index_from_storage, StorageContext
from llama_index.embeddings.clip import ClipEmbedding
from typing import List, Dict, Any
import os
import base64
from io import BytesIO
from PIL import Image

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
        
        self.embed_model = ClipEmbedding()
        
        storage_context = StorageContext.from_defaults(
            persist_dir=IMAGE_STORAGE_PATH
        )
        self.index = load_index_from_storage(
            storage_context,
            embed_model=self.embed_model
        )
        print("Image index loaded successfully")
    
    def _process_image_input(self, image_input: str) -> Image.Image:
        
        if os.path.exists(image_input):
            return Image.open(image_input)
        
        elif image_input.startswith('data:image'):
            image_data = image_input.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            return Image.open(BytesIO(image_bytes))
        
        elif image_input.startswith('http://') or image_input.startswith('https://'):
            import requests
            response = requests.get(image_input)
            return Image.open(BytesIO(response.content))
        
        else:
            try:
                image_bytes = base64.b64decode(image_input)
                return Image.open(BytesIO(image_bytes))
            except Exception as e:
                raise ValueError(f"Could not process image input: {e}")
    
    def search(self, image_input: str, limit: int = 5) -> List[Dict[str, Any]]:
        from sentence_transformers import SentenceTransformer
        from llama_index.core.schema import QueryBundle
        
        img = Image.open(image_input).convert('RGB')
        
        clip_model = SentenceTransformer('clip-ViT-B-32')
        query_embedding = clip_model.encode(img)
        
        query_bundle = QueryBundle(
            query_str="",   
            embedding=query_embedding.tolist()
        )
        
        retriever = self.index.as_retriever(similarity_top_k=limit)
        nodes = retriever.retrieve(query_bundle)
        
        results = []
        for node in nodes:
            result = {
                "product_id": node.metadata.get("product_id"),
                "title": node.metadata.get("title"),
                "price": node.metadata.get("price"),
                "category": node.metadata.get("category"),
                "thumbnail": node.metadata.get("thumbnail"),
                "similarity_score": node.score
            }
            results.append(result)
        
        return results


_image_search_instance = None

def get_image_search() -> ImageProductSearch:
    global _image_search_instance
    if _image_search_instance is None:
        _image_search_instance = ImageProductSearch()
    return _image_search_instance


def search_products_by_image(image_input: str, limit: int = 5) -> List[Dict[str, Any]]:
    
    searcher = get_image_search()
    return searcher.search(image_input, limit)