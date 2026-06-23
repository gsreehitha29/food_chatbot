"""
=============================================================
SEED DATA — DEPRECATED
=============================================================
This script previously seeded the database with dummy/demo
restaurants (Pizza Palace, Biryani House, Dragon Wok, etc.)
for local testing.

That fake data has been REMOVED. The application now uses the
real production database:

  Database : chatbot_database  (MongoDB Atlas)
  Cluster  : chatbot-cluster.tlksy4i.mongodb.net

Collections (real data):
  RESTAURANTS  — 9 restaurants
  MENU         — 69 menu items
  CART         — live cart data
  ORDERS       — live order data
  REVIEW       — live reviews
  USERS        — live users

Do NOT run this script. There is no seed data to insert.
If you need to add new restaurants or menu items, add them
directly to the chatbot_database collections in MongoDB Atlas.
=============================================================
"""

print("ℹ️  seed_data.py is deprecated.")
print("   The application uses real data in 'chatbot_database' on MongoDB Atlas.")
print("   No seeding is required.")
