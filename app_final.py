import validators
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import YoutubeLoader
from youtube_search import YoutubeSearch
import re

# --------------------------- PAGE CONFIG ---------------------------
st.set_page_config(
    page_title="Video Summarizer 🎬",
    page_icon='https://cdn-icons-png.flaticon.com/512/1384/1384060.png',
    layout="wide"
)

# Initialize session state for utility outputs and theme control
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0
if 'theme' not in st.session_state:
    st.session_state.theme = "Light"  # Default theme
if 'summary' not in st.session_state:
    st.session_state.summary = ""
if 'docs' not in st.session_state:
    st.session_state.docs = []
if 'translation_output' not in st.session_state:
    st.session_state.translation_output = ""
if 'notes_output' not in st.session_state:
    st.session_state.notes_output = ""
if 'recommendations_output' not in st.session_state:
    st.session_state.recommendations_output = ""

# --- THEME DEFINITIONS (YouTube Aesthetic) ---
YOUTUBE_RED = "#FF0000"  # Defined for easy access

LIGHT_THEME_VARS = {
    "bg_color": "#ffffff",
    "text_color": "#0f0f0f",
    "link_color": "#065fd4",  # YouTube blue for links/highlights
    "youtube_red": YOUTUBE_RED,
    "card_bg": "#f1f1f1",  # Light Gray for feature cards
    "card_hover_bg": "#e5e5e5",
    "input_bg": "#ffffff",
    "input_border": "#cccccc",
    "divider_color": "#e5e5e5",
    # Result Boxes
    "blue_box_bg": "#e6f0ff",
    "blue_box_border": "#065fd4",
    "green_box_bg": "#e8fff0",
    "green_box_border": "#00a854",
    "orange_box_bg": "#fff5e6",
    "orange_box_border": "#ff8c00",
    # Tech Card Colors (New)
    "tech_card_bg": "#e0e0e0",
    "tech_card_hover_bg": "#d0d0d0",
    "tech_icon_color": "#0f0f0f"
}

DARK_THEME_VARS = {
    "bg_color": "#0f0f0f",  # Dark Black
    "text_color": "#ffffff",
    "link_color": "#3ea6ff",  # YouTube light blue for links/highlights
    "youtube_red": YOUTUBE_RED,
    "card_bg": "#282828",  # Dark Gray for feature cards
    "card_hover_bg": "#3f3f3f",
    "input_bg": "#121212",
    "input_border": "#3f3f3f",
    "divider_color": "#3f3f3f",
    # Result Boxes
    "blue_box_bg": "#1f2a40",
    "blue_box_border": "#60a5fa",
    "green_box_bg": "#1a3b2e",
    "green_box_border": "#34d399",
    "orange_box_bg": "#3d1f1f",
    "orange_box_border": "#fb923c",
    # Tech Card Colors (New)
    "tech_card_bg": "#1e1e1e",
    "tech_card_hover_bg": "#2a2a2a",
    "tech_icon_color": "#ffffff"
}

# Select the theme variables based on session state
THEME = LIGHT_THEME_VARS if st.session_state.theme == "Light" else DARK_THEME_VARS

