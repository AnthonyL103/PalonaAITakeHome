import json
from mcp.server.fastmcp import FastMCP
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_retrieval.llama_search_text import search_products_by_text
from data_retrieval.llama_search_image import search_products_by_image

mcp = FastMCP("Semantic Search Agent")

semantic_search_image_description = """
Search for products visually similar to an uploaded image with optional filters.

This tool uses CLIP embeddings to find products that look similar to the provided image.
Use this when a user uploads a photo or asks to find products similar to an image.
The image_path should be either a file path or a base64 encoded image string.

You can filter results by:
- category: Product category (e.g., "laptops", "smartphones", "mobile-accessories")
- min_price: Minimum price in dollars
- max_price: Maximum price in dollars
- min_rating: Minimum product rating (0-5)
- brand: Specific brand name
- in_stock: Set to true to only show available products
"""

@mcp.tool("semantic_search_image", semantic_search_image_description)
async def semantic_search_image(
    image_path: str,
    top_k: int = 3,
    category: str = None,
    min_price: float = None,
    max_price: float = None,
    min_rating: float = None,
    brand: str = None,
    in_stock: bool = False
) -> str:
    """
    Perform semantic search on the provided image and return top-k similar items.
    
    Args:
        image_path: Path to image file or base64 encoded image string
        top_k: Number of similar products to return (default: 3)
        category: Filter by category (optional)
        min_price: Minimum price filter (optional)
        max_price: Maximum price filter (optional)
        min_rating: Minimum rating filter (optional)
        brand: Filter by brand (optional)
        in_stock: Only show in-stock products (default: False)
    
    Returns:
        JSON string with similar products
    """
    try:
        results = search_products_by_image(
            image_path,
            limit=top_k,
            category=category,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
            brand=brand,
            in_stock=in_stock
        )
        
        response = {
            "status": "success",
            "num_results": len(results),
            "filters_applied": {
                "category": category,
                "min_price": min_price,
                "max_price": max_price,
                "min_rating": min_rating,
                "brand": brand,
                "in_stock": in_stock
            },
            "products": results
        }
        
        return json.dumps(response, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


semantic_search_text_description = """
Search for products using natural language text descriptions with optional filters.

This tool uses semantic embeddings to understand the meaning of the query and find relevant products.
Use this when a user describes what they're looking for in words.

Examples:
- 'sports t-shirt'
- 'affordable laptop under $800'
- 'running shoes for women'
- 'Apple headphones'
- 'highly rated smartphones'

You can filter results by:
- category: Product category (e.g., "laptops", "smartphones", "mobile-accessories")
- min_price: Minimum price in dollars
- max_price: Maximum price in dollars
- min_rating: Minimum product rating (0-5)
- brand: Specific brand name (e.g., "Apple", "Samsung", "Nike")
- in_stock: Set to true to only show available products

IMPORTANT: Extract price ranges, brand names, categories, and rating requirements from the user's query
and pass them as filter parameters for better results.
"""

@mcp.tool("semantic_search_text", semantic_search_text_description)
async def semantic_search_text(
    query: str,
    top_k: int = 3,
    category: str = None,
    min_price: float = None,
    max_price: float = None,
    min_rating: float = None,
    brand: str = None,
    in_stock: bool = False
) -> str:
    """
    Perform semantic search based on the provided text query and return top-k relevant items.
    
    Args:
        query: Natural language search query describing desired products
        top_k: Number of relevant products to return (default: 3)
        category: Filter by category (optional)
        min_price: Minimum price filter (optional)
        max_price: Maximum price filter (optional)
        min_rating: Minimum rating filter (optional)
        brand: Filter by brand (optional)
        in_stock: Only show in-stock products (default: False)
    
    Returns:
        JSON string with matching products
    """
    try:
        results = search_products_by_text(
            query,
            limit=top_k,
            category=category,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
            brand=brand,
            in_stock=in_stock
        )
        
        response = {
            "status": "success",
            "query": query,
            "num_results": len(results),
            "filters_applied": {
                "category": category,
                "min_price": min_price,
                "max_price": max_price,
                "min_rating": min_rating,
                "brand": brand,
                "in_stock": in_stock
            },
            "products": results
        }
        
        return json.dumps(response, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e),
            "query": query
        })


if __name__ == "__main__":
    mcp.run()