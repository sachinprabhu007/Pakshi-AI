from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

import streamlit as st

load_dotenv()

print(
    "rag.py imported",
    flush=True
)


@st.cache_resource(show_spinner=False)
def get_groq_llm():
    """
    Load and cache the Groq LLM.
    """

    print(
        "Loading Groq LLM...",
        flush=True
    )

    return ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0,
        max_tokens=250
    )


@st.cache_resource(show_spinner=False)
def get_gemini_llm():
    """
    Load and cache the Gemini LLM.
    """

    print(
        "Loading Gemini LLM...",
        flush=True
    )

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0
    )


@st.cache_resource(show_spinner=False)
def get_embeddings():
    """
    Load and cache the embedding model.
    """

    print(
        "Loading embeddings...",
        flush=True
    )

    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )


@st.cache_resource(show_spinner=False)
def get_db():
    """
    Load and cache the FAISS vector database.
    """

    print(
        "Loading FAISS database...",
        flush=True
    )

    embeddings = get_embeddings()

    return FAISS.load_local(
        "vector_db",
        embeddings,
        allow_dangerous_deserialization=True
    )


def answer_question(species, question):
    """
    Answer questions using retrieved bird knowledge.
    """

    db = get_db()

    groq_llm = get_groq_llm()

    species_key = (
        species.lower()
        .replace("-", "_")
        .replace(" ", "_")
    )

    # Retrieve relevant documents for the detected species
    docs = db.similarity_search(
        question,
        k=3,
        filter={
            "species": species_key
        }
    )

    if not docs:
        return (
            "I don't have enough information "
            "in the knowledge base."
        )

    context = "\n\n".join(
        doc.page_content
        for doc in docs
    )

    # Handle vague questions
    generic_questions = {
        "about",
        "tell me",
        "tell me about it",
        "tell me about this bird",
        "information",
        "what is this bird",
        "describe this bird"
    }

    if question.lower().strip() in generic_questions:

        question = (
            f"Provide a complete summary of {species} "
            "including scientific name, habitat, diet, "
            "conservation status, description and "
            "interesting facts."
        )

    prompt = f"""
You are a bird expert.

Bird Species:
{species}

Use ONLY the retrieved context below.

Context:
{context}

User Question:
{question}

Rules:
- Answer only from the provided context.
- Do not invent facts.
- If the information is not present in the context, reply exactly:
I don't have enough information in the knowledge base.
- If the user asks for general information, provide a concise summary.
"""

    response = groq_llm.invoke(
        prompt
    )

    return response.content

def answer_from_gemini(species, question):

    gemini_llm = get_gemini_llm()

    prompt = f"""
You are a bird expert.

Bird: {species}

Question: {question}

Provide a helpful, accurate answer about the bird.
"""

    try:

        response = gemini_llm.invoke(prompt)

        if hasattr(response, "content"):
            return response.content

        return str(response)

    except Exception as e:

        print(f"Gemini error: {e}")

        error_text = str(e)

        if (
            "RESOURCE_EXHAUSTED" in error_text
            or "429" in error_text
            or "quota" in error_text.lower()
        ):
            return (
                f"⚠️ {species} was identified successfully.\n\n"
                "Detailed information for this species is temporarily unavailable.\n\n"
                "For a full demo of Pakshi AI, try House Sparrow or Peacock images.\n\n"
                "Please try again later for other bird species."
            )
        
        return (
            "⚠️ Unable to generate bird information at the moment. "
            "Please try again later."
        )