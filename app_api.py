from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import YoutubeLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from youtube_search import YoutubeSearch
import validators
import re
from langchain.schema import Document
from llm_factory import create_llm, validate_api_key, get_default_model

# --------------------------- APP CONFIG ---------------------------
app = FastAPI(
    title="YouTube Summarizer API 🎬",
    description="Analyze and summarize YouTube videos using LangChain + Groq LLMs.",
    version="1.0.0",
)

# --------------------------- REQUEST MODELS ---------------------------
class SummarizeRequest(BaseModel):
    youtube_url: str
    provider: str = "groq"  # Default to Groq for backward compatibility
    api_key: str = None
    model: str = None  # Uses default if None
    # For Ollama only
    ollama_url: str = "http://localhost:11434"
    # Backward compatibility
    groq_api_key: str = None  # Deprecated, use api_key

    def __init__(self, **data):
        # Migrate groq_api_key → api_key for backward compatibility
        if data.get('groq_api_key') and not data.get('api_key'):
            data['api_key'] = data['groq_api_key']
            data['provider'] = 'groq'
        super().__init__(**data)


class TranslateRequest(BaseModel):
    summary_text: str
    target_language: str
    provider: str = "groq"
    api_key: str = None
    model: str = None
    ollama_url: str = "http://localhost:11434"
    groq_api_key: str = None  # Deprecated

    def __init__(self, **data):
        if data.get('groq_api_key') and not data.get('api_key'):
            data['api_key'] = data['groq_api_key']
            data['provider'] = 'groq'
        super().__init__(**data)


class NotesRequest(BaseModel):
    transcript_text: str
    provider: str = "groq"
    api_key: str = None
    model: str = None
    ollama_url: str = "http://localhost:11434"
    groq_api_key: str = None  # Deprecated

    def __init__(self, **data):
        if data.get('groq_api_key') and not data.get('api_key'):
            data['api_key'] = data['groq_api_key']
            data['provider'] = 'groq'
        super().__init__(**data)


class RecommendationsRequest(BaseModel):
    summary_text: str
    # No LLM needed for recommendations


# --------------------------- CORE UTILS ---------------------------
def init_llm(provider: str, api_key: str = None, model: str = None, **kwargs):
    """
    Initialize LLM based on provider.

    Args:
        provider: "groq", "openai", "claude", "mistral", or "ollama"
        api_key: API key (not needed for Ollama)
        model: Model name (uses default if None)
        **kwargs: Provider-specific params (e.g., ollama_url)

    Returns:
        Configured LLM instance

    Raises:
        HTTPException: If validation fails
    """
    try:
        # Ollama doesn't require API key
        if provider == "ollama":
            base_url = kwargs.get('ollama_url', 'http://localhost:11434')
            model = model or get_default_model("ollama")
            return create_llm("ollama", model=model, base_url=base_url)

        # Other providers: validate API key
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail=f"API key required for {provider.upper()}"
            )

        if not validate_api_key(provider, api_key):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {provider.upper()} API key format"
            )

        # Use default model if not specified
        model = model or get_default_model(provider)

        return create_llm(provider, api_key=api_key, model=model)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM initialization failed: {str(e)}"
        )


