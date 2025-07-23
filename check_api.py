from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv(override=True)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
print("FROM .env:", repr(GOOGLE_API_KEY))

hardcoded_key = "AIzaSyCaJCtkGhuOxKKUySnMJC9X9lRzzx0RePU"
print("HARDCODED :", repr(hardcoded_key))

assert GOOGLE_API_KEY == hardcoded_key, "Mismatch between .env and hardcoded key"

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)
response = llm.invoke("Say hello")
print("Gemini Response:", response.content)
