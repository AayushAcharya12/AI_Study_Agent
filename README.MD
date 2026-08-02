# 📚 AI Study Agent

An AI-powered study assistant built with **LangGraph** and **Streamlit**. Upload your notes, ask questions, and get answers grounded in your own material — backed up by live web search and YouTube video recommendations when needed.

## Features

- **📄 Document Q&A (RAG)** — Upload PDF, DOCX, TXT, CSV, or MD files. The agent retrieves relevant chunks from a persistent Chroma vector store to ground its answers.
- **🌐 Web Search** — Falls back to Tavily search for current events, recent updates, or anything not covered in uploaded material.
- **▶️ YouTube Recommendations** — Suggests real educational videos (with thumbnails) when the user asks for tutorials or video explanations.
- **🧠 Multi-LLM Fallback Chain** — Automatically switches between Groq (Llama 3.3 70B, Qwen 32B) and Gemini if one provider is rate-limited or unavailable, so the agent stays responsive.
- **💬 Persistent Chat Sessions** — Conversation history is checkpointed per session via SQLite, so context isn't lost between turns.
- **🔊 Text-to-Speech** — Listen to responses using Edge TTS, including Nepali voice support.
- **🔎 Transparent Reasoning** — An optional "Show agent steps" view lets users see which tool the agent used and why.

## Tech Stack

`LangGraph` · `LangChain` · `Streamlit` · `Groq` · `Gemini` · `Tavily` · `ChromaDB` · `HuggingFace Embeddings` · `YouTube Data API` · `Edge TTS`

## Status

This project is actively being developed. Planned upgrades include:

### Retrieval & Knowledge Base
- Session-scoped document isolation, so one user's uploads don't leak into another session's answers
- A proper "clear knowledge base" control instead of relying on manual vector-store resets
- Support for larger documents and more file types

### Reliability
- Additional LLM fallback providers beyond Groq/Gemini for better uptime
- Retry-with-backoff on transient rate limits before cascading to a fallback provider
- Better handling of token/context limits on longer conversations (auto-trimming chat history)

### Agent Quality
- More consistent tool selection (reducing cases where the agent answers from memory instead of calling the right tool)
- Improved, more reliable confidence scoring and source attribution
- Better multi-source answer formatting (documents + web + video combined cleanly)

### UI / UX
- Polished chat interface with clearer tool-usage indicators
- More robust YouTube video card rendering (thumbnails, direct links)
- Expanded text-to-speech language/voice options

**Deployment is planned** for a future release — the app currently runs locally via Streamlit, with hosted deployment to follow once the above upgrades are complete.

## Running Locally

```bash
streamlit run src/app.py
```

Requires a `.env` file with `GROQ_API`, `TAVILY_API`, `YOUTUBE_API`, and `GOOGLE_API` keys.

## Author

Built by **Aayush Acharya**.