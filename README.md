

## 🎬 YouTube Video Summarizer 

## 💡 Project Overview

The **YouTube Video Summarizer** is a fast and powerful GenAI application built using **Streamlit** and the **Groq LLM**. It allows users to input a YouTube video URL and instantly receive a concise summary, structured notes, multi-language translations, and related video recommendations by leveraging the video's transcript.

The core goal is to demonstrate the **blazing speed** and effectiveness of Groq's LLMs (specifically **Llama 3.1 8B**) when combined with the **LangChain** framework for transcript analysis.

-----

## ✨ Features

This application transforms passive viewing into actionable insights:

  * **⚡ Ultra-Fast Summarization:** Get a $\sim$300-word summary of any YouTube video's transcript almost instantly, powered by the Groq LPU.
  * **🧠 Structured Study Notes:** Generates detailed notes with clear headings for Key Topics, Main Takeaways, Detailed Insights, and Actionable Steps.
  * **🌍 Multi-Language Translation:** Translate the generated summary into popular languages like Hindi, Spanish, French, German, and Tamil.
  * **🎬 Content Recommendations:** Automatically searches YouTube for similar video content based on the summary's theme.
  * **🎨 Clean UI:** A responsive, YouTube-themed user interface built with Streamlit (`app\_final.py`).
  * **🔌 API Access:** A separate file (`app\_api.py`) exposes the core summarization, notes, translation, and recommendation logic via API endpoints.

-----

## 🛠️ Technology Stack

| Technology | Role |
| :--- | :--- |
| **Streamlit** | Frontend framework for building the interactive web application (`app_final.py`). |
| **Groq (ChatGroq)** | Provides the Llama 3.1 8B LLM for high-speed inference (summaries, notes, translations). |
| **LangChain** | Orchestration framework for connecting the LLM, managing prompts, and handling summarization chains. |
| **YoutubeLoader** | Used to fetch and process the YouTube video transcripts. |
| **YoutubeSearch** | Library used for finding related video content. |
| **Python** | The primary language used for the entire application logic. |

-----

## ⚙️ Setup and Installation

Follow these steps to set up the project locally:

### 1\. Prerequisites

You must have **Python 3.8+** installed.

### 2\. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_LINK>
cd youtube-summarizer-project
```

### 3\. Install Dependencies

Install all required packages:

```bash

pip install -r requirements.text

            (OR)

# Install core dependencies for the Streamlit app and API logic
pip install streamlit langchain groq langchain-groq langchain-community pydantic youtube-search validators 

# Install dependencies required to run the API (e.g., FastAPI and Uvicorn)
pip install fastapi uvicorn
```

### 4\. Get Your Groq API Key

This project requires a **Groq API Key** for LLM access.

  * Sign up or log in at the [Groq Console](https://console.groq.com/).
  * Generate a new API key (`gsk\_...`).

-----

## 🚀 Usage

The project can be run as a Web App or as a backend API service.

### Option A: Streamlit Web App (`app_final.py`)

This provides the full graphical interface with all features.


1.  **Run the App:**

    ```bash
    streamlit run app_final.py
    ```
2.  **Access:** Open your browser to `http://localhost:8501`.
3.  **Use:** Paste your **Groq API Key** in the sidebar, then input a YouTube URL and click "Analyze & Summarize Video."

### Option B: API Service (`app_api.py`)

This allows programmatic access to the summarization features.

1.  **Start the API Server:**
    ```bash
    # Start the server (assuming FastAPI setup in app_api.py)
    uvicorn app_api:app --reload --port 8000
    ```
2.  **API Endpoints:** The following endpoints are available:
      * `/summary`
      * `/notes`
      * `/translate`
      * `/recommendations`

-----

## 🔌 API Usage with Postman

We have provided a **Postman Collection** to make testing and integration easy.

### 1\. Import the Collection

1.  Download the provided Postman collection file (`youtube-summarizer-collection.json`).
2.  Import the collection into your Postman application.

### 2\. Required Payload

All endpoints are typically **POST** requests and require the following common structure in the **JSON body**:

| Field | Type | Description |
| :--- | :--- | :--- |
| `url` | string | The **YouTube video URL** to be analyzed. |
| `groq_key` | string | Your **Groq API Key** (`gsk\_...`). |
| `language` | string (Optional) | Required only for the `/translate` endpoint (e.g., "Hindi" or "Spanish"). |

### 3\. Hitting Endpoints

Use the requests provided in the Postman collection:

| Endpoint | Purpose |
| :--- | :--- |
| `/summary` | Retrieves the concise text summary of the video. |
| `/notes` | Retrieves the detailed, structured study notes. |
| `/translate` | Translates the summary into the specified language. **Requires the `language` field.** |
| `/recommendations` | Fetches a list of related YouTube videos. |