# --------------------------- ENDPOINT: Summarize ---------------------------
@app.post("/summarize")
async def summarize_video(req: SummarizeRequest):
    """Fetch transcript from YouTube and generate summary."""
    if not validators.url(req.youtube_url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL.")

    llm = init_llm(
        provider=req.provider,
        api_key=req.api_key,
        model=req.model,
        ollama_url=req.ollama_url
    )

    try:
        loader = YoutubeLoader.from_youtube_url(
            req.youtube_url,
            add_video_info=False,
            language=['fr', 'en', 'es', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh-Hans', 'ar', 'hi', 'nl', 'pl', 'tr', 'sv', 'no', 'da', 'fi']
        )
        docs = loader.load()
        if not docs or not any(doc.page_content.strip() for doc in docs):
            raise HTTPException(status_code=404, detail="No transcript found for this video.")

        # Get the full transcript text
        full_text = " ".join([doc.page_content for doc in docs])

        # Map prompt for individual chunks
        map_prompt_template = """
        CRITICAL INSTRUCTION: You MUST write your summary in the SAME LANGUAGE as the content below. If the content is in French, write in French. If in English, write in English. DO NOT switch languages.

        Provide a detailed summary of the following content section. Capture all key points, important details, and main ideas:

        {text}

        DETAILED SUMMARY (in the same language as the content above):
        """
        map_prompt = PromptTemplate(template=map_prompt_template, input_variables=["text"])

        # Combine prompt for final summary
        combine_prompt_template = """
        CRITICAL INSTRUCTION: You MUST write your final summary in the SAME LANGUAGE as the summaries below. DO NOT translate or switch languages. Maintain the original language throughout.

        You are given multiple summaries from different sections of a video. Combine them into one comprehensive, well-structured summary.

        Section summaries:
        {text}

        FINAL COMPREHENSIVE SUMMARY (in the same language as above):
        """
        combine_prompt = PromptTemplate(template=combine_prompt_template, input_variables=["text"])

        # Simple chunking - reduced size to respect Groq API limits
        chunk_size = 1200
        chunks = []
        for i in range(0, len(full_text), chunk_size):
            chunk = full_text[i:i + chunk_size]
            chunks.append(chunk)

        # If the text is short enough, summarize directly
        if len(full_text) < 2000:
            result = llm.invoke(map_prompt.format(text=full_text))
            summary = result.content.strip()
        else:
            # Summarize each chunk
            import time
            chunk_summaries = []
            for idx, chunk in enumerate(chunks):
                try:
                    result = llm.invoke(map_prompt.format(text=chunk))
                    chunk_summaries.append(result.content.strip())
                    # Add delay to avoid rate limits
                    if idx < len(chunks) - 1:
                        time.sleep(0.5)
                except Exception as e:
                    if "rate_limit" in str(e).lower():
                        time.sleep(5)
                        result = llm.invoke(map_prompt.format(text=chunk))
                        chunk_summaries.append(result.content.strip())
                    else:
                        raise e

            # Combine all summaries
            combined_text = "\n\n".join(chunk_summaries)

            # If combined summaries are still long, summarize again
            if len(combined_text) > 2000:
                # Recursively summarize the summaries
                final_chunks = []
                for i in range(0, len(combined_text), 1200):
                    final_chunks.append(combined_text[i:i + 1200])

                final_summaries = []
                for idx, chunk in enumerate(final_chunks):
                    result = llm.invoke(combine_prompt.format(text=chunk))
                    final_summaries.append(result.content.strip())
                    if idx < len(final_chunks) - 1:
                        time.sleep(0.5)

                summary = " ".join(final_summaries)
            else:
                result = llm.invoke(combine_prompt.format(text=combined_text))
                summary = result.content.strip()
        return {"summary": summary.strip()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {e}")


# --------------------------- ENDPOINT: Translate ---------------------------
@app.post("/translate")
async def translate_summary(req: TranslateRequest):
    """Translate summary text to a target language."""
    llm = init_llm(
        provider=req.provider,
        api_key=req.api_key,
        model=req.model,
        ollama_url=req.ollama_url
    )
    try:
        prompt = PromptTemplate(
            template="Translate the following text to {target_language} naturally and accurately. Preserve the meaning, tone, and structure:\n{text}",
            input_variables=["text", "target_language"],
        )

        # For long texts, chunk and translate
        if len(req.summary_text) > 2000:
            chunk_size = 1200
            chunks = []
            for i in range(0, len(req.summary_text), chunk_size):
                chunks.append(req.summary_text[i:i + chunk_size])

            import time
            translated_chunks = []
            for idx, chunk in enumerate(chunks):
                try:
                    result = llm.invoke(prompt.format(text=chunk, target_language=req.target_language))
                    translated_chunks.append(result.content.strip())
                    # Add delay to avoid rate limits
                    if idx < len(chunks) - 1:
                        time.sleep(1)
                except Exception as e:
                    if "rate_limit" in str(e).lower():
                        time.sleep(5)
                        result = llm.invoke(prompt.format(text=chunk, target_language=req.target_language))
                        translated_chunks.append(result.content.strip())
                    else:
                        raise e

            translation = " ".join(translated_chunks)
        else:
            result = llm.invoke(prompt.format(text=req.summary_text, target_language=req.target_language))
            translation = result.content.strip()

        return {"translation": translation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {e}")


# --------------------------- ENDPOINT: Notes ---------------------------
@app.post("/notes")
async def generate_notes(req: NotesRequest):
    """Generate detailed study notes from transcript text."""
    llm = init_llm(
        provider=req.provider,
        api_key=req.api_key,
        model=req.model,
        ollama_url=req.ollama_url
    )
    try:
        # Prompt for extracting key info from chunks
        chunk_prompt_template = """
        Extract key information from the following content section.
        List the main topics, important points, and insights.

        Content:
        {text}

        Key information:
        """

        # Final notes prompt
        notes_prompt_template = """
        From the information provided below, create detailed, structured study notes.

        **Strictly adhere to the following formatting rules, using Markdown for headings and lists.**

        # 🔑 Key Topics
        * List 3-5 main topics covered.

        # 💡 Main Takeaways
        * List 3 concise, most important takeaways.

        # 📝 Detailed Insights
        1. Use numbered list for detailed insights, explaining each point in a complete sentence.
        2. Ensure at least 4 detailed insights are provided.

        # 🚀 Actionable Steps
        * List 2-3 specific actions a user can take based on the content.

        Generate the result in a proper format.
        ---

        Information to organize:
        {text}
        """

        full_text = req.transcript_text

        # For long texts, use chunking
        if len(full_text) > 2000:
            chunk_size = 1200
            chunks = []
            for i in range(0, len(full_text), chunk_size):
                chunks.append(full_text[i:i + chunk_size])

            # Extract key info from each chunk
            import time
            chunk_prompt = PromptTemplate(template=chunk_prompt_template, input_variables=["text"])
            chunk_summaries = []
            for idx, chunk in enumerate(chunks):
                try:
                    result = llm.invoke(chunk_prompt.format(text=chunk))
                    chunk_summaries.append(result.content.strip())
                    # Add delay to avoid rate limits
                    if idx < len(chunks) - 1:
                        time.sleep(1)
                except Exception as e:
                    if "rate_limit" in str(e).lower():
                        time.sleep(5)
                        result = llm.invoke(chunk_prompt.format(text=chunk))
                        chunk_summaries.append(result.content.strip())
                    else:
                        raise e

            # Combine all key info
            combined_text = "\n\n".join(chunk_summaries)

            # If combined text is still too long, chunk it again
            if len(combined_text) > 2000:
                final_chunks = []
                for i in range(0, len(combined_text), 1200):
                    final_chunks.append(combined_text[i:i + 1200])

                # Summarize the summaries
                mini_summaries = []
                for idx, chunk in enumerate(final_chunks):
                    result = llm.invoke(chunk_prompt.format(text=chunk))
                    mini_summaries.append(result.content.strip())
                    if idx < len(final_chunks) - 1:
                        time.sleep(1)

                combined_text = "\n\n".join(mini_summaries)

            # Generate final structured notes
            notes_prompt = PromptTemplate(template=notes_prompt_template, input_variables=["text"])
            result = llm.invoke(notes_prompt.format(text=combined_text))
            notes = result.content.strip()
        else:
            # For short texts, generate notes directly
            notes_prompt = PromptTemplate(template=notes_prompt_template, input_variables=["text"])
            result = llm.invoke(notes_prompt.format(text=full_text))
            notes = result.content.strip()

        # Clean extra whitespace or blank lines
        clean_notes = re.sub(r"\n\s*\n", "\n\n", notes).strip()

        return {"notes": clean_notes}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notes generation failed: {e}")


# --------------------------- ENDPOINT: Recommendations ---------------------------
@app.post("/recommendations")
async def get_recommendations(req: RecommendationsRequest):
    """Search similar videos on YouTube."""
    try:
        search_query = req.summary_text.split('.')[0][:80]
        results = YoutubeSearch(search_query, max_results=5).to_dict()

        recs = []
        for r in results:
            match = re.search(r"(v=|shorts/)([a-zA-Z0-9_-]+)", r.get("url_suffix", ""))
            video_id = match.group(2) if match else None
            if video_id:
                recs.append({
                    "title": r["title"],
                    "url": f"https://www.youtube.com/watch?v={video_id}"
                })

        return {"recommendations": recs}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation fetch failed: {e}")


# --------------------------- HEALTH CHECK ---------------------------
@app.get("/")
async def home():
    return {"message": "🎬 YouTube Summarizer API is running!"}
