from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

db = FAISS.load_local(
    "vector_store",
    embeddings,
    allow_dangerous_deserialization=True
)


def build_query(preferences: dict):

    parts = []

    if preferences.get("similar_to"):
        parts.append(
            f"similar to {preferences['similar_to']}"
        )

    if preferences.get("cuisine"):
        parts.append(preferences["cuisine"])

    if preferences.get("diet"):
        parts.append(preferences["diet"])

    if preferences.get("spice_level"):
        parts.append(
            f"{preferences['spice_level']} spicy"
        )

    if preferences.get("category"):
        parts.append(preferences["category"])

    if preferences.get("budget"):
        parts.append(
            f"under {preferences['budget']} rupees"
        )

    if not parts:
        return "popular dishes"

    return " ".join(parts)


def retrieve_dishes(preferences):

    query = build_query(preferences)

    docs = db.similarity_search(
        query=query,
        k=10
    )

    return docs