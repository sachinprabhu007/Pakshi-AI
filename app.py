print("=== APP STARTED ===", flush=True)

import streamlit as st
print("=== STREAMLIT IMPORTED ===", flush=True)

import requests
from io import BytesIO
from PIL import Image
from pathlib import Path
import os

from src.classifier import detect_bird
from src.rag import answer_question, answer_from_gemini
print("=== IMPORTS DONE ===", flush=True)

from audio_detector import detect_bird_from_audio
print("=== AUDIO IMPORTS DONE ===", flush=True)



# Config
st.set_page_config(
    page_title="Pakshi AI",
    page_icon="🐦"
)

# Session state init
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_source" not in st.session_state:
    st.session_state.current_source = None


# Helper
def bird_exists(species):
    species = (
        species.lower()
        .replace("-", "_")
        .replace(" ", "_")
    )
    return Path(f"data/birds/{species}.txt").exists()

# def get_bird_image(species):
#     name = species.replace(" ", "_")
#     return f"https://en.wikipedia.org/wiki/Special:FilePath/{name}.jpg"
   

def get_bird_image(species):
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{species.replace(' ', '_')}"

        headers = {
            "User-Agent": "PakshiAI/1.0"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=5
        )

        print("Status:", response.status_code)

        if response.status_code != 200:
            return None

        data = response.json()

        return data.get("thumbnail", {}).get("source")

    except Exception as e:
        print("ERROR:", e)
        return None

def image_exists(url):
    try:
        r = requests.get(url, timeout=3)
        return r.status_code == 200 and "image" in r.headers.get("Content-Type", "")
    except:
        return False
    
# Header
st.title("🐦 Pakshi AI")

st.markdown("""
### Discover Birds with AI

Upload a bird image or provide an image URL to identify species and learn about them.
""")


# About section
with st.expander("About Pakshi AI"):

    st.markdown(
        """
**Pakshi AI** combines computer vision, retrieval-augmented generation (RAG),
and large language models to help users identify bird species and learn more
about them.

### Features
- 🖼️ Bird identification from images
- 🔗 Support for image URLs
- 📚 Knowledge-grounded Q&A
- 🤖 AI fallback for unsupported species
- 💬 Conversational bird assistant
"""
    )


# Image input
input_method = st.radio(
    "Choose Image Source",
    ["Upload Image", "Image URL"]
)

uploaded_file = None
image_url = None

if input_method == "Upload Image":
    uploaded_file = st.file_uploader(
        "Upload Bird Image",
        type=["jpg", "jpeg", "png"]
    )
else:

    col1, col2 = st.columns([5, 1])
    with col1:
        image_url = st.text_input(
            "Enter Image URL"
        )
    with col2:
        st.write("")
        st.write("")
        load_image = st.button("Send 🚀")


# Load image
image = None

if uploaded_file:
    image = Image.open(uploaded_file)

elif image_url:
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
    except Exception:
        st.error("Unable to load image from URL.")


# Main logic
if image:

    st.image(image, caption="Bird Image", width="stretch")

    species, confidence, top_predictions = detect_bird(image)

    if species == "Unknown Bird":
        st.error(f"Low confidence ({confidence:.2%})")

        with st.expander("Top Predictions"):
            for label, score in top_predictions:
                st.write(f"{label} — {score:.2%}")

        st.stop()

    st.success(f"Detected: {species}")
    st.caption(f"Confidence: {confidence:.2%}")

    with st.expander("Top Predictions"):
        for label, score in top_predictions:
            st.write(f"{label} — {score:.2%}")

    # Knowledge check
    has_kb = bird_exists(species)

    if not has_kb:
        st.info("Using AI-generated knowledge.")

    # Reset chat on new image
    source_id = uploaded_file.name if uploaded_file else image_url

    if st.session_state.current_source != source_id:
        st.session_state.messages = []
        st.session_state.current_source = source_id

    st.divider()

    # Chat history
    for msg in st.session_state.messages:
        avatar = "👤" if msg["role"] == "user" else "🐦"

        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])

    # Chat input (Enter or button submit)
    st.markdown("### 💬 Ask about the bird")

    with st.form("bird_chat_form", clear_on_submit=True):

        question = st.text_input(
            "Ask question",
            placeholder=f"Ask about {species}",
            label_visibility="collapsed"
        )

        send = st.form_submit_button("Send 🚀")

    # Handle chat
    if send and question:

        st.session_state.messages.append({
            "role": "user",
            "content": question
        })

        with st.chat_message("user", avatar="👤"):
            st.write(question)

        with st.spinner("Searching knowledge..."):

            if has_kb:
                answer = answer_question(species, question)
            else:
                answer = answer_from_gemini(species, question)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        with st.chat_message("assistant", avatar="🐦"):
            st.write(answer)

        st.rerun()

st.divider()

st.header("🎵 Bird Audio Identification")

audio_file = st.file_uploader(
    "Upload Bird Audio",
    type=["mp3", "wav", "flac"],
    key="audio_uploader"
)

if audio_file:

    # Save directly into project folder
    os.makedirs("uploads", exist_ok=True)

    audio_path = f"uploads/{audio_file.name}"

    with open(audio_path, "wb") as f:
        f.write(audio_file.getbuffer())
    st.audio(audio_path)

    # Run BirdNET
    with st.spinner("Analyzing bird sound..."):
        results = detect_bird_from_audio(audio_path)

    if not results:
        st.error("No bird detected")
    else:
        best = results[0]

        st.success(f"Detected: {best['species']}")
        st.caption(f"Confidence: {best['confidence']:.2%}")

        # show image
        image_url = get_bird_image(best["species"])
            
        if image_url:
            st.image(
            image_url,
            caption=best["species"],
            width = 'stretch'
        )
        else: 
            st.info("Image not available")
      
        st.subheader("🎵 Top 5 Predictions")

        for i, bird in enumerate(results, start=1):
            st.write(
                f"{i}. {bird['species']} "
                f"({bird['confidence']:.2%})"
            )

# Footer
st.markdown("""
<hr style="margin-top:2rem;margin-bottom:1rem;">

<div style="text-align:center;font-size:0.85rem;color:#888;">

Made with ❤️ by <b>Sachin Prabhu</b><br><br>

<a href="https://huggingface.co/spaces/sachinprabhu007/pakshi-ai" target="_blank">🤗 Hugging Face Space</a> |
<a href="https://github.com/sachinprabhu007/Pakshi-AI" target="_blank">GitHub</a>

Powered by
<a href="https://huggingface.co/spaces" target="_blank">🤗 Hugging Face Spaces</a> •
<a href="https://www.langchain.com" target="_blank">LangChain</a> •
<a href="https://faiss.ai" target="_blank">FAISS</a> •
<a href="https://groq.com" target="_blank">Groq</a> •
<a href="https://ai.google.dev" target="_blank">Gemini</a> •
<a href="https://streamlit.io" target="_blank">Streamlit</a> •
<a href="https://github.com/kahst/BirdNET-Analyzer" target="_blank">BirdNET</a> •
<a href="https://xeno-canto.org" target="_blank">Xeno-canto</a>
            
</div>
""", unsafe_allow_html=True)