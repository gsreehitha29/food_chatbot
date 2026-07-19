import json
from pathlib import Path

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from ..adapter.mcp_adapter import menu_client

# Project root (food_chatbot/)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
VECTOR_DB = PROJECT_ROOT / "vector_store"

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


async def build_index():
    docs = []

    async with menu_client:
        response = await menu_client.call_tool("retrieve_all_menu_items")

    data = json.loads(response.content[0].text)

    for item in data:
        text = f"""
Dish: {item.get('dish_name', '')}
Category: {item.get('category', '')}
Cuisine: {item.get('cuisine', '')}
Diet: {item.get('diet_type', '')}
Price: ₹{item.get('price', '')}
Restaurant: {item.get('restaurant_name', '')}
Description: {item.get('description', '')}
Available: {item.get('is_available', True)}
"""

        docs.append(
            Document(
                page_content=text,
                metadata={
                    "dish_id": item.get("dish_id"),
                    "dish_name": item.get("dish_name"),
                    "restaurant_id": item.get("restaurant_id"),
                    "restaurant_name": item.get("restaurant_name"),
                    "category": item.get("category"),
                    "cuisine": item.get("cuisine"),
                    "diet_type": item.get("diet_type"),
                    "price": item.get("price"),
                    "is_available": item.get("is_available"),
                },
            )
        )

    # Create the directory if it doesn't exist
    VECTOR_DB.mkdir(parents=True, exist_ok=True)

    # Build FAISS index
    db = FAISS.from_documents(docs, embeddings)

    # Save to food_chatbot/vector_store/
    db.save_local(str(VECTOR_DB))

    print(f"✅ Index created with {len(docs)} dishes.")
    print(f"📂 Saved to: {VECTOR_DB}")