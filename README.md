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
   
   Create a `.secrets.toml` file in the project root with your Groq API key:
   ```toml
   [default]
   GROQ_API_KEY = "your-groq-api-key-here"
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
  "message": "What services does CloudForge Systems offer?"
}
```

**Response:**
```json
{
  "response": "CloudForge Systems offers: - Cloud migration and infrastructure consulting - Custom software development - AI/ML solution implementation - DevOps automation and CI/CD pipeline setup - Enterprise application modernization"
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
├── app.py                    # FastAPI application and endpoints
├── graph.py                  # LangGraph workflow and chatbot agent
├── config.py                 # Configuration management (Dynaconf)
├── requirements.txt          # Python dependencies
├── .secrets.toml             # Configuration secrets (create this - add to .gitignore)
│
└── models/
    ├── request_model.py      # InputModel - incoming chat messages
    └── response_model.py     # ResponseModel - outgoing responses
```