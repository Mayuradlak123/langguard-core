# 🛡️ LangGuard Core

**LangGuard Core** is a production-grade Python framework designed for building **resilient**, **stateful**, and **grounded** AI agents. It eliminates LLM hallucinations by enforcing a strict anti-hallucination pipeline powered by LangGraph.

[![PyPI version](https://badge.fury.io/py/langguard-core.svg)](https://badge.fury.io/py/langguard-core)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Key Features

- **6-Stage Anti-Hallucination Pipeline**: A robust workflow consisting of Query Rewriting, Hybrid Retrieval, Reranking, Grounded Generation, Verification, and Guardrails.
- **Truth Verification**: Automated grounding scores that cross-reference AI responses with source context to ensure zero hallucinations.
- **Resilience Engineering**: Built-in **Circuit Breakers** for LLMs and Databases to prevent cascading failures in production.
- **Hybrid Retrieval**: Native support for parallel retrieval from **ChromaDB** (Semantic) and **Neo4j** (Graph).
- **Stateful Memory**: Powered by LangGraph's persistent checkpointers to maintain conversational context across sessions.

---

## 📦 Installation

Install the core package via pip:

```bash
pip install langguard-core
```

---

## ⚡ Quick Start

LangGuard is designed to be integrated into any application with just a few lines of code.

```python
import chromadb
from langguard import LangGuardPipeline

# 1. Initialize your database clients
chroma_client = chromadb.HttpClient(host='localhost', port=8000)
# (Optionally) Initialize your Neo4j manager

# 2. Build the production pipeline
pipeline = LangGuardPipeline(
    chroma_client=chroma_client,
    neo4j_manager=None # Or pass your neo4j manager
)

# 3. Invoke the grounded agent
async def ask_ai():
    async for event in pipeline.astream("What is the impact of LLMs on system design?"):
        print(event)
```

---

## 🏗️ Production Architecture

The library implements a specialized pipeline to ensure every response is verified:

1.  **🔍 Query Rewriter**: Optimizes user input for high-performance retrieval.
2.  **📚 Retriever**: Fetches data in parallel from Vector and Graph databases.
3.  **⚖️ Reranker**: Filters out irrelevant context "noise."
4.  **🤖 Generator**: Produces a response based *only* on the verified context.
5.  **✅ Verifier**: Calculates a **Grounding Score** (0.0 - 1.0).
6.  **🛡️ Guardrails**: Blocks responses if the grounding score falls below the safety threshold (default: 0.6).

---

## ⚙️ Configuration

The package relies on the following environment variables. Create a `.env` file in your project root:

```env
# --- LLM Provider (Groq) ---
GROQ_API_KEY=your_groq_api_key

# --- Remote Vector Database (ChromaDB Cloud) ---
CHROMA_API_KEY=your_chroma_cloud_api_key
CHROMA_TENANT=your_chroma_tenant_id
CHROMA_DATABASE=your_database_name

# --- Graph Database (Neo4j Aura) ---
NEO4J_URI=your_neo4j_uri
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password

# --- Search Tool (Optional) ---
TAVILY_API_KEY=your_tavily_api_key
```

---

## 🛡️ Resilience (Circuit Breakers)
The system monitors the health of external services. If Neo4j, ChromaDB, or Groq becomes unresponsive, the **Circuit Breaker** will open, preventing system-wide crashes and returning a controlled fallback response.

---

## 🤝 Contributing

We welcome contributions! Please feel free to submit a Pull Request or open an issue on the [GitHub Repository](https://github.com/Mayuradlak123/langguard-core).

---
*Built with ❤️ for the AI Engineering Community.*
