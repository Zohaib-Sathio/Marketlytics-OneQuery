import os

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma 
from langchain.schema import Document

from utils.google_embeddings import get_embeddings




CHROMA_DIR = "vector_store/emails"

def chunk_and_store_emails(text, metadata):
    embeddings = get_embeddings()

    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=60)
    chunks = splitter.split_text(text)
    documents = [Document(page_content=chunk, metadata=metadata) for chunk in chunks]

    if not os.path.exists(CHROMA_DIR):
        db = Chroma.from_documents(documents, embeddings, persist_directory=CHROMA_DIR)
    else:
        db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
        db.add_documents(documents)
