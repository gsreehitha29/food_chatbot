from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

# Load env variables from backend/.env dynamically
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.abspath(os.path.join(current_dir, "..", "..", ".env"))
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    google_api_key=api_key,
)
