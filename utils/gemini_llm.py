from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv(override=True)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Sanity check
if not GOOGLE_API_KEY or "AIza" not in GOOGLE_API_KEY:
    raise ValueError(f"Invalid or missing GOOGLE_API_KEY: {GOOGLE_API_KEY}")

def get_gemini_llm():
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)
    return llm

# llm = get_gemini_llm()
# print(llm.invoke("Say hello").content)
