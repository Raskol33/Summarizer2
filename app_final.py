import validators
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import YoutubeLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from youtube_search import YoutubeSearch
import re
import os
import json
from datetime import datetime

# --------------------------- API KEY PERSISTENCE ---------------------------
CONFIG_FILE = "config.json"

def load_api_key():
    """Load API key from config file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return config.get("groq_api_key", "")
        except:
            return ""
    return ""

def save_api_key(api_key):
    """Save API key to config file."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"groq_api_key": api_key}, f)
        return True
    except:
        return False

def save_file_with_dialog(content, default_filename):
    """Save file using system dialog (tkinter)."""
    try:
        from tkinter import Tk, filedialog

        # Create a Tk root window (hidden)
        root = Tk()
        root.withdraw()
        root.wm_attributes('-topmost', 1)

        # Open file dialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=default_filename,
            filetypes=[
                ("Text files", "*.txt"),
                ("Markdown files", "*.md"),
                ("All files", "*.*")
            ]
        )

        # Save file if user didn't cancel
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            root.destroy()
            return True, file_path

        root.destroy()
        return False, None

    except Exception as e:
        return False, str(e)

# --------------------------- TRANSLATIONS ---------------------------
TRANSLATIONS = {
    "English": {
        "page_title": "Video Summarizer 🎬",
        "config": "Configuration",
        "api_key": "Groq API Key",
        "get_key": "Get your key at",
        "save_key": "Save API Key",
        "clear": "Clear",
        "about": "About This Project",
        "about_text": "This project demonstrates how **LangChain** and **Groq LLM** can analyze YouTube content with blazing speed — turning long videos into actionable insights, notes, and translations.",
        "connect": "Connect with Me",
        "header_title": "YouTubeSummarizer",
        "header_subtitle": "GENAI Tools",
        "header_desc": "Enter a YouTube video URL below to get an instant summary, notes, and recommendations.",
        "video_url": "🎥 Video URL (Paste link here)",
        "url_placeholder": "e.g. https://youtube.com/watch?v=abcd1234",
        "enter_api_key": "🔑 Enter your valid **Groq API key** in the sidebar to enable video input and summarization.",
        "analyze_btn": "🚀 Analyze & Summarize Video",
        "invalid_url": "❌ Please enter a valid YouTube URL.",
        "fetching": "⏳ Fetching transcript and generating summary...",
        "no_transcript": "❌ No transcript content available for this video.",
        "success": "✅ Summary generated successfully!",
        "error": "⚠️ Unable to load transcript:",
        "summary_title": "🧾 Video Summary",
        "edit_btn": "✏️ Edit",
        "save_btn": "💾 Save",
        "edit_summary": "Edit your summary:",
        "export_title": "📥 Export Options",
        "export_summary": "📄 Export Summary",
        "export_notes": "📝 Export Notes",
        "export_translation": "🌐 Export Translation",
        "export_recommendations": "🎬 Export Recommendations",
        "file_name": "📝 File name",
        "format": "Format",
        "quick_download": "⬇️ Quick Download",
        "quick_download_help": "Download to your default Downloads folder",
        "save_as": "📁 Save As...",
        "save_as_help": "Choose where to save the file",
        "file_saved": "✅ File saved to:",
        "save_cancelled": "ℹ️ Save cancelled",
        "tab_translate": "🌐 Translate",
        "tab_notes": "📝 Notes",
        "tab_recommendations": "🎥 Recommendations",
        "choose_language": "🌍 Choose target language",
        "translate_btn": "🔄 Translate to",
        "translating": "Translating to",
        "translation_failed": "Translation failed:",
        "translated_summary": "🌍 Translated Summary",
        "notes_caption": "Create detailed, structured notes from the original video content.",
        "generate_notes_btn": "🧠 Generate Structured Notes",
        "creating_notes": "Creating structured notes...",
        "notes_failed": "Note generation failed:",
        "structured_notes": "🗒️ Structured Notes",
        "edit_notes": "Edit your notes:",
        "recs_caption": "Find similar video content on YouTube.",
        "find_videos_btn": "🎯 Find Similar Videos",
        "searching_videos": "Searching similar videos...",
        "recs_failed": "Could not fetch recommendations:",
        "recommended_videos": "🎬 Recommended Videos",
        "no_recs": "No recommendations found based on the summary.",
        "features_title": "💡 Key Capabilities",
        "feature1_title": "⚡ Smart Summarization",
        "feature1_text": "Summarizes lengthy YouTube transcripts into clear, digestible insights using Groq's ultra-fast models.",
        "feature2_title": "🧠 Structured Notes",
        "feature2_text": "Generates professional notes — key topics, insights, and takeaways ready for study or content reuse.",
        "feature3_title": "🌍 Multi-Language Translation",
        "feature3_text": "Instantly translate summaries into 14+ languages including English, French, Spanish, German, Arabic, Chinese, Japanese and more.",
        "feature4_title": "🎬 Content Recommendations",
        "feature4_text": "Discover similar YouTube videos relevant to your summarized topic.",
        "tech_title": "🛠️ Main Technologies Used",
        "ui_language": "🌐 Interface Language"
    },
    "Français": {
        "page_title": "Résumeur de Vidéos 🎬",
        "config": "Configuration",
        "api_key": "Clé API Groq",
        "get_key": "Obtenez votre clé sur",
        "save_key": "Sauvegarder la clé",
        "clear": "Effacer",
        "about": "À propos",
        "about_text": "Ce projet démontre comment **LangChain** et **Groq LLM** peuvent analyser le contenu YouTube à une vitesse fulgurante — transformant de longues vidéos en insights, notes et traductions exploitables.",
        "connect": "Me contacter",
        "header_title": "RésumeurYouTube",
        "header_subtitle": "Outils GENAI",
        "header_desc": "Entrez une URL de vidéo YouTube ci-dessous pour obtenir un résumé instantané, des notes et des recommandations.",
        "video_url": "🎥 URL de la vidéo (Collez le lien ici)",
        "url_placeholder": "ex. https://youtube.com/watch?v=abcd1234",
        "enter_api_key": "🔑 Entrez votre **clé API Groq** valide dans la barre latérale pour activer l'analyse vidéo.",
        "analyze_btn": "🚀 Analyser et Résumer la Vidéo",
        "invalid_url": "❌ Veuillez entrer une URL YouTube valide.",
        "fetching": "⏳ Récupération de la transcription et génération du résumé...",
        "no_transcript": "❌ Aucune transcription disponible pour cette vidéo.",
        "success": "✅ Résumé généré avec succès !",
        "error": "⚠️ Impossible de charger la transcription :",
        "summary_title": "🧾 Résumé de la Vidéo",
        "edit_btn": "✏️ Modifier",
        "save_btn": "💾 Sauvegarder",
        "edit_summary": "Modifiez votre résumé :",
        "export_title": "📥 Options d'Export",
        "export_summary": "📄 Exporter le Résumé",
        "export_notes": "📝 Exporter les Notes",
        "export_translation": "🌐 Exporter la Traduction",
        "export_recommendations": "🎬 Exporter les Recommandations",
        "file_name": "📝 Nom du fichier",
        "format": "Format",
        "quick_download": "⬇️ Téléchargement Rapide",
        "quick_download_help": "Télécharger dans votre dossier Téléchargements par défaut",
        "save_as": "📁 Enregistrer Sous...",
        "save_as_help": "Choisir où enregistrer le fichier",
        "file_saved": "✅ Fichier enregistré dans :",
        "save_cancelled": "ℹ️ Enregistrement annulé",
        "tab_translate": "🌐 Traduire",
        "tab_notes": "📝 Notes",
        "tab_recommendations": "🎥 Recommandations",
        "choose_language": "🌍 Choisissez la langue cible",
        "translate_btn": "🔄 Traduire vers",
        "translating": "Traduction vers",
        "translation_failed": "Échec de la traduction :",
        "translated_summary": "🌍 Résumé Traduit",
        "notes_caption": "Créez des notes détaillées et structurées à partir du contenu vidéo original.",
        "generate_notes_btn": "🧠 Générer des Notes Structurées",
        "creating_notes": "Création des notes structurées...",
        "notes_failed": "Échec de la génération des notes :",
        "structured_notes": "🗒️ Notes Structurées",
        "edit_notes": "Modifiez vos notes :",
        "recs_caption": "Trouvez du contenu vidéo similaire sur YouTube.",
        "find_videos_btn": "🎯 Trouver des Vidéos Similaires",
        "searching_videos": "Recherche de vidéos similaires...",
        "recs_failed": "Impossible de récupérer les recommandations :",
        "recommended_videos": "🎬 Vidéos Recommandées",
        "no_recs": "Aucune recommandation trouvée basée sur le résumé.",
        "features_title": "💡 Fonctionnalités Clés",
        "feature1_title": "⚡ Résumé Intelligent",
        "feature1_text": "Résume les longues transcriptions YouTube en insights clairs et digestes en utilisant les modèles ultra-rapides de Groq.",
        "feature2_title": "🧠 Notes Structurées",
        "feature2_text": "Génère des notes professionnelles — sujets clés, insights et points à retenir prêts pour l'étude ou la réutilisation.",
        "feature3_title": "🌍 Traduction Multilingue",
        "feature3_text": "Traduisez instantanément les résumés en plus de 14 langues dont l'anglais, le français, l'espagnol, l'allemand, l'arabe, le chinois, le japonais et plus encore.",
        "feature4_title": "🎬 Recommandations de Contenu",
        "feature4_text": "Découvrez des vidéos YouTube similaires pertinentes pour votre sujet résumé.",
        "tech_title": "🛠️ Technologies Principales Utilisées",
        "ui_language": "🌐 Langue de l'Interface"
    }
}

