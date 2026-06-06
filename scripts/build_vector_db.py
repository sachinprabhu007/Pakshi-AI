import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.vector_store import build_vector_db

build_vector_db()

print("Vector database created successfully")