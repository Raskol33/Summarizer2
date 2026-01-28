# VERSION LOCALE - Utilise Ollama au lieu de Groq
# Ce fichier est identique à app_final.py mais utilise un LLM local (Ollama)

import validators
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama  # Utilisation d'Ollama au lieu de Groq
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import YoutubeLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from youtube_search import YoutubeSearch
import re
import os
import json
from datetime import datetime

# --------------------------- CONFIGURATION OLLAMA ---------------------------
CONFIG_FILE = "config_local.json"

def load_config():
    """Load Ollama configuration."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return config.get("ollama_url", "http://localhost:11434"), config.get("model_name", "llama3.1:8b")
        except:
            return "http://localhost:11434", "llama3.1:8b"
    return "http://localhost:11434", "llama3.1:8b"

def save_config(ollama_url, model_name):
    """Save Ollama configuration."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"ollama_url": ollama_url, "model_name": model_name}, f)
        return True
    except:
        return False

def save_file_with_dialog(content, default_filename):
    """Save file using system dialog (tkinter)."""
    try:
        from tkinter import Tk, filedialog

        root = Tk()
        root.withdraw()
        root.wm_attributes('-topmost', 1)

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=default_filename,
            filetypes=[
                ("Text files", "*.txt"),
                ("Markdown files", "*.md"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            root.destroy()
            return True, file_path

        root.destroy()
        return False, None

    except Exception as e:
        return False, str(e)

# --------------------------- PAGE CONFIG ---------------------------
st.set_page_config(
    page_title="YouTube Summarizer LOCAL 🎬",
    page_icon='https://cdn-icons-png.flaticon.com/512/1384/1384060.png',
    layout="wide"
)

# Initialize session state
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0
if 'theme' not in st.session_state:
    st.session_state.theme = "Light"
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
if 'translation_language' not in st.session_state:
    st.session_state.translation_language = None

# --------------------------- SIDEBAR ---------------------------
with st.sidebar:
    st.markdown("### ⚙️ Configuration Ollama (Local)")

    # Load saved config
    saved_url, saved_model = load_config()

    ollama_url = st.text_input("🔗 Ollama Server URL", value=saved_url)
    model_name = st.text_input("🤖 Model Name", value=saved_model)

    st.caption("Exemples de modèles: llama3.1:8b, mistral:7b, llama3.1:8b-instruct-q4_0")

    # Save button
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("💾 Save Config"):
            if save_config(ollama_url, model_name):
                st.success("✅ Configuration sauvegardée !")
            else:
                st.error("❌ Échec de la sauvegarde")
    with col2:
        if st.button("🗑️ Reset"):
            save_config("http://localhost:11434", "llama3.1:8b")
            st.rerun()

    st.divider()

    st.markdown("#### 🔒 Confidentialité Totale")
    st.info(
        "**Version locale** : Toutes les données restent sur votre VPS/serveur. "
        "Aucune donnée n'est envoyée à des services tiers."
    )

    st.markdown("#### 📝 Instructions Rapides")
    st.code("""
# Installer Ollama sur votre VPS :
curl -fsSL https://ollama.com/install.sh | sh

# Télécharger un modèle :
ollama pull llama3.1:8b

# Lancer le serveur :
ollama serve
    """)

# --- LLM INITIALIZATION ---
try:
    llm = Ollama(base_url=ollama_url, model=model_name)
    llm_available = True
except Exception as e:
    llm_available = False
    llm = None
# ----------------------------------------------

# --------------------------- MAIN HEADER ---------------------------
st.markdown(f"""
<div style='text-align: center; padding: 2rem 0;'>
    <h1>🎬 YouTube Summarizer <span style='color: #FF0000;'>LOCAL</span></h1>
    <p style='color: #666;'>100% privé - Vos données restent sur votre serveur</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# --------------------------- MAIN SECTION ---------------------------
youtube_url = None

if llm_available:
    youtube_url = st.text_input("🎥 URL de la vidéo YouTube", placeholder="ex. https://youtube.com/watch?v=abcd1234")
else:
    st.error("❌ **Impossible de se connecter à Ollama.** Vérifiez que le serveur Ollama est lancé et accessible.")
    st.info(f"URL testée : {ollama_url}")

# Prompts templates
map_prompt_template = """
Provide a detailed summary of the following content section. Capture all key points, important details, and main ideas:

{text}

DETAILED SUMMARY:
"""
map_prompt = PromptTemplate(template=map_prompt_template, input_variables=["text"])

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
if llm_available:
    if st.button("🚀 Analyser et Résumer la Vidéo"):
        if not validators.url(youtube_url):
            st.error("❌ Veuillez entrer une URL YouTube valide.")
        else:
            st.session_state.translation_output = ""
            st.session_state.notes_output = ""
            st.session_state.recommendations_output = ""
            st.session_state.active_tab = 0

            with st.spinner("⏳ Récupération de la transcription et génération du résumé..."):
                try:
                    loader = YoutubeLoader.from_youtube_url(
                        youtube_url,
                        add_video_info=False,
                        language=['fr', 'en', 'es', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh-Hans', 'ar', 'hi', 'nl', 'pl', 'tr', 'sv', 'no', 'da', 'fi']
                    )
                    docs = loader.load()
                    if not docs or not any(doc.page_content.strip() for doc in docs):
                        st.error("❌ Aucune transcription disponible pour cette vidéo.")
                    else:
                        # Get the full transcript text
                        full_text = " ".join([doc.page_content for doc in docs])

                        # Simple chunking
                        chunk_size = 2500
                        chunks = []
                        for i in range(0, len(full_text), chunk_size):
                            chunk = full_text[i:i + chunk_size]
                            chunks.append(chunk)

                        # If short, summarize directly
                        if len(full_text) < 3000:
                            result = llm.invoke(map_prompt.format(text=full_text))
                            summary = result.strip()
                        else:
                            # Summarize each chunk
                            chunk_summaries = []
                            progress_bar = st.progress(0)
                            for idx, chunk in enumerate(chunks):
                                result = llm.invoke(map_prompt.format(text=chunk))
                                chunk_summaries.append(result.strip())
                                progress_bar.progress((idx + 1) / len(chunks))
                            progress_bar.empty()

                            # Combine
                            combined_text = "\n\n".join(chunk_summaries)

                            if len(combined_text) > 3000:
                                final_chunks = []
                                for i in range(0, len(combined_text), 2500):
                                    final_chunks.append(combined_text[i:i + 2500])

                                final_summaries = []
                                for chunk in final_chunks:
                                    result = llm.invoke(combine_prompt.format(text=chunk))
                                    final_summaries.append(result.strip())

                                summary = " ".join(final_summaries)
                            else:
                                result = llm.invoke(combine_prompt.format(text=combined_text))
                                summary = result.strip()

                        st.session_state.summary = summary
                        st.session_state.docs = docs
                        st.success("✅ Résumé généré avec succès !")
                except Exception as e:
                    st.warning(f"⚠️ Erreur : {e}")

# --- RESULT SECTION ---
if st.session_state.summary:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🧾 Résumé de la Vidéo")

    # Edit mode toggle
    col_summary_1, col_summary_2 = st.columns([6, 1])
    with col_summary_2:
        btn_text = "✏️ Modifier" if not st.session_state.edit_mode_summary else "💾 Sauvegarder"
        if st.button(btn_text, key="edit_summary_btn"):
            if not st.session_state.edit_mode_summary:
                st.session_state.edit_mode_summary = True
                st.session_state.edited_summary = st.session_state.summary
            else:
                st.session_state.summary = st.session_state.edited_summary
                st.session_state.edit_mode_summary = False
            st.rerun()

    # Display summary
    if st.session_state.edit_mode_summary:
        st.session_state.edited_summary = st.text_area(
            "Modifiez votre résumé :",
            value=st.session_state.edited_summary,
            height=300,
            key="summary_editor"
        )
    else:
        st.info(st.session_state.summary, icon="🧠")

    st.divider()

    # Export section
    st.markdown("### 📥 Options d'Export")

    col_export_1, col_export_2 = st.columns([2, 2])
    with col_export_1:
        export_summary = st.checkbox("📄 Exporter le Résumé", value=True, key="export_summary_cb")
        export_notes = st.checkbox("📝 Exporter les Notes", value=False, key="export_notes_cb", disabled=not st.session_state.notes_output)
    with col_export_2:
        export_translation = st.checkbox("🌐 Exporter la Traduction", value=False, key="export_translation_cb", disabled=not st.session_state.translation_output)
        export_recommendations = st.checkbox("🎬 Exporter les Recommandations", value=False, key="export_recommendations_cb", disabled=not st.session_state.recommendations_output)

    col_name_1, col_name_2, col_name_3 = st.columns([3, 1, 2])
    with col_name_1:
        default_name = f"youtube_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        custom_filename = st.text_input("📝 Nom du fichier", value=default_name, key="custom_filename_input")
    with col_name_2:
        export_format = st.selectbox("Format", ["txt", "md"], key="export_format_select")

    def build_export_content():
        export_content = "# YouTube Video Summary Export (LOCAL)\n\n"
        export_content += "=" * 50 + "\n\n"

        if export_summary and st.session_state.summary:
            export_content += "## 📄 RÉSUMÉ\n\n"
            export_content += st.session_state.summary + "\n\n"
            export_content += "-" * 50 + "\n\n"

        if export_translation and st.session_state.translation_output:
            export_content += "## 🌐 TRADUCTION\n\n"
            export_content += st.session_state.translation_output + "\n\n"
            export_content += "-" * 50 + "\n\n"

        if export_notes and st.session_state.notes_output:
            export_content += "## 📝 NOTES STRUCTURÉES\n\n"
            clean_notes = re.sub(r'<[^>]+>', '', st.session_state.notes_output)
            export_content += clean_notes + "\n\n"
            export_content += "-" * 50 + "\n\n"

        if export_recommendations and st.session_state.recommendations_output:
            export_content += "## 🎬 RECOMMANDATIONS\n\n"
            clean_recs = re.sub(r'<[^>]+>', '\n', st.session_state.recommendations_output)
            clean_recs = re.sub(r'\n+', '\n', clean_recs)
            export_content += clean_recs + "\n\n"

        return export_content

    col_btn_1, col_btn_2 = st.columns(2)
    with col_btn_1:
        export_content = build_export_content()
        filename_with_ext = f"{custom_filename}.{export_format}"
        st.download_button(
            label="⬇️ Téléchargement Rapide",
            data=export_content,
            file_name=filename_with_ext,
            mime="text/plain" if export_format == "txt" else "text/markdown",
            key="download_file_btn",
            help="Télécharger dans votre dossier Téléchargements"
        )
    with col_btn_2:
        if st.button("📁 Enregistrer Sous...", key="save_dialog_btn", help="Choisir où enregistrer"):
            export_content = build_export_content()
            filename_with_ext = f"{custom_filename}.{export_format}"
            success, result = save_file_with_dialog(export_content, filename_with_ext)
            if success:
                st.success(f"✅ Fichier enregistré : {result}")
            elif result:
                st.error(f"❌ Erreur : {result}")
            else:
                st.info("ℹ️ Enregistrement annulé")

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

st.markdown("### 🔒 Avantages de la Version Locale")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**🛡️ Confidentialité**")
    st.caption("Vos données ne quittent jamais votre serveur")
with col2:
    st.markdown("**💰 Gratuit**")
    st.caption("Pas de limite d'API, pas de coût externe")
with col3:
    st.markdown("**🌍 Souveraineté**")
    st.caption("Contrôle total sur vos données et infrastructure")