def t(key):
    """Get translation for current UI language."""
    return TRANSLATIONS[st.session_state.ui_language].get(key, key)

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
if 'edit_mode_summary' not in st.session_state:
    st.session_state.edit_mode_summary = False
if 'edit_mode_notes' not in st.session_state:
    st.session_state.edit_mode_notes = False
if 'edited_summary' not in st.session_state:
    st.session_state.edited_summary = ""
if 'edited_notes' not in st.session_state:
    st.session_state.edited_notes = ""
if 'ui_language' not in st.session_state:
    st.session_state.ui_language = "English"
if 'translation_language' not in st.session_state:
    st.session_state.translation_language = None

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
    # Language selector at the top
    st.markdown(f"### {t('ui_language')}")
    new_language = st.selectbox(
        "",
        ["English", "Français"],
        index=0 if st.session_state.ui_language == "English" else 1,
        key="language_selector"
    )
    if new_language != st.session_state.ui_language:
        st.session_state.ui_language = new_language
        st.rerun()

    st.divider()

    st.markdown(f"### ⚙️ {t('config')}")

    # Load saved API key
    saved_key = load_api_key()
    groq_api_key = st.text_input(t("api_key"), type="password", value=saved_key)

    # Save button
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button(f"💾 {t('save_key')}"):
            if groq_api_key and groq_api_key.startswith("gsk_"):
                if save_api_key(groq_api_key):
                    st.success("✅ API Key saved!" if st.session_state.ui_language == "English" else "✅ Clé API sauvegardée !")
                else:
                    st.error("❌ Failed to save key" if st.session_state.ui_language == "English" else "❌ Échec de la sauvegarde")
            else:
                st.warning("⚠️ Enter a valid Groq API key" if st.session_state.ui_language == "English" else "⚠️ Entrez une clé API Groq valide")
    with col2:
        if st.button(f"🗑️ {t('clear')}"):
            save_api_key("")
            st.rerun()

    st.markdown(f"{t('get_key')} [Groq Console](https://console.groq.com)")
    st.divider()

    st.markdown(f"#### 🧠 {t('about')}")
    st.info(t("about_text"))

    st.markdown(f"### 🌐 {t('connect')}")
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
    <span class='youtube-title'>{t('header_title')}</span>
    <span class='youtube-subtitle'>{t('header_subtitle')}</span>
