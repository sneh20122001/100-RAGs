# Web RAG Flask App

This Flask app uses LangChain with Google Gemini and ChromaDB to perform Retrieval-Augmented Generation (RAG) from web data.

## Features

- Web scraping using `WebBaseLoader`
- Embedding with `GoogleGenerativeAIEmbeddings`
- Vector storage with ChromaDB
- Gemini 2.0 LLM via LangChain
- Flask API to ask RAG-powered questions

## API

### POST `/ask`

**Request Body:**
```json
{
  "question": "Is there doubt support?"
}
