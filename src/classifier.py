from transformers import pipeline
import streamlit as st

# Minimum confidence required to accept a prediction
CONFIDENCE_THRESHOLD = 0.90


@st.cache_resource
def get_classifier():
    """
    Load and cache the bird classification model.
    """

    print(
        "Loading bird classifier...",
        flush=True
    )

    return pipeline(
        "image-classification",
        model="chriamue/bird-species-classifier"
    )


def detect_bird(image):
    """
    Detect the bird species from an input image.
    """

    classifier = get_classifier()

    results = classifier(image)

    # Store top predictions for display in the UI
    top_predictions = [
        (
            pred["label"].upper(),
            pred["score"]
        )
        for pred in results[:5]
    ]

    best = results[0]

    species = best["label"].upper().strip()
    confidence = float(best["score"])

    # Reject low-confidence predictions
    if confidence < CONFIDENCE_THRESHOLD:
        return (
            "Unknown Bird",
            confidence,
            top_predictions
        )

    return (
        species,
        confidence,
        top_predictions
    )