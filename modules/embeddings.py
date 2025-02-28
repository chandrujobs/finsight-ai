from langchain.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import EMBEDDING_MODEL

def create_vectorstore(documents):
    """Create a vector store from documents"""
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = FAISS.from_documents(documents, embeddings)
    return vectorstore

def get_retriever(vectorstore, k=8, score_threshold=0.7):
    """Get a retriever from a vector store"""
    return vectorstore.as_retriever(
        search_kwargs={
            "k": k,  # Retrieve k documents for better context
            "score_threshold": score_threshold  # Only include relevant chunks
        },
        metadata_keys=[
            "page_display", 
            "section", 
            "content_type", 
            "doc_type", 
            "doc_year", 
            "company"
        ]
    )