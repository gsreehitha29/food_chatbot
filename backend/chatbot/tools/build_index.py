import asyncio
import json
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from adapter.mcp_adapter import menu_client

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

async def build_index():
    docs = []

    async with menu_client:
        response = await menu_client.call_tool("retrieve_all_menu_items")


    menu_items = getattr(response, "result", response)
    text_content = menu_items.content[0].text  

    data = json.loads(text_content)
    for item in data:


        text = f"""
Dish: {item['item_name']}
Category: {item.get('category')}
Diet: {item.get('veg_or_nonveg')}
Price: ₹{item.get('price')}
Description: {item.get('description', '')}
"""

        docs.append(Document(page_content=text, metadata=item))

    db = FAISS.from_documents(docs, embeddings)
    db.save_local("vector_store")

    print("Index created:", len(docs))
