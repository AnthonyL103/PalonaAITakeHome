import asyncio
import json
from mcp.server.fastmcp import FastMCP
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))) 
from data_retrieval.llama_search_text import search_products_by_text
from data_retrieval.llama_search_image import search_products_by_image

mcp = FastMCP("Semantic Search Agent")

semantic_search_image_description = """
Search for products visually similar to an uploaded image. 
This tool uses CLIP embeddings to find products that look similar to the provided image.
Use this when a user uploads a photo or asks to find products similar to an image.
The image_path should be either a file path or a base64 encoded image string.
"""

@mcp.tool("semantic_search_image", semantic_search_image_description)
async def semantic_search_image(image_path: str, top_k: int = 3) -> str:
    """
    Perform semantic search on the provided image and return top-k similar items.
    
    Args:
        image_path: Path to image file or base64 encoded image string
        top_k: Number of similar products to return (default: 3)
    
    Returns:
        JSON string with similar products
    """
    try:
        results = search_products_by_image(image_path, limit=top_k)
        
        response = {
            "status": "success",
            "num_results": len(results),
            "products": results
        }
        
        return json.dumps(response, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


semantic_search_text_description = """
Search for products using natural language text descriptions.
This tool uses semantic embeddings to understand the meaning of the query and find relevant products.
Use this when a user describes what they're looking for in words.
Examples: 'sports t-shirt', 'affordable laptop', 'running shoes for women', 'kitchen appliances under $100'
"""

@mcp.tool("semantic_search_text", semantic_search_text_description)
async def semantic_search_text(query: str, top_k: int = 3) -> str:
    """
    Perform semantic search based on the provided text query and return top-k relevant items.
    
    Args:
        query: Natural language search query describing desired products
        top_k: Number of relevant products to return (default: 3)
    
    Returns:
        JSON string with matching products
    """
    try:
        results = search_products_by_text(query, limit=top_k)
        
        response = {
            "status": "success",
            "query": query,
            "num_results": len(results),
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