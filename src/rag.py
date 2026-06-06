from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

# LLM used for Retrieval-Augmented Generation (RAG)
groq_llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    max_tokens=250
)

# Fallback LLM for bird species not present in the knowledge base
gemini_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

# Embedding model used to vectorize bird documents
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

# Load the FAISS vector database
db = FAISS.load_local(
    "vector_db",
    embeddings,
    allow_dangerous_deserialization=True
)


def answer_question(species, question):
    """
    Answer questions using retrieved bird knowledge.
    """

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

def answer_from_gemini(
    species,
    question
):
    """
    Fallback for bird species not available
    in the curated knowledge base.
    """

    prompt = f"""
You are a bird expert.

The bird species being discussed is:

{species}

Answer the user's question about THIS bird species.

User Question:
{question}

If the question is general (for example:
'Tell me about it',
'Tell me about this bird',
'What is this bird?'),
respond in this format:

Name:

Scientific Name:

Habitat:

Diet:

Conservation Status:

Description:

Interesting Facts:
- Fact 1
- Fact 2

If the question is specific, answer only that question.
"""

    response = gemini_llm.invoke(
        prompt
    )

    return response.content