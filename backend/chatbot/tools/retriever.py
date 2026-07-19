from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
VECTOR_STORE = PROJECT_ROOT / "vector_store"

db = None


def get_db():
    global db

    if db is None:
        db = FAISS.load_local(
            str(VECTOR_STORE),
            embeddings,
            allow_dangerous_deserialization=True,
        )

    return db


def build_query(preferences: dict):
    parts = []

    if preferences.get("similar_to"):
        parts.append(f"similar to {preferences['similar_to']}")

    if preferences.get("cuisine"):
        parts.append(preferences["cuisine"])

    if preferences.get("diet"):
        parts.append(preferences["diet"])

    if preferences.get("spice_level"):
        parts.append(f"{preferences['spice_level']} spicy")

    if preferences.get("category"):
        parts.append(preferences["category"])

    if preferences.get("budget"):
        parts.append(f"under {preferences['budget']} rupees")

    return " ".join(parts) if parts else "popular dishes"


def retrieve_dishes(preferences):
    db = get_db()

    query = build_query(preferences)

    return db.similarity_search(
        query=query,
        k=10,
    )