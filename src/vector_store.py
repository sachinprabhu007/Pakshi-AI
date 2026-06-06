from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


def build_vector_db():

    documents = []

    # Load all bird knowledge files and attach species metadata
    for file in Path("data/birds").glob("*.txt"):

        text = file.read_text(encoding="utf-8")

        documents.append(
            Document(
                page_content=text,
                metadata={
                    "species": file.stem
                }
            )
        )

    # Split large documents into smaller chunks for retrieval
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(documents)

    # Embedding model used for semantic search
    emb = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    # Build and persist the FAISS vector index
    db = FAISS.from_documents(
        chunks,
        emb
    )

    db.save_local("vector_db")