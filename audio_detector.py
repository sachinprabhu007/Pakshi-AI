from birdnet_analyzer.analyze.core import analyze
import csv
import os
from pathlib import Path


def detect_bird_from_audio(audio_path):
    output_dir = "birdnet_output"
    os.makedirs(output_dir, exist_ok=True)

    analyze(
        audio_input=audio_path,
        output=output_dir,
        min_conf=0.2,
        top_n=5,
        rtype="csv",
        locale="en",
        threads=2,
    )

    audio_name = Path(audio_path).stem

    results_file = os.path.join(
        output_dir,
        f"{audio_name}.BirdNET.results.csv"
    )

    if not os.path.exists(results_file):
        return []

    candidates = []

    with open(results_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            candidates.append(
                {
                    "species": row["Common name"],
                    "scientific_name": row["Scientific name"],
                    "confidence": float(row["Confidence"]),
                }
            )

    unique_candidates = {}

    for candidate in candidates:
        species = candidate["species"]

        if (
            species not in unique_candidates
            or candidate["confidence"]
            > unique_candidates[species]["confidence"]
        ):
            unique_candidates[species] = candidate

    results = sorted(
        unique_candidates.values(),
        key=lambda x: x["confidence"],
        reverse=True,
    )

    return results[:5]


if __name__ == "__main__":
    results = detect_bird_from_audio(
        "samples/indian_peafowl.mp3"
    )

    print("\nTop Predictions:\n")

    for idx, bird in enumerate(results, start=1):
        print(
            f"{idx}. {bird['species']} "
            f"({bird['scientific_name']}) - "
            f"{bird['confidence']:.2%}"
        )