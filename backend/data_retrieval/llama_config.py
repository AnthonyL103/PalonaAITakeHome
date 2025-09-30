import json
import os
from pathlib import Path
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.core.schema import ImageDocument
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.core.indices import MultiModalVectorStoreIndex

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEXT_STORAGE_PATH = os.path.join(BASE_DIR, "storage", "text_index")
IMAGE_STORAGE_PATH = os.path.join(BASE_DIR, "storage", "image_index")
CATALOG_PATH = os.path.join(BASE_DIR, "data", "product_catalog.json")

def fetch_product_catalog():
    import requests
    
    response = requests.get('https://dummyjson.com/products?limit=100')
    data = response.json()
    
    os.makedirs("./data", exist_ok=True)
    with open(CATALOG_PATH, 'w') as f:
        json.dump(data['products'], f, indent=2)
    
    return data['products']


def create_text_index(products):
    print("Creating text index...")
    
    text_docs = [
        Document(
            text=f"{p['title']}. {p['description']}. Category: {p['category']}. Brand: {p.get('brand', 'Generic')}",
            metadata={
                "product_id": p['id'],
                "title": p['title'],
                "price": p['price'],
                "category": p['category'],
                "rating": p.get('rating', 0),
                "stock": p.get('stock', 0),
                "thumbnail": p['thumbnail'],
                "brand": p.get('brand', 'Generic')
            }
        )
        for p in products
    ]
    
    embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-small-en-v1.5"  
    )
    
    text_index = VectorStoreIndex.from_documents(
        text_docs,
        embed_model=embed_model,
        show_progress=True
    )
    
    os.makedirs(TEXT_STORAGE_PATH, exist_ok=True)
    text_index.storage_context.persist(persist_dir=TEXT_STORAGE_PATH)
    
    print(f"Text index created and saved to {TEXT_STORAGE_PATH}")
    return text_index

def create_image_index(products):
    print("Creating image index with CLIP vision embeddings...")
    
    import requests
    from PIL import Image
    from io import BytesIO
    from sentence_transformers import SentenceTransformer
    from llama_index.core import Document, VectorStoreIndex, Settings
    
    clip_model = SentenceTransformer('clip-ViT-B-32')
    
    docs_with_embeddings = []
    
    for p in products:
        try:
            response = requests.get(p['thumbnail'], timeout=10)
            img = Image.open(BytesIO(response.content)).convert('RGB')
            
            image_embedding = clip_model.encode(img)
            
            doc = Document(
                text=p['title'],
                metadata={
                    "product_id": p['id'],
                    "title": p['title'],
                    "price": p['price'],
                    "category": p['category'],
                    "thumbnail": p['thumbnail']
                },
                embedding=image_embedding.tolist()
            )
            docs_with_embeddings.append(doc)
            print(f"✓ {p['title']}")
            
        except Exception as e:
            print(f"✗ Failed {p['title']}: {e}")
    

    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    
    image_index = VectorStoreIndex(
        docs_with_embeddings,
        embed_model=embed_model  
    )
    
    os.makedirs(IMAGE_STORAGE_PATH, exist_ok=True)
    image_index.storage_context.persist(persist_dir=IMAGE_STORAGE_PATH)
    
    print(f"Image index created with {len(docs_with_embeddings)} images")
    return image_index


def initialize_indexes():
    print("Initializing product catalog indexes...")
    

    products = fetch_product_catalog()
    print(f"Fetched {len(products)} products")
    
    text_index = create_text_index(products)
    image_index = create_image_index(products)
    
    print("\nAll indexes created successfully!")
    print(f"Text index: {TEXT_STORAGE_PATH}")
    print(f"Image index: {IMAGE_STORAGE_PATH}")
    
    return text_index, image_index


if __name__ == "__main__":
    initialize_indexes()