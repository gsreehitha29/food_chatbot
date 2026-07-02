import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(dotenv_path=r"c:\Users\vinja\Desktop\sreehitha_intern\chatbot\backend\.env")

uri = os.getenv("MONGODB_URI")
client = MongoClient(uri)

target_names = ["Yum Yum", "Punjabi", "Bake Factory", "Mota Kababi", "Kolkata"]

print("Databases on main cluster:", client.list_database_names())

for db_name in client.list_database_names():
    if db_name in ["admin", "local", "sample_mflix"]:
        continue
    db = client[db_name]
    try:
        for col_name in db.list_collection_names():
            col = db[col_name]
            # Search for restaurant names or restaurant IDs
            for name in target_names:
                doc = col.find_one({"$or": [
                    {"restaurant_name": {"$regex": name, "$options": "i"}},
                    {"item_name": {"$regex": name, "$options": "i"}},
                    {"description": {"$regex": name, "$options": "i"}}
                ]})
                if doc:
                    print(f"🎉 FOUND match for '{name}' in database '{db_name}', collection '{col_name}':")
                    import pprint
                    pprint.pprint(doc)
    except Exception as e:
        print(f"Error checking {db_name}: {e}")