# --------------------------- THEME & CSS ---------------------------
# Use f-strings to inject theme variables into the CSS
st.markdown(
    f"""
    <style>
    /* === GLOBAL === */
    .stApp {{
        background-color: {THEME['bg_color']}; /* Solid background now */
        font-family: 'Poppins', 'Roboto', sans-serif;
        color: {THEME['text_color']};
    }}
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}
    /* Adjust Streamlit components text color */
    .stMarkdown, .stText, .stLabel, .stCheckbox, .stSelectbox > div > label, 
    .stTextInput > label, .stRadio > label {{
        color: {THEME['text_color']} !important;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {THEME['text_color']} !important;
    }}

    /* --- YOUTUBE HEADER/LOGO --- */
    .youtube-header-logo {{
        display: flex;
        align-items: center;
        padding: 0 0 1rem 0; 
    }}
    .youtube-icon {{
        font-size: 2.2rem;
        color: {THEME['youtube_red']};
        margin-right: 5px;
    }}
    .youtube-title {{
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: -0.05em;
        color: {THEME['text_color']};
    }}
    .youtube-subtitle {{
        font-size: 1rem;
        color: {THEME['link_color']};
        margin-left: 10px;
        align-self: flex-end;
        padding-bottom: 5px;
        font-weight: 500;
    }}

    /* --- SEARCH BAR (st.text_input) STYLE --- */
    /* Target the container of the text input to style the "search bar" background and border */
    div[data-testid="stTextInput"] > div:first-child > div:first-child {{
        background-color: {THEME['input_bg']} !important;
        border: 1px solid {THEME['input_border']} !important;
        border-radius: 20px !important; /* Rounded corners like YouTube */
        padding: 5px 15px !important;
        box-shadow: none !important;
        transition: border-color 0.2s;
    }}
    div[data-testid="stTextInput"] > div:first-child > div:first-child:focus-within {{
        border: 1px solid {THEME['link_color']} !important;
    }}
    /* Style the text inside the input */
    div[data-testid="stTextInput"] input {{
        color: {THEME['text_color']} !important;
    }}


    /* === BUTTONS (Kept colorful/gradient for action) === */
    .stButton > button {{
        background: linear-gradient(90deg, #2563eb, #0ea5e9);
        color: white;
        border-radius: 8px;
        padding: 10px 22px;
        font-weight: 600;
        border: none;
        transition: all 0.25s ease;
    }}
    .stButton > button:hover {{
        transform: scale(1.03);
        box-shadow: 0 0 12px rgba(37,99,235,0.4);
    }}

    /* === FEATURE BOXES (Look like Suggested Videos) === */
    .feature-card {{
        background-color: {THEME['card_bg']};
        border-radius: 8px; /* Softer corners */
        padding: 1rem;
        box-shadow: none; /* Remove shadows for flat YouTube look */
        text-align: center;
        transition: background-color 0.2s ease-in-out;
        min-height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        color: {THEME['text_color']};
    }}
    .feature-card:hover {{
        transform: translateY(-4px);
        background-color: {THEME['card_hover_bg']};
        box-shadow: none;
    }}
    .feature-title {{
        color: {THEME['youtube_red']}; /* Highlight with YouTube Red */
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.4em;
    }}
    .feature-text {{
        color: {THEME['text_color']};
        font-size: 0.95rem;
    }}

    /* === RESULT BOXES (For Output) === */
    .result-box-blue, .result-box-green, .result-box-orange {{
        padding: 1rem;
        border-radius: 10px;
        margin-top: 1rem;
        color: {THEME['text_color']}; 
    }}
    .result-box-blue {{
        background-color: {THEME['blue_box_bg']};
        border-left: 5px solid {THEME['blue_box_border']};
    }}
    .result-box-green {{
        background-color: {THEME['green_box_bg']};
        border-left: 5px solid {THEME['green_box_border']};
    }}
    .result-box-orange {{
        background-color: {THEME['orange_box_bg']};
        border-left: 5px solid {THEME['orange_box_border']};
    }}

    /* Specific list styling for recommendations */
    .result-box-orange ul {{
        list-style-type: none;
        padding-left: 0;
        margin: 0.5rem 0 0 0;
    }}
    .result-box-orange li {{
        margin-bottom: 0.5rem;
    }}
    .result-box-orange a {{
        color: {THEME['link_color']}; /* Hyperlink color */
    }}

    /* Ensure Markdown lists within the green box render properly */
    .result-box-green ul, .result-box-green ol {{
        padding-left: 20px;
        margin-top: 0.5em;
    }}
    .result-box-green h2 {{
        margin-top: 1em !important;
        margin-bottom: 0.5em !important;
        font-size: 1.3rem !important;
    }}

    /* --- NEW TECH BOX STYLE --- */
    .tech-card {{
        background-color: {THEME['tech_card_bg']};
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        font-weight: 600;
        font-size: 1.1rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 80px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); /* Subtle shadow */
        transition: background-color 0.2s, transform 0.2s;
    }}
    .tech-card:hover {{
        background-color: {THEME['tech_card_hover_bg']};
        transform: translateY(-2px);
    }}
    .tech-icon {{
        font-size: 2.0rem;
        margin-bottom: 0.2rem;
        color: {THEME['tech_icon_color']};
    }}

    hr {{
        border: 0;
        border-top: 1px solid {THEME['divider_color']};
        margin: 1.5em 0;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------- SIDEBAR ---------------------------
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    groq_api_key = st.text_input("Groq API Key", type="password", value="")
    st.markdown("Get your key at [Groq Console](https://console.groq.com)")
    st.divider()

    st.markdown("#### 🧠 About This Project")
    st.info(
        "This project demonstrates how **LangChain** and **Groq LLM** can analyze YouTube content with blazing speed — turning long videos into actionable insights, notes, and translations."
    )

    st.markdown("### 🌐 Connect with Me")
    st.markdown(
        """
        <div style='display: flex; gap: 10px; flex-wrap: wrap;'>
            <a href='https://www.youtube.com/@avenkatesh0610' target='_blank'>
                <img src='https://cdn-icons-png.flaticon.com/512/1384/1384060.png' width='30' title='YouTube'/>
            </a>
            <a href='https://medium.com/@avenkatesh0610' target='_blank'>
                <img src='https://cdn-icons-png.flaticon.com/512/2111/2111505.png' width='30' title='Medium'/>
            </a>
            <a href='https://github.com/Venkatesh0610' target='_blank'>
                <img src='https://cdn-icons-png.flaticon.com/512/2111/2111432.png' width='30' title='GitHub'/>
            </a>
            <a href='https://www.linkedin.com/in/venkatesh-a-400459191/' target='_blank'>
                <img src='https://cdn-icons-png.flaticon.com/128/3536/3536505.png' width='30' title='LinkedIn'/>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- API KEY VALIDATION & LLM INITIALIZATION ---
valid_api_key = groq_api_key.startswith("gsk_")
llm = None
if valid_api_key:
    llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=groq_api_key)
# ----------------------------------------------


# --------------------------- YOUTUBE STYLE HEADER (ALWAYS VISIBLE) ---------------------------
st.markdown(f"""
<div class='youtube-header-logo'>
    <span class='youtube-icon'><img src='https://cdn-icons-png.flaticon.com/512/1384/1384060.png' width='30' title='YouTube'/></span>
    <span class='youtube-title'>YouTubeSummarizer</span>
    <span class='youtube-subtitle'>GENAI Tools</span>
</div>
<div class='hero-description'>Enter a YouTube video URL below to get an instant summary, notes, and recommendations.</div>
""", unsafe_allow_html=True)

st.markdown("---")

# --------------------------- MAIN SECTION (Conditional Input/Search Bar Area) ---------------------------

youtube_url = None # Initialize outside the if block

if valid_api_key:
    youtube_url = st.text_input("🎥 Video URL (Paste link here)", placeholder="e.g. https://youtube.com/watch?v=abcd1234")
else:
    st.info("🔑 Enter your valid **Groq API key** in the sidebar to enable video input and summarization.")

prompt_template = """
Provide a clear, concise summary (~300 words) of the following content:
{text}
"""
prompt = PromptTemplate(template=prompt_template, input_variables=["text"])

# --------------------------- SUMMARIZATION ---------------------------
# Only show the button and run the logic if the API key is valid
if valid_api_key:
    if st.button("🚀 Analyze & Summarize Video"):
        if not validators.url(youtube_url):
            st.error("❌ Please enter a valid YouTube URL.")
        else:
            # Clear previous utility outputs on new run
            st.session_state.translation_output = ""
            st.session_state.notes_output = ""
            st.session_state.recommendations_output = ""
            st.session_state.active_tab = 0

            with st.spinner("⏳ Fetching transcript and generating summary..."):
                try:
                    loader = YoutubeLoader.from_youtube_url(youtube_url, add_video_info=False)
                    docs = loader.load()
                    if not docs or not any(doc.page_content.strip() for doc in docs):
                        st.error("❌ No transcript content available for this video.")
                    else:
                        chain = load_summarize_chain(llm, chain_type="stuff", prompt=prompt)
                        summary = chain.run(docs)
                        st.session_state.summary = summary
                        st.session_state.docs = docs
                        st.success("✅ Summary generated successfully!")
                except Exception as e:
                    st.warning(f"⚠️ Unable to load transcript: {e}")

# --- RESULT SECTION (Conditional on session state, which requires the API key) ---
if st.session_state.summary:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🧾 Video Summary")
    st.info(st.session_state.summary, icon="🧠")
    st.divider()

    # --------------------------- UTILITIES ---------------------------
    tab1, tab2, tab3 = st.tabs(["🌐 Translate", "📝 Notes", "🎥 Recommendations"])

    # --- Translation ---
    with tab1:
        lang = st.selectbox("🌍 Choose target language", ["Hindi", "Spanish", "French", "German", "Tamil"], key='t_lang')


        def translate_action():
            st.session_state.active_tab = 0
            st.session_state.notes_output = ""
            st.session_state.recommendations_output = ""
            st.session_state.translation_output = ""


        if st.button(f"🔄 Translate to {lang}", on_click=translate_action):
            with st.spinner(f"Translating to {lang}..."):
                try:
                    t_prompt = PromptTemplate(
                        template="Translate the following English text to {target_language} naturally:\n{text}",
                        input_variables=["text", "target_language"],
                    )
                    result = llm.invoke(t_prompt.format(text=st.session_state.summary, target_language=lang))
                    st.session_state.translation_output = result.content.strip()
                except Exception as e:
                    st.warning(f"Translation failed: {e}")

        if st.session_state.translation_output:
            html_output = f"""
            <div class="result-box-blue">
                <b>🌍 Translated Summary ({lang})</b><br>
                {st.session_state.translation_output}
            </div>
            """
            st.markdown(html_output, unsafe_allow_html=True)

    # --- Notes ---
    with tab2:
        st.caption("Create detailed, structured notes from the original video content.")


        def notes_action():
            st.session_state.active_tab = 1
            st.session_state.translation_output = ""
            st.session_state.recommendations_output = ""
            st.session_state.notes_output = ""


        if st.button("🧠 Generate Structured Notes", on_click=notes_action, key='notes_btn'):
            with st.spinner("Creating structured notes..."):
                try:
                    # IMPROVED PROMPT FOR BETTER STRUCTURE AND RELIABILITY
                    n_prompt = PromptTemplate(
                        template="""
                        From the content provided below, create detailed, structured study notes.

                        **Strictly adhere to the following formatting rules, using Markdown for headings and lists.**

                        # 🔑 Key Topics
                        * List 3-5 main topics covered.

                        # 💡 Main Takeaways
                        * List 3 concise, most important takeaways.

                        # 📝 Detailed Insights
                        1. Use numbered list for detailed insights, explaining each point in a complete sentence.
                        2. Ensure at least 4 detailed insights are provided.

                        # 🚀 Actionable Steps
                        * List 2-3 specific actions a user can take based on the video content.

                        Generate the result in a proper format.
                        ---

                        Content to summarize:
                        {text}
                        """,
                        input_variables=["text"],
                    )
                    note_chain = load_summarize_chain(llm, chain_type="stuff", prompt=n_prompt)
                    notes = note_chain.run(st.session_state.docs)

                    st.session_state.notes_output = re.sub(r'\n\s*\n', '\n\n', notes).strip()
                except Exception as e:
                    st.warning(f"Note generation failed: {e}")

        if st.session_state.notes_output:
            html_output = f"""
            <div class="result-box-green">
                <b>🗒️ Structured Notes</b><br>
                {st.session_state.notes_output}
            </div>
            """
            st.markdown(html_output, unsafe_allow_html=True)

    # --- Recommendations ---
    with tab3:
        st.caption("Find similar video content on YouTube.")


        def recs_action():
            st.session_state.active_tab = 2
            st.session_state.translation_output = ""
            st.session_state.notes_output = ""
            st.session_state.recommendations_output = ""


        if st.button("🎯 Find Similar Videos", on_click=recs_action, key='recs_btn'):
            with st.spinner("Searching similar videos..."):
                try:
                    search_query = st.session_state.summary.split('.')[0][:80]
                    results = YoutubeSearch(search_query, max_results=5).to_dict()

                    # Build the content as HTML <ul><li> list for correct vertical rendering
                    recs_content_html = "<ul>"
                    if results:
                        for r in results:
                            # Function to safely extract the video ID and ensure a clean link
                            def extract_clean_url(suffix):
                                # Regex to find standard v=ID or shorts/ID
                                video_id_match = re.search(r'(v=|shorts\/)([a-zA-Z0-9_-]+)', suffix)

                                if video_id_match:
                                    video_id = video_id_match.group(2)
                                    return f"https://www.youtube.com/watch?v={video_id}"
                                return "#"  # Fallback if ID can't be extracted


                            clean_url = extract_clean_url(r['url_suffix'])

                            if clean_url != "#":
                                # Build HTML list item: <li>🎥 <a href="URL">Title</a></li>
                                recs_content_html += f"<li>🎥 <a href='{clean_url}'>{r['title']}</a></li>"
                            else:
                                recs_content_html += f"<li>🎥 {r['title']} (Link Error)</li>"

                    recs_content_html += "</ul>"
                    st.session_state.recommendations_output = recs_content_html
                except Exception as e:
                    st.warning(f"Could not fetch recommendations: {e}")

        if st.session_state.recommendations_output:
            # Inject the full HTML list into the custom box
            html_output = f"""
            <div class="result-box-orange">
                <b>🎬 Recommended Videos</b>
                {st.session_state.recommendations_output}
            </div>
            """
            st.markdown(html_output, unsafe_allow_html=True)
        elif st.session_state.active_tab == 2:
            st.info("No recommendations found based on the summary.")

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

# --------------------------- FEATURES (ALWAYS VISIBLE) ---------------------------
st.subheader("💡 Key Capabilities")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(
        "<div class='feature-card'><div class='feature-title'>⚡ Smart Summarization</div><div class='feature-text'>Summarizes lengthy YouTube transcripts into clear, digestible insights using Groq’s ultra-fast models.</div></div>",
        unsafe_allow_html=True)
with col2:
    st.markdown(
        "<div class='feature-card'><div class='feature-title'>🧠 Structured Notes</div><div class='feature-text'>Generates professional notes — key topics, insights, and takeaways ready for study or content reuse.</div></div>",
        unsafe_allow_html=True)
with col3:
    st.markdown(
        "<div class='feature-card'><div class='feature-title'>🌍 Multi-Language Translation</div><div class='feature-text'>Instantly translate summaries into popular global languages like Hindi, Spanish, or French.</div></div>",
        unsafe_allow_html=True)
with col4:
    st.markdown(
        "<div class='feature-card'><div class='feature-title'>🎬 Content Recommendations</div><div class='feature-text'>Discover similar YouTube videos relevant to your summarized topic.</div></div>",
        unsafe_allow_html=True)

# --------------------------- NEW: MAIN PACKAGES USED SECTION (ALWAYS VISIBLE) ---------------------------
st.divider()

st.subheader("🛠️ Main Technologies Used")
tech_col1, tech_col2, tech_col3, tech_col4 = st.columns(4)

# Tech Card HTML Structure: <div class='tech-card'><span class='tech-icon'>ICON</span>Package Name</div>

with tech_col1:
    st.markdown(
        "<div class='tech-card'><img src='https://images.seeklogo.com/logo-png/60/2/groq-icon-logo-png_seeklogo-605779.png' width='30'/>Groq</div>",
        unsafe_allow_html=True
    )

with tech_col2:
    st.markdown(
        "<div class='tech-card'><img src='https://logo.svgcdn.com/simple-icons/langchain-dark.png' width='30'/>LangChain</div>",
        unsafe_allow_html=True
    )

with tech_col3:
    st.markdown(
        "<div class='tech-card'><img src='https://images.seeklogo.com/logo-png/44/2/streamlit-logo-png_seeklogo-441815.png' width='30'/>Streamlit</div>",
        unsafe_allow_html=True
    )


with tech_col4:
    st.markdown(
        "<div class='tech-card'><img src='https://cdn-icons-png.flaticon.com/512/14/14373.png' width='30'/>YoutubeSearch</div>",
        unsafe_allow_html=True
    )
# ---------------------------------------------------------------------------------------

st.markdown("<br>", unsafe_allow_html=True)