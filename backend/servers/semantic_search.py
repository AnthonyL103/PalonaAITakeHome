import json
from mcp.server.fastmcp import FastMCP
import sys
import os
from textwrap import dedent
import logging
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_retrieval.llama_search_text import search_products_by_text
from data_retrieval.llama_search_image import search_products_by_image
from tooling_updates.websocket_http_sender import send_to_frontend

from app import is_retryable_error, async_retry_operation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    
    try:
        if not image_path or not image_path.strip():
            return json.dumps({
                "status": "error",
                "message": "Image path is required",
                "error_type": "validation_error"
            })
        
        if top_k < 1 or top_k > 50:
            return json.dumps({
                "status": "error",
                "message": "top_k must be between 1 and 50",
                "error_type": "validation_error"
            })
        
        if not os.path.exists(image_path):
            return json.dumps({
                "status": "error",
                "message": f"Image file not found: {image_path}",
                "error_type": "file_not_found"
            })
        
        filters_desc = []
        if category:
            filters_desc.append(f"**Category:** {category}")
        if min_price:
            filters_desc.append(f"**Min Price:** ${min_price}")
        if max_price:
            filters_desc.append(f"**Max Price:** ${max_price}")
        if min_rating:
            filters_desc.append(f"**Min Rating:** {min_rating}⭐")
        if brand:
            filters_desc.append(f"**Brand:** {brand}")
        if in_stock:
            filters_desc.append("**Stock:** In stock only")
        
        filters_text = " • ".join(filters_desc) if filters_desc else "No filters applied"
        
        frontend_tool_update = dedent(f"""
        ## SEARCH IN PROGRESS

        Searching by image using CLIP embeddings...

        **Search Parameters:**

        - Searching for: {top_k} visually similar products
        - {filters_text}

        *Processing image data and comparing with catalog...*
        """)
        
        try:
            await send_to_frontend(frontend_tool_update.strip())
        except Exception as ws_error:
            logger.warning(f"WebSocket update failed: {ws_error}")
        
        async def _search():
            logger.info(f"Image search: {image_path}, top_k={top_k}")
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                search_products_by_image,
                image_path,
                top_k,
                category,
                min_price,
                max_price,
                min_rating,
                brand,
                in_stock
            )
            return results
        
        results = await async_retry_operation(_search, max_retries=2)
        
        logger.info(f"Image search complete: {len(results)} results")
        
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
        error_type = "retryable_error" if is_retryable_error(e) else "non_retryable_error"
        logger.error(f"Image search error ({error_type}): {e}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": str(e),
            "error_type": error_type
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
 
    try:
        if not query or not query.strip():
            return json.dumps({
                "status": "error",
                "message": "Query text is required",
                "error_type": "validation_error"
            })
        
        if len(query.strip()) > 500:
            return json.dumps({
                "status": "error",
                "message": "Query too long (max 500 characters)",
                "error_type": "validation_error"
            })
        
        if top_k < 1 or top_k > 50:
            return json.dumps({
                "status": "error",
                "message": "top_k must be between 1 and 50",
                "error_type": "validation_error"
            })
        
        filters_desc = []
        if category:
            filters_desc.append(f"**Category:** {category}")
        if min_price:
            filters_desc.append(f"**Min Price:** ${min_price}")
        if max_price:
            filters_desc.append(f"**Max Price:** ${max_price}")
        if min_rating:
            filters_desc.append(f"**Min Rating:** {min_rating}⭐")
        if brand:
            filters_desc.append(f"**Brand:** {brand}")
        if in_stock:
            filters_desc.append("**Stock:** In stock only")
        
        filters_text = " • ".join(filters_desc) if filters_desc else "No filters applied"
        
        frontend_tool_update = dedent(f"""
        ## SEARCH IN PROGRESS

        Searching by text: **"{query}"**

        **Search Parameters:**

        - Looking for: {top_k} best matches
        - {filters_text}

        *Analyzing product descriptions with AI embeddings...*
        """)
        
        try:
            await send_to_frontend(frontend_tool_update.strip())
        except Exception as ws_error:
            logger.warning(f"WebSocket update failed: {ws_error}")
        
        async def _search():
            logger.info(f"Text search: '{query}', top_k={top_k}")
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                search_products_by_text,
                query,
                top_k,
                category,
                min_price,
                max_price,
                min_rating,
                brand,
                in_stock
            )
            return results
        
        results = await async_retry_operation(_search, max_retries=2)
        
        logger.info(f"Text search complete: {len(results)} results")
        
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
        error_type = "retryable_error" if is_retryable_error(e) else "non_retryable_error"
        logger.error(f"Text search error ({error_type}): {e}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": str(e),
            "query": query,
            "error_type": error_type
        })


if __name__ == "__main__":
    mcp.run()