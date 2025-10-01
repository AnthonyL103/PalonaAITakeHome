# CartPal - AI-Powered Shopping Assistant

An intelligent e-commerce assistant that combines semantic text search, visual image search, and natural language conversation to help users find products. Built with LLMs, vector embeddings, and real-time tool calling.


## Features

### 1. Natural Language Conversation
- Conversational AI that understands context and maintains conversation history as a chat thread.
- Answers questions about its capabilities and provides shopping guidance.
- Friendly, retro-styled interface inspired by classic shopping catalogs.

### 2. Smart Text-Based Product Search
- Semantic search using BGE embeddings for natural language queries
- Smart filter generation based on user queries (price ranges, brands, categories, ratings)
- Example: "Apple headphones under $200" automatically filters by brand and price
- Metadata filtering at the vector store level for efficient searches

### 3. Visual Image-Based Search
- CLIP embeddings for finding visually similar products
- Upload product images to find similar items in the catalog
- Same metadata filtering capabilities as text search
- Example: "[airpods.img] find me products like this one but under $200"

## 4. Real-Time Tool Updates via WebSocket
- WebSocket connection forwards tool execution updates from backend to frontend
- Shows users exactly what's happening: "Searching by text: 'headphones'", "Applying filters: Max Price $200"
- Improves perceived performance - users see progress instead of staring at a loading spinner

## Architecture

### Technology Stack

**Backend:**
- **FastAPI** - Async web framework for API endpoints and WebSocket connections
  - *Why:* Native async support, built-in WebSocket handling, automatic OpenAPI docs, and fast request handling for real-time applications

- **LlamaIndex** - RAG framework for vector store management and retrieval
  - *Why:* Intuitive API for storing embeddings with metadata, enabling hybrid search (semantic similarity + metadata filters) at the vector store level

- **OpenAI GPT-4o** - LLM for conversational agent and tool calling
  - *Why:* Superior function calling capabilities, maintains conversation context, and generates well-formatted markdown responses. Enables the agent to intelligently extract filters from natural language queries

- **MCP (Model Context Protocol) / FastAgent** - Tool server architecture for modular search tools
  - *Why:* Separates tool implementation from agent logic, enabling clean architecture with independent search services. FastAgent provides simple setup while maintaining flexibility for custom integrations

- **HuggingFace BGE** - Text embeddings (`BAAI/bge-small-en-v1.5`)
  - *Why:* High-quality semantic embeddings optimized for retrieval tasks, with good balance of speed and accuracy for e-commerce queries

- **CLIP ViT-B/32** - Image embeddings via SentenceTransformers
  - *Why:* Pre-trained vision-language model that captures semantic similarity between images, enabling "find similar products" functionality without fine-tuning

**Frontend:**
- **React + TypeScript** - Component-based UI with type safety
  - *Why:* Type safety catches errors at compile time, component architecture enables reusable UI elements, and strong ecosystem support for rapid development

- **TailwindCSS** - Utility-first styling with custom retro theme
  - *Why:* Inline utility classes eliminate CSS file management, rapid prototyping with design consistency, and easy customization for the retro shopping catalog aesthetic

- **Vite** - Fast development and build tooling
  - *Why:* Hot module replacement for instant feedback during development, optimized production builds with code splitting, and native ES modules support

- **WebSocket** - Real-time tool execution updates
  - *Why:* Bidirectional communication enables server-to-client push notifications, showing users search progress and tool execution status in real-time without polling
  
**Data:**
- **Vector Store** - LlamaIndex with metadata filtering support
  - *Why:* Enables hybrid search combining semantic similarity with structured filters (price, brand, category). Metadata stored alongside embeddings allows efficient filtering at query time rather than post-processing

- **Product Catalog** - DummyJSON API (1000 products)
  - *Why:* Provides realistic e-commerce data with product images, descriptions, categories, and pricing without requiring database setup or API authentication

- **Dual Indexes** - Separate text and image vector indexes
  - *Why:* Text (BGE) and image (CLIP) embeddings have different dimensions and semantic properties. Separate indexes optimize for each modality's specific retrieval patterns

### System Design

```
┌─────────────────┐
│   React UI      │
│  (Retro Theme)  │
└────────┬────────┘
         │
    ┌────┴─────┐
    │  FastAPI │◄──── WebSocket (Tool Updates)
    └────┬─────┘
         │
    ┌────┴──────────┐
    │  Agent Layer  │
    │   (GPT-4o)    │
    └────┬──────────┘
         │
    ┌────┴─────────────┐
    │   MCP Server     │
    │  (Search Tools)  │
    └────┬─────────────┘
         │
    ┌────┴──────────────────┐
    │  LlamaIndex Retrieval │
    ├───────────┬───────────┤
    │ Text Index│Image Index│
    │  (BGE)    │  (CLIP)   │
    └───────────┴───────────┘
```

### Key Design Decisions

### Key Design Decisions

**1. Metadata Filtering at Vector Store Level**
- Filters (price, brand, category, rating, stock) applied during vector search
- More efficient than post-filtering retrieved results
- Enables precise budget-constrained searches

