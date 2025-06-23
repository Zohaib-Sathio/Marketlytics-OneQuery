
# 🔍 RAG System with Google Drive, Gmail, and Slack Integration

This project is a **Retrieval-Augmented Generation (RAG)** system that allows users to query and generate intelligent answers from their personal or organizational data sources: **Google Drive**, **Gmail**, and **Slack**. The system integrates document retrieval from multiple platforms, performs chunking, embeddings, vector storage, and uses LLMs to generate responses with strong context awareness.

---

## 🚀 Features

- ✅ **Google Drive Integration** – Fetch documents, PDFs, Google Docs and extract content for semantic search.
- ✅ **Gmail Integration** – Parse and retrieve relevant email content to power context-aware responses.
- ✅ **Slack Integration** – Extract messages from specific channels and threads for use in semantic memory.
- ✅ **ChromaDB + LangChain** – Store embeddings and enable fast vector search.
- ✅ **Multi-modal Input Sources** – Combine unstructured text from multiple sources into one RAG pipeline.
- ✅ **LLM-Powered Answers** – Query over your documents using Large Language Models (LLMs) via LangChain.
- ✅ **FastAPI + Streamlit Interface (Optional)** – Interact with the system via API or web UI.

---

## 🧠 Architecture Overview

```mermaid
flowchart TD
    A[User Query] --> B[Retriever]
    B --> C1[Google Drive Vector DB]
    B --> C2[Gmail Vector DB]
    B --> C3[Slack Vector DB]
    C1 --> D[Relevant Docs]
    C2 --> D
    C3 --> D
    D --> E[LLM via LangChain]
    E --> F[Response]
```

---

## 📂 Folder Structure

```
📁 RAG-System
│
├── backend/
│   ├── drive_ingestion.py
│   ├── gmail_ingestion.py
│   ├── slack_ingestion.py
│   ├── vector_store.py
│   ├── rag_engine.py
│   └── api.py
│
├── frontend/
│   ├── app.py  # Streamlit app (optional)
│
├── .env
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup & Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/yourusername/rag-multi-source.git
   cd rag-multi-source
   ```

2. **Create `.env` file** with the following keys:
   ```
   GOOGLE_API_KEY=...
   GMAIL_CLIENT_SECRET=...
   SLACK_BOT_TOKEN=...
   GEMINI_API_KEY=...
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Authenticate Google & Slack APIs**
   - Follow OAuth setup for Google Drive and Gmail.
   - Add the bot to Slack channels manually or via API.

5. **Run the backend API**
   ```bash
   uvicorn backend.api:app --reload
   ```

6. *(Optional)* Run Streamlit UI:
   ```bash
   streamlit run frontend/app.py
   ```

---

## 🧪 How It Works

1. **Ingestion Pipelines**:
   - Google Drive: Extracts text from docs and PDFs.
   - Gmail: Parses emails with filters like sender, date, etc.
   - Slack: Pulls conversations from selected channels.

2. **Chunking & Embeddings**:
   - Uses LangChain text splitters and Google Embeddings (or OpenAI).
   - Stored in ChromaDB vector store.

3. **RAG Retrieval**:
   - Query is embedded and matched against vector stores.
   - Top relevant chunks are passed to the LLM for response generation.

---

## 📤 APIs

- `POST /query`  
  Send a user query and receive a response using data from integrated sources.

- `POST /ingest`  
  Ingest data from a selected source (drive, gmail, slack).

---

## 🛠️ Technologies Used

- Python
- LangChain
- ChromaDB
- Google API (Drive, Gmail)
- Slack SDK
- FastAPI
- Streamlit (optional)
- Gemini / OpenAI LLMs

---

---

## 🙌 Contributors

- **Zohaib** –
