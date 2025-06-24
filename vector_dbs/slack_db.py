
from langchain_chroma import Chroma 
from langchain.schema import Document
import os

from utils.google_embeddings import get_embeddings


CHROMA_DIR = "vector_store/slack_vector_db"


# Utility: Store summary into vector DB
def upsert_summary(summary_text, metadata):
    
    embedding = get_embeddings()
    
    # Initialize or load Chroma DB
    if not os.path.exists(CHROMA_DIR):
        os.makedirs(CHROMA_DIR)

    chroma_db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embedding)
        
    doc = Document(page_content=summary_text, metadata=metadata)
    chroma_db.add_documents([doc])
