# Support Chatbot Backend

A FastAPI-based backend for an intelligent customer service chatbot powered by LangChain, LangGraph, and Groq's language models. This project implements a strictly-scoped AI agent that provides information exclusively about Company.

## Features

- **LLM-Powered Chatbot**: Built with LangChain and LangGraph for reliable agent orchestration
- **Groq Integration**: Uses Groq's optimized LLM endpoints for fast inference
- **Strict Information Scope**: Configured with guardrails to only answer questions about Company
- **RESTful API**: FastAPI endpoints for chat interactions and health checks
- **Configuration Management**: Uses Dynaconf for flexible environment-based settings

## Installation

### Prerequisites

- Python 3.12.13
- Groq API key
- OpenAI API key

- PostgreSQL: install Postgres on your system and ensure it's running. Update the `DB_URI` in `settings.toml` with your database connection string before running the setup step below.

### Setup

1. **Clone or navigate to the project directory**

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure secrets**
   
   Create a `.secrets.toml` file in the project root and add both your OpenAI and Groq API keys:
   ```toml
   [default]
   OPENAI_API_KEY = "your-openai-api-key-here"
   GROQ_API_KEY = "your-groq-api-key-here"
   ```

5. **Initialize the vector database**

   Run the script.

   run:
   ```bash
   python -m database.ingest_data
   ```

   This will create the vector database collections needed by the chatbot.

6. **Setup PostgreSQL tables (first-time only)**

   If you plan to use Postgres-backed features, run the table setup script once to create required tables:

   ```bash
   python -m utils.postgres_conn
   ```

## Running the Server

```bash
python app.py
```

The server will start at `http://localhost:8000`

## API Endpoints

### Chat Endpoint
**POST** `/chat`

Send a message to the chatbot.

**Request:**
```json
{
   "message": "What supplements does Nutritional World offer?",
   "chat_id": "1234"
}
```

**Response:**
```json
{
  "response": "Nutritional World offers halal-certified supplements including whey protein, creatine, weight gainers, fat burners, pre-workout, post-workout, multivitamins, and energy supplements. Visit www.nutritionalworld.com.pk or contact us on WhatsApp at +92 306 9111184 for details."
}
```

### Health Check
**GET** `/health`

Check if the server is running.

**Response:**
```json
{
  "status": "ok"
}
```

## Project Structure

```
backend/
├── app.py                        # FastAPI application and endpoints
├── README.md                     # Project documentation
├── requirements.txt              # Python dependencies
├── settings.toml                 # Default settings configuration
├── .secrets.toml                 # Configuration secrets (create this - add to .gitignore)
├── agents/                       # Domain-specific agent implementations
│   ├── aggregator_agent.py
│   ├── general_agent.py
│   ├── order_management_agent.py
│   ├── product_agent.py
│   └── router_agent.py
├── database/                     # Vector DB ingestion and config
│   ├── chroma_config.py
│   └── ingest_data.py
├── graph/                        # LangGraph workflow and state logic
│   ├── conditions.py
│   └── graph.py
├── state/
│   └── graph_state.py            # Current workflow state tracking
├── tools/
│   └── product_search.py         # Product search tools
├── utils/
│   ├── config.py                 # Dynaconf and config helpers
│   ├── logger.py                 # Logging utilities
│   ├── postgres_conn.py          # Postgres connection & setup helper
│   └── state_helper.py           # State helper functions
├── models/
│   ├── request_model.py          # InputModel - incoming chat messages
│   └── response_model.py         # ResponseModel - outgoing responses
└── prompts/                      # Agent prompt templates
    ├── aggregator.md
    ├── general.md
    ├── order.md
    ├── product.md
    ├── router.md
    └── prompt_loader.py
```