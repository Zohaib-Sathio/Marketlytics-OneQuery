from pinecone import Pinecone, ServerlessSpec
import os
from utils.google_embeddings import get_embeddings
from dotenv import load_dotenv

import os

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")


# Init Gemini embedding model
embedding_model = get_embeddings()

# Init Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

def query_pinecone_with_gemini(query_text: str, top_k: int = 3):
    # Step 1: Embed the query
    query_embedding = embedding_model.embed_query(query_text)

    # Step 2: Search Pinecone using this embedding
    response = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )

    # Step 3: Display results
    print("\n🔍 Top results:")
    for i, match in enumerate(response['matches']):
        print(f"\nResult #{i+1}")
        print(f"Score: {match['score']}")
        print(f"Metadata: {match['metadata']}")

    return response['matches']

# Example usage
if __name__ == "__main__":
    user_question = input("❓ Your question: ")
    query_pinecone_with_gemini(user_question)
