# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube Video Summarizer - A GenAI application that transforms YouTube videos into summaries, structured notes, translations, and recommendations using Groq's Llama 3.1 8B model with LangChain.

## Commands

### Run Streamlit Web App
```bash
streamlit run app_final.py
```
Access at http://localhost:8501

### Run FastAPI Backend
```bash
uvicorn app_api:app --reload --port 8000
```
Access at http://localhost:8000, docs at http://localhost:8000/docs

### Install Dependencies
```bash
pip install -r requirements.txt
```

## Architecture

### Dual Interface Pattern
- **`app_final.py`** (Streamlit): Interactive web UI with session state management for user-facing features
- **`app_api.py`** (FastAPI): REST API with Pydantic models for programmatic access

Both share the same core processing logic but are independent applications.

### Core Processing Flow
```
YouTube URL → YoutubeLoader (transcript) → LangChain summarize_chain → Groq LLM → Output
```

### Key Components
- **LLM**: `ChatGroq` with model `llama-3.1-8b-instant`
- **Transcript Extraction**: `YoutubeLoader` from langchain-community
- **Summarization**: `load_summarize_chain` with chain_type="stuff"
- **Video Search**: `YoutubeSearch` for recommendations

### API Endpoints (app_api.py)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/summarize` | POST | Generate video summary (requires youtube_url, groq_api_key) |
| `/translate` | POST | Translate summary (requires summary_text, target_language, groq_api_key) |
| `/notes` | POST | Generate structured notes (requires transcript_text, groq_api_key) |
| `/recommendations` | POST | Find similar videos (requires summary_text) |

### Session State (app_final.py)
Streamlit uses session state to persist: `summary`, `docs`, `translation_output`, `notes_output`, `recommendations_output`, `active_tab`, `theme`

## External Dependencies

- **Groq API Key**: Required, must start with `gsk_`. Get from https://console.groq.com
- **YouTube Transcripts**: Videos must have available transcripts/captions
