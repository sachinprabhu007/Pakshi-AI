print("=== APP STARTED ===", flush=True)

import streamlit as st
print("=== STREAMLIT IMPORTED ===", flush=True)

import requests
from io import BytesIO
from PIL import Image
from pathlib import Path

from src.classifier import detect_bird
from src.rag import answer_question, answer_from_gemini

print("=== IMPORTS DONE ===", flush=True)


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
<a href="https://streamlit.io" target="_blank">Streamlit</a>
            
</div>
""", unsafe_allow_html=True)