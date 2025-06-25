from langchain_chroma import Chroma
from utils.google_embeddings import get_embeddings

from langchain.retrievers import EnsembleRetriever

def db_retriever():
    embeddings = get_embeddings()

    # Setup vector stores
    CHROMA_DIR_1 = "vector_store/google_drive"
    CHROMA_DIR_2 = "vector_store/emails"
    CHROMA_DIR_3 = "vector_store/slack_vector_db"

    db1 = Chroma(persist_directory=CHROMA_DIR_1, embedding_function=embeddings)
    db2 = Chroma(persist_directory=CHROMA_DIR_2, embedding_function=embeddings)
    db3 = Chroma(persist_directory=CHROMA_DIR_3, embedding_function=embeddings)

    retriever1 = db1.as_retriever(search_kwargs={"k": 3})
    retriever2 = db2.as_retriever(search_kwargs={"k": 3})
    # retriever3 = db3.as_retriever(search_kwargs={"k": 3})

    ensemble_retriever = EnsembleRetriever(
        retrievers=[retriever1, retriever2],
        weights=[0.5, 0.5]
    )
    return ensemble_retriever