</div>
<div class='hero-description'>{t('header_desc')}</div>
""", unsafe_allow_html=True)

st.markdown("---")

# --------------------------- MAIN SECTION (Conditional Input/Search Bar Area) ---------------------------

youtube_url = None # Initialize outside the if block

if valid_api_key:
    youtube_url = st.text_input(t("video_url"), placeholder=t("url_placeholder"))
else:
    st.info(t("enter_api_key"))

# Prompt for individual chunks (map step)
map_prompt_template = """
Provide a detailed summary of the following content section. Capture all key points, important details, and main ideas:

{text}

DETAILED SUMMARY:
"""
map_prompt = PromptTemplate(template=map_prompt_template, input_variables=["text"])

# Prompt for combining summaries (reduce step)
combine_prompt_template = """
You are given multiple summaries from different sections of a video. Combine them into one comprehensive, well-structured summary.

The final summary should:
- Be proportional to the total content length and importance
- Maintain logical flow and coherence
- Capture all essential information from all sections
- Include important examples, statistics, or quotes when relevant
- Be organized and easy to read

Section summaries:
{text}

FINAL COMPREHENSIVE SUMMARY:
"""
combine_prompt = PromptTemplate(template=combine_prompt_template, input_variables=["text"])

# --------------------------- SUMMARIZATION ---------------------------
# Only show the button and run the logic if the API key is valid
if valid_api_key:
    if st.button(t("analyze_btn")):
        if not validators.url(youtube_url):
            st.error(t("invalid_url"))
        else:
            # Clear previous utility outputs on new run
            st.session_state.translation_output = ""
            st.session_state.notes_output = ""
            st.session_state.recommendations_output = ""
            st.session_state.active_tab = 0

            with st.spinner(t("fetching")):
                try:
                    # Support for multiple languages - will try in order until one works
                    loader = YoutubeLoader.from_youtube_url(
                        youtube_url,
                        add_video_info=False,
                        language=['fr', 'en', 'es', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh-Hans', 'ar', 'hi', 'nl', 'pl', 'tr', 'sv', 'no', 'da', 'fi']
                    )
                    docs = loader.load()
                    if not docs or not any(doc.page_content.strip() for doc in docs):
                        st.error(t("no_transcript"))
                    else:
                        # Get the full transcript text
                        full_text = " ".join([doc.page_content for doc in docs])

                        # Simple chunking without transformers dependency
                        chunk_size = 2500
                        chunks = []
                        for i in range(0, len(full_text), chunk_size):
                            chunk = full_text[i:i + chunk_size]
                            chunks.append(chunk)

                        # If the text is short enough, summarize directly
                        if len(full_text) < 3000:
                            result = llm.invoke(map_prompt.format(text=full_text))
                            summary = result.content.strip()
                        else:
                            # Summarize each chunk
                            chunk_summaries = []
                            progress_bar = st.progress(0)
                            for idx, chunk in enumerate(chunks):
                                result = llm.invoke(map_prompt.format(text=chunk))
                                chunk_summaries.append(result.content.strip())
                                progress_bar.progress((idx + 1) / len(chunks))
                            progress_bar.empty()

                            # Combine all summaries
                            combined_text = "\n\n".join(chunk_summaries)

                            # If combined summaries are still long, summarize again
                            if len(combined_text) > 3000:
                                # Recursively summarize the summaries
                                final_chunks = []
                                for i in range(0, len(combined_text), 2500):
                                    final_chunks.append(combined_text[i:i + 2500])

                                final_summaries = []
                                for chunk in final_chunks:
                                    result = llm.invoke(combine_prompt.format(text=chunk))
                                    final_summaries.append(result.content.strip())

                                summary = " ".join(final_summaries)
                            else:
                                result = llm.invoke(combine_prompt.format(text=combined_text))
                                summary = result.content.strip()
                        st.session_state.summary = summary
                        st.session_state.docs = docs
                        st.success(t("success"))
                except Exception as e:
                    st.warning(f"{t('error')} {e}")

# --- RESULT SECTION (Conditional on session state, which requires the API key) ---
if st.session_state.summary:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"### {t('summary_title')}")

    # Edit mode toggle
    col_summary_1, col_summary_2 = st.columns([6, 1])
    with col_summary_1:
        pass
    with col_summary_2:
        btn_text = t("edit_btn") if not st.session_state.edit_mode_summary else t("save_btn")
        if st.button(btn_text, key="edit_summary_btn"):
            if not st.session_state.edit_mode_summary:
                st.session_state.edit_mode_summary = True
                st.session_state.edited_summary = st.session_state.summary
            else:
                st.session_state.summary = st.session_state.edited_summary
                st.session_state.edit_mode_summary = False
            st.rerun()

    # Display summary (editable or not)
    if st.session_state.edit_mode_summary:
        st.session_state.edited_summary = st.text_area(
            t("edit_summary"),
            value=st.session_state.edited_summary,
            height=300,
            key="summary_editor"
        )
    else:
        st.info(st.session_state.summary, icon="🧠")

    # --------------------------- EXPORT SECTION ---------------------------
    st.markdown(f"### {t('export_title')}")

    col_export_1, col_export_2 = st.columns([2, 2])

    with col_export_1:
        export_summary = st.checkbox(t("export_summary"), value=True, key="export_summary_cb")
        export_notes = st.checkbox(t("export_notes"), value=False, key="export_notes_cb", disabled=not st.session_state.notes_output)

    with col_export_2:
        export_translation = st.checkbox(t("export_translation"), value=False, key="export_translation_cb", disabled=not st.session_state.translation_output)
        export_recommendations = st.checkbox(t("export_recommendations"), value=False, key="export_recommendations_cb", disabled=not st.session_state.recommendations_output)

    # File name and format section
    col_name_1, col_name_2, col_name_3 = st.columns([3, 1, 2])

    with col_name_1:
        # Default filename with timestamp
        default_name = f"youtube_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        custom_filename = st.text_input(t("file_name"), value=default_name, key="custom_filename_input")

    with col_name_2:
        export_format = st.selectbox(t("format"), ["txt", "md"], key="export_format_select")

    with col_name_3:
        st.write("")  # Spacing
        st.write("")  # Spacing

    # Function to build export content
    def build_export_content():
        export_content = "# YouTube Video Summary Export\n\n"
        export_content += "=" * 50 + "\n\n"

        if export_summary and st.session_state.summary:
            export_content += "## 📄 SUMMARY\n\n"
            export_content += st.session_state.summary + "\n\n"
            export_content += "-" * 50 + "\n\n"

        if export_translation and st.session_state.translation_output:
            export_content += "## 🌐 TRANSLATION\n\n"
            export_content += st.session_state.translation_output + "\n\n"
            export_content += "-" * 50 + "\n\n"

        if export_notes and st.session_state.notes_output:
            export_content += "## 📝 STRUCTURED NOTES\n\n"
            # Clean HTML tags from notes
            clean_notes = re.sub(r'<[^>]+>', '', st.session_state.notes_output)
            export_content += clean_notes + "\n\n"
            export_content += "-" * 50 + "\n\n"

        if export_recommendations and st.session_state.recommendations_output:
            export_content += "## 🎬 RECOMMENDATIONS\n\n"
            # Clean HTML tags from recommendations
            clean_recs = re.sub(r'<[^>]+>', '\n', st.session_state.recommendations_output)
            clean_recs = re.sub(r'\n+', '\n', clean_recs)
            export_content += clean_recs + "\n\n"

        return export_content

    # Export buttons
    col_btn_1, col_btn_2 = st.columns(2)

    with col_btn_1:
        # Standard download button (downloads to browser default folder)
        export_content = build_export_content()
        filename_with_ext = f"{custom_filename}.{export_format}"

        st.download_button(
            label=t("quick_download"),
            data=export_content,
            file_name=filename_with_ext,
            mime="text/plain" if export_format == "txt" else "text/markdown",
            key="download_file_btn",
            help=t("quick_download_help")
        )

    with col_btn_2:
        # Save with dialog button (allows choosing location)
        if st.button(t("save_as"), key="save_dialog_btn", help=t("save_as_help")):
            export_content = build_export_content()
            filename_with_ext = f"{custom_filename}.{export_format}"

            success, result = save_file_with_dialog(export_content, filename_with_ext)

            if success:
                st.success(f"{t('file_saved')} {result}")
            elif result:
                st.error(f"❌ Error: {result}")
            else:
                st.info(t("save_cancelled"))

    st.divider()

    # --------------------------- UTILITIES ---------------------------
    tab1, tab2, tab3 = st.tabs([t("tab_translate"), t("tab_notes"), t("tab_recommendations")])

    # --- Translation ---
    with tab1:
        lang = st.selectbox(t("choose_language"), ["English", "French", "Spanish", "German", "Hindi", "Tamil", "Arabic", "Portuguese", "Italian", "Dutch", "Russian", "Chinese", "Japanese", "Korean"], key='t_lang')


        def translate_action():
            st.session_state.active_tab = 0
            st.session_state.notes_output = ""
            st.session_state.recommendations_output = ""
            st.session_state.translation_output = ""
            st.session_state.translation_language = lang  # Store the target language


        if st.button(f"{t('translate_btn')} {lang}", on_click=translate_action):
            with st.spinner(f"{t('translating')} {lang}..."):
                try:
                    t_prompt = PromptTemplate(
                        template="Translate the following text to {target_language} naturally and accurately. Preserve the meaning, tone, and structure:\n{text}",
                        input_variables=["text", "target_language"],
                    )
                    result = llm.invoke(t_prompt.format(text=st.session_state.summary, target_language=lang))
                    st.session_state.translation_output = result.content.strip()
                except Exception as e:
                    st.warning(f"{t('translation_failed')} {e}")

        if st.session_state.translation_output:
            html_output = f"""
            <div class="result-box-blue">
                <b>{t('translated_summary')} ({lang})</b><br>
                {st.session_state.translation_output}
            </div>
            """
            st.markdown(html_output, unsafe_allow_html=True)

    # --- Notes ---
    with tab2:
        st.caption(t("notes_caption"))


        def notes_action():
            st.session_state.active_tab = 1
            st.session_state.translation_output = ""
            st.session_state.recommendations_output = ""
            st.session_state.notes_output = ""


        if st.button(t("generate_notes_btn"), on_click=notes_action, key='notes_btn'):
            with st.spinner(t("creating_notes")):
                try:
                    # Determine target language for notes
                    target_lang = st.session_state.translation_language if st.session_state.translation_language else "English"

                    # Language-specific section titles
                    section_titles = {
                        "English": {
                            "key_topics": "Key Topics",
                            "main_takeaways": "Main Takeaways",
                            "detailed_insights": "Detailed Insights",
                            "actionable_steps": "Actionable Steps"
                        },
                        "French": {
                            "key_topics": "Sujets Clés",
                            "main_takeaways": "Points Principaux",
                            "detailed_insights": "Analyses Détaillées",
                            "actionable_steps": "Actions à Entreprendre"
                        },
                        "Spanish": {
                            "key_topics": "Temas Clave",
                            "main_takeaways": "Conclusiones Principales",
                            "detailed_insights": "Análisis Detallado",
                            "actionable_steps": "Pasos a Seguir"
                        },
                        "German": {
                            "key_topics": "Hauptthemen",
                            "main_takeaways": "Wichtigste Erkenntnisse",
                            "detailed_insights": "Detaillierte Einblicke",
                            "actionable_steps": "Handlungsschritte"
                        },
                        "Hindi": {
                            "key_topics": "मुख्य विषय",
                            "main_takeaways": "मुख्य बातें",
                            "detailed_insights": "विस्तृत जानकारी",
                            "actionable_steps": "कार्रवाई योग्य कदम"
                        },
                        "Tamil": {
                            "key_topics": "முக்கிய தலைப்புகள்",
                            "main_takeaways": "முக்கிய புள்ளிகள்",
                            "detailed_insights": "விரிவான நுண்ணறிவுகள்",
                            "actionable_steps": "செயல்படுத்தக்கூடிய படிகள்"
                        },
                        "Arabic": {
                            "key_topics": "المواضيع الرئيسية",
                            "main_takeaways": "النقاط الأساسية",
                            "detailed_insights": "رؤى مفصلة",
                            "actionable_steps": "خطوات قابلة للتنفيذ"
                        },
                        "Portuguese": {
                            "key_topics": "Tópicos Principais",
                            "main_takeaways": "Conclusões Principais",
                            "detailed_insights": "Insights Detalhados",
                            "actionable_steps": "Passos Acionáveis"
                        },
                        "Italian": {
                            "key_topics": "Argomenti Chiave",
                            "main_takeaways": "Conclusioni Principali",
                            "detailed_insights": "Approfondimenti Dettagliati",
                            "actionable_steps": "Passi da Seguire"
                        },
                        "Dutch": {
                            "key_topics": "Belangrijkste Onderwerpen",
                            "main_takeaways": "Belangrijkste Conclusies",
                            "detailed_insights": "Gedetailleerde Inzichten",
                            "actionable_steps": "Actiestappen"
                        },
                        "Russian": {
                            "key_topics": "Ключевые Темы",
                            "main_takeaways": "Основные Выводы",
                            "detailed_insights": "Подробный Анализ",
                            "actionable_steps": "Действия"
                        },
                        "Chinese": {
                            "key_topics": "关键主题",
                            "main_takeaways": "主要要点",
                            "detailed_insights": "详细见解",
                            "actionable_steps": "可行步骤"
                        },
                        "Japanese": {
                            "key_topics": "主なトピック",
                            "main_takeaways": "重要なポイント",
                            "detailed_insights": "詳細な洞察",
                            "actionable_steps": "実行可能なステップ"
                        },
                        "Korean": {
                            "key_topics": "주요 주제",
                            "main_takeaways": "주요 요점",
                            "detailed_insights": "상세 분석",
                            "actionable_steps": "실행 가능한 단계"
                        }
                    }

                    # Get section titles for target language (default to English)
                    titles = section_titles.get(target_lang, section_titles["English"])

                    # Get the full transcript text
                    full_text = " ".join([doc.page_content for doc in st.session_state.docs])

                    # Prompt for individual chunks
                    chunk_prompt_template = f"""
                    Extract key information from the following content section IN {target_lang}.
                    List the main topics, important points, and insights.

                    Content:
                    {{text}}

                    Key information:
                    """

                    # Final notes prompt
                    final_notes_template = f"""
                    From the information provided below, create detailed, structured study notes IN {target_lang}.

                    **Strictly adhere to the following formatting rules, using Markdown for headings and lists.**
                    **All content must be written in {target_lang}.**

                    # 🔑 {titles['key_topics']}
                    * List 3-5 main topics covered.

                    # 💡 {titles['main_takeaways']}
                    * List 3 concise, most important takeaways.

                    # 📝 {titles['detailed_insights']}
                    1. Use numbered list for detailed insights, explaining each point in a complete sentence.
                    2. Ensure at least 4 detailed insights are provided.

                    # 🚀 {titles['actionable_steps']}
                    * List 2-3 specific actions a user can take based on the video content.

                    Generate the result in a proper format, entirely in {target_lang}.
                    ---

                    Information to organize:
                    {{text}}
                    """

                    # Simple chunking
                    chunk_size = 2500
                    chunks = []
                    for i in range(0, len(full_text), chunk_size):
                        chunk = full_text[i:i + chunk_size]
                        chunks.append(chunk)

                    # If the text is short enough, generate notes directly
                    if len(full_text) < 3000:
                        final_prompt = PromptTemplate(template=final_notes_template, input_variables=["text"])
                        result = llm.invoke(final_prompt.format(text=full_text))
                        notes = result.content.strip()
                    else:
                        # Extract key info from each chunk
                        chunk_prompt = PromptTemplate(template=chunk_prompt_template, input_variables=["text"])
                        chunk_summaries = []
                        progress_bar = st.progress(0)
                        for idx, chunk in enumerate(chunks):
                            result = llm.invoke(chunk_prompt.format(text=chunk))
                            chunk_summaries.append(result.content.strip())
                            progress_bar.progress((idx + 1) / len(chunks))
                        progress_bar.empty()

                        # Combine all key info
                        combined_text = "\n\n".join(chunk_summaries)

                        # Generate final structured notes
                        final_prompt = PromptTemplate(template=final_notes_template, input_variables=["text"])
                        result = llm.invoke(final_prompt.format(text=combined_text))
                        notes = result.content.strip()

                    st.session_state.notes_output = re.sub(r'\n\s*\n', '\n\n', notes).strip()
                except Exception as e:
                    st.warning(f"{t('notes_failed')} {e}")

        if st.session_state.notes_output:
            # Edit mode toggle for notes
            col_notes_1, col_notes_2 = st.columns([6, 1])
            with col_notes_1:
                st.markdown(f"**{t('structured_notes')}**")
            with col_notes_2:
                btn_text = t("edit_btn") if not st.session_state.edit_mode_notes else t("save_btn")
                if st.button(btn_text, key="edit_notes_btn"):
                    if not st.session_state.edit_mode_notes:
                        st.session_state.edit_mode_notes = True
                        st.session_state.edited_notes = st.session_state.notes_output
                    else:
                        st.session_state.notes_output = st.session_state.edited_notes
                        st.session_state.edit_mode_notes = False
                    st.rerun()

            # Display notes (editable or not)
            if st.session_state.edit_mode_notes:
                st.session_state.edited_notes = st.text_area(
                    t("edit_notes"),
                    value=st.session_state.edited_notes,
                    height=400,
                    key="notes_editor"
                )
            else:
                html_output = f"""
                <div class="result-box-green">
                    {st.session_state.notes_output}
                </div>
                """
                st.markdown(html_output, unsafe_allow_html=True)

    # --- Recommendations ---
    with tab3:
        st.caption(t("recs_caption"))


        def recs_action():
            st.session_state.active_tab = 2
            st.session_state.translation_output = ""
            st.session_state.notes_output = ""
            st.session_state.recommendations_output = ""


        if st.button(t("find_videos_btn"), on_click=recs_action, key='recs_btn'):
            with st.spinner(t("searching_videos")):
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
                    st.warning(f"{t('recs_failed')} {e}")

        if st.session_state.recommendations_output:
            # Inject the full HTML list into the custom box
            html_output = f"""
            <div class="result-box-orange">
                <b>{t('recommended_videos')}</b>
                {st.session_state.recommendations_output}
            </div>
            """
            st.markdown(html_output, unsafe_allow_html=True)
        elif st.session_state.active_tab == 2:
            st.info(t("no_recs"))

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

# --------------------------- FEATURES (ALWAYS VISIBLE) ---------------------------
st.subheader(t("features_title"))
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(
        f"<div class='feature-card'><div class='feature-title'>{t('feature1_title')}</div><div class='feature-text'>{t('feature1_text')}</div></div>",
        unsafe_allow_html=True)
with col2:
    st.markdown(
        f"<div class='feature-card'><div class='feature-title'>{t('feature2_title')}</div><div class='feature-text'>{t('feature2_text')}</div></div>",
        unsafe_allow_html=True)
with col3:
    st.markdown(
        f"<div class='feature-card'><div class='feature-title'>{t('feature3_title')}</div><div class='feature-text'>{t('feature3_text')}</div></div>",
        unsafe_allow_html=True)
with col4:
    st.markdown(
        f"<div class='feature-card'><div class='feature-title'>{t('feature4_title')}</div><div class='feature-text'>{t('feature4_text')}</div></div>",
        unsafe_allow_html=True)

# --------------------------- NEW: MAIN PACKAGES USED SECTION (ALWAYS VISIBLE) ---------------------------
st.divider()

st.subheader(t("tech_title"))
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