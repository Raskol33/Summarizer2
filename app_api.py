from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import YoutubeLoader
from youtube_search import YoutubeSearch
import validators
import re
from langchain.schema import Document

# --------------------------- APP CONFIG ---------------------------
app = FastAPI(
    title="YouTube Summarizer API 🎬",
    description="Analyze and summarize YouTube videos using LangChain + Groq LLMs.",
    version="1.0.0",
)

# --------------------------- REQUEST MODELS ---------------------------
class SummarizeRequest(BaseModel):
    youtube_url: str
    groq_api_key: str


class TranslateRequest(BaseModel):
    summary_text: str
    target_language: str
    groq_api_key: str


class NotesRequest(BaseModel):
    transcript_text: str
    groq_api_key: str


class RecommendationsRequest(BaseModel):
    summary_text: str


# --------------------------- CORE UTILS ---------------------------
def init_llm(api_key: str):
    """Initialize the ChatGroq model."""
    if not api_key.startswith("gsk_"):
        raise HTTPException(status_code=400, detail="Invalid Groq API key.")
    return ChatGroq(model="llama-3.1-8b-instant", groq_api_key=api_key)


# --------------------------- ENDPOINT: Summarize ---------------------------
@app.post("/summarize")
async def summarize_video(req: SummarizeRequest):
    """Fetch transcript from YouTube and generate summary."""
    if not validators.url(req.youtube_url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL.")

    llm = init_llm(req.groq_api_key)

    try:
        loader = YoutubeLoader.from_youtube_url(req.youtube_url, add_video_info=False)
        docs = loader.load()
        if not docs or not any(doc.page_content.strip() for doc in docs):
            raise HTTPException(status_code=404, detail="No transcript found for this video.")

        prompt_template = """
        Provide a clear, concise summary (~300 words) of the following content:
        {text}
        """
        prompt = PromptTemplate(template=prompt_template, input_variables=["text"])
        chain = load_summarize_chain(llm, chain_type="stuff", prompt=prompt)
        summary = chain.run(docs)
        return {"summary": summary.strip()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {e}")


# --------------------------- ENDPOINT: Translate ---------------------------
@app.post("/translate")
async def translate_summary(req: TranslateRequest):
    """Translate summary text to a target language."""
    llm = init_llm(req.groq_api_key)
    try:
        prompt = PromptTemplate(
            template="Translate the following English text to {target_language} naturally:\n{text}",
            input_variables=["text", "target_language"],
        )
        result = llm.invoke(prompt.format(text=req.summary_text, target_language=req.target_language))
        return {"translation": result.content.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {e}")


# --------------------------- ENDPOINT: Notes ---------------------------
@app.post("/notes")
async def generate_notes(req: NotesRequest):
    """Generate detailed study notes from transcript text."""
    llm = init_llm(req.groq_api_key)
    try:
        notes_prompt = PromptTemplate(
            template="""
            From the content provided below, create detailed, structured study notes.

            # 🔑 Key Topics
            * 3–5 main topics covered.

            # 💡 Main Takeaways
            * 3 concise takeaways.

            # 📝 Detailed Insights
            1. Provide detailed numbered insights.

            # 🚀 Actionable Steps
            * 2–3 actions a viewer can take.

            Content:
            {text}
            """,
            input_variables=["text"],
        )

        # ✅ Wrap transcript text into a LangChain Document object
        docs = [Document(page_content=req.transcript_text)]

        # Create summarization chain
        chain = load_summarize_chain(llm, chain_type="stuff", prompt=notes_prompt)

        # Run the chain properly
        notes = chain.run(docs)

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