**2. MCP Tool Architecture**
- Modular search tools following Model Context Protocol
- Clean separation: agent logic vs. search implementation
- Tools communicate search progress via WebSocket
- Retry logic with error classification and exponential backoff for transient failures

**3. Dual Vector Indexes**
- Separate indexes for text and image embeddings
- Text: BGE embeddings optimized for semantic text search
- Images: Pre-computed CLIP embeddings stored with metadata
- Trade-off: Storage overhead for faster query performance

**4. Agent Prompt Engineering**
- Single agent handles all use cases (conversation, text search, image search)
- Detailed instructions for filter extraction from natural language
- Repetitive emphasis on critical formatting (response tags, image tags) to ensure consistency
- Structured markdown output format for consistent UI rendering
- Example-driven prompting for better filter parameter usage

**5. Real-Time Feedback**
- WebSocket updates show tool execution progress
- Users see search parameters being applied in real-time
- Reduces perceived latency during CLIP embedding generation and LLM response

**6. Error Handling Strategy**
- Centralized error classification (retryable vs. non-retryable)
- Retry logic at multiple layers (search functions, MCP tools, FastAPI endpoints)
- Keyword-based error detection for intelligent retry decisions
- Graceful degradation with fallbacks when services fail

## Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 16+
- OpenAI API key

### 1. Clone Repository
```bash
git clone https://github.com/AnthonyL103/CartPal.git
cd cartpal
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variable in fastagent.secrets.yaml
provider: openai

openai:
  api_key: "YOUR API KEY"
  reasoning_effort: "high"
  
  
# Initialize vector indexes (one-time setup)
python data_retrieval/llama_search_config.py
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

### 4. Run Application

**Terminal 1 - Backend:**
```bash
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access the app:** http://localhost:5173

## Project Structure

```
cartpal/
├── app.py                          # FastAPI main application
├── servers/
│   ├── agent.py                    # Agent configuration & prompt
│   └── server.py                   # MCP tool server
├── data_retrieval/
│   ├── llama_search_config.py      # Index creation script
│   ├── llama_search_text.py        # Text search with metadata filters
│   └── llama_search_image.py       # Image search with CLIP
├── tooling_updates/
│   └── websocket_http_sender.py    # WebSocket message sender
├── storage/
│   ├── text_index/                 # BGE vector index
│   └── image_index/                # CLIP vector index
├── frontend/
│   ├── src/
│   │   ├── CommerceAgent.tsx       # Main UI component
│   │   └── WebSocket.tsx           # WebSocket hook
│   └── package.json
└── requirements.txt
```

## API Documentation

### Endpoints

**POST /agent**
```json
{
  "prompt": "Apple headphones under $200",
  "image": null  // or path to uploaded image
}
```

**POST /upload_image**
- Multipart form data with image file
- Returns server path for image search

**POST /reset_conversation**
- Clears conversation history
- Restarts agent context

**WS /ws**
- WebSocket connection for real-time tool updates

**GET /health**
- Service health check

### Search Tool Parameters

Both `semantic_search_text` and `semantic_search_image` support:
- `top_k`: Number of results (1-50)
- `category`: Product category filter
- `min_price` / `max_price`: Price range filters
- `min_rating`: Minimum product rating (0-5)
- `brand`: Brand name filter
- `in_stock`: Only show available products

## Usage Examples

### Text Search
```
"Show me laptops between $500 and $1000"
→ Filters: category="laptops", min_price=500, max_price=1000

"Highly rated Apple products"
→ Filters: brand="Apple", min_rating=4.0
```

### Image Search
1. Click camera icon
2. Upload product image
3. Agent finds visually similar items using CLIP embeddings
4. Optional: Add text filters ("under $100")

### Conversation
```
"What's your name?"
"What can you help me with?"
"Tell me about this product [shows image]"
```

## Performance Considerations

**Index Loading:**
- First search after startup takes ~2-3 seconds (model loading)
- Subsequent searches: <500ms for text, ~1-2s for images

**Optimizations:**
- Singleton pattern for search instances (models loaded once)
- Pre-computed CLIP embeddings stored in index
- Metadata filters reduce search space
- Async operations prevent blocking

**Scalability:**
- Current: ~1000 products, single-machine deployment
- Scale: Add vector database (Pinecone/Weaviate), load balancing, caching
- Deploy as a plugin or as a webpage (Amplify, Cloudfront + S3)

## Limitations & Future Work

**Current Limitations:**
- Product catalog limited to 1000 items (DummyJSON)
- Image search slower than text (CLIP encoding on-the-fly)
- No persistent conversation storage (resets on server restart) for agent to reuse as context
- Single-user 

**Potential Improvements:**
- Add product comparison feature
- Scrape data from multiple e-commerce giant websites for realism
- Add price tracking and alerts
- Product reviews analysis

## Testing

Run searches to verify:
```bash
# Text search with filters
"headphones under $200"

# Image search
Upload phone image → finds similar phones

# Conversation
"What can you do?"
```

## License

MIT

## Acknowledgments

- Built for AI Agent Take-Home Exercise
- Product data from DummyJSON API
- Embeddings: HuggingFace BGE & OpenAI CLIP
- LLM: OpenAI GPT-4o