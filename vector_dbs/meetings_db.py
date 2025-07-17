from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma 
from langchain.schema import Document
from utils.google_embeddings import get_embeddings

embedding = get_embeddings()

def chunk_and_store_meeting(cleaned_text, metadata=None, persist_dir="vector_store/grain_meetings"):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)

    docs = text_splitter.create_documents([cleaned_text], metadatas=[metadata])

    # 🔁 Add inline prefix to each chunk
    title_line = f"[This is the meeting summary for {metadata.get('project_name', 'Untitled')} project.]"
    for doc in docs:
        doc.page_content = f"{title_line}\n\n{doc.page_content}"
        print(doc)

    vectorstore = Chroma(
        persist_directory=persist_dir,
        embedding_function=embedding
    )

    vectorstore.add_documents(docs)