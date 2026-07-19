from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient("mongodb+srv://Cluster47062:XLxGVu26VDbfppvU@cluster47062.yhvoyo7.mongodb.net/")

db = client.chatbot

preferences_collection = db.preferences


async def get_preferences(user_id: str) -> dict:
    """
    Returns the user's saved preferences.
    """

    document = await preferences_collection.find_one(
        {"user_id": user_id}
    )

    if not document:
        return {}





async def save_preferences(user_id: str, new_preferences: dict) -> dict:
    """
    Merge new preferences with existing ones and save them.
    Returns the merged preferences.
    """

    document = await preferences_collection.find_one(
        {"user_id": user_id}
    )

    if document:
        existing_preferences = document.get("preferences", {})
    else:
        existing_preferences = {}

    # Merge preferences
    merged_preferences = {
        **existing_preferences,
        **new_preferences,
    }

    await preferences_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "preferences": merged_preferences,
                "updated_at": datetime.utcnow(),
            },
            "$setOnInsert": {
                "created_at": datetime.utcnow(),
            },
        },
        upsert=True,
    )

    return merged_preferences