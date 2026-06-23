from langchain_google_genai import ChatGoogleGenerativeAI


import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print(api_key)
llm=ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", google_api_key=api_key)
print(llm.invoke("hello").content)