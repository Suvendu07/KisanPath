import os
from pathlib import Path


from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.prompts import PromptTemplate

from fastapi import HTTPException, status
from app.config import settings
from app.schemas.ai import RagRequest, RagResponse, RagSource



KNOWLEDGE_DIR = Path(settings.KNOWLEDGE_BASE_DIR)
VECTOR_DIR = Path(settings.VECTOR_STORE_DIR)
VECTOR_INDEX = VECTOR_DIR / "kisanpath_index"


RAG_PROMPT_TEMPLATE = """You are AgriAI, KisanPath's farming expert.
Answer the farmer's question using ONLY the information from the provided documents.
If the answer is not in the documents, say: "This specific information is not in our farming guides.
Please consult your local agriculture officer (KVK)."
 
Always be practical and clear. Use bullet points for steps.
 
Documents: {summaries}
 
Question: {question}
Answer:"""
 
 
 
RAG_PROMPT = PromptTemplate(
    template=RAG_PROMPT_TEMPLATE,
    input_variables=["summaries", "question"],
)


def get_embedding():
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured.")
    
    return GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key = settings.GEMINI_API_KEY,
    )
    
    
def build_vector_store() -> FAISS:
    
    if not KNOWLEDGE_DIR.exists() or not any(KNOWLEDGE_DIR.glob("*.pdf")):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "No PDFs found in knowldge_base/ folder."
                "Add farming PDFs (crop_guides, pest management, etc.) to that folder first."
            )
        )
        
        
    print("Building RAG vector store from PDFs...")
    
    """DirectoryLoader() helps to load multiple pdf file at the same time
    while pypdfloader only load one pdf at a time."""
    loader = DirectoryLoader(str(KNOWLEDGE_DIR), glob="**/*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    print(f" Loader {len(documents)} pages from {KNOWLEDGE_DIR}")
    
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000,
        chunk_overlap = 200,
        separators=["\n\n" , "\n", ".", "!", "?", " "],
    )
    
    chunks = splitter.split_documents(documents)
    print(f" Split into {len(chunks)} chunks")
    
    embedding = get_embedding()
    vector_store = FAISS.from_documents(chunks, embedding)
    
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(str(VECTOR_INDEX))
    print(f" vector store saved to {VECTOR_INDEX}")
    
    
    return vector_store




def load_vector_store() -> FAISS:
    
    embeddings = get_embedding()
    
    if VECTOR_INDEX.exists():
        return FAISS.load_local(
            str(VECTOR_INDEX),
            embeddings,
            allow_dangerous_deserialization=True,
        )
        
    else:
        return build_vector_store()
    
    


def ask_farming_docs(payload : RagRequest) -> RagResponse:
    
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="GEMINI_API_KEY not configured.")
    
    try:
        vector_store = load_vector_store()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to load knowledge base: {str(e)}"
                            )
        
        
    llm = ChatGoogleGenerativeAI(
        model = "gemini-2.5-flash",
        google_api_key = settings.GEMINI_API_KEY,
        temperature = 0.3,
    )
    
    
    retriever = vector_store.as_retriever(
        search_type = "similarity",
        search_kwargs = {"k" : payload.top_k},
    )
    
    
    document_chain = create_stuff_documents_chain(
        llm = llm,
        prompt=RAG_PROMPT,
    )
    
    chain = create_retrieval_chain(
        retriever = retriever,
        combine_docs_chain = document_chain,
    )
    
    
    try:
        result = chain({"question" : payload.question})
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"RAG chain error : {str(e)}")
        
    
    sources = []
    seen = set()
    
    for doc in result.get("source_documents", []):
        meta = doc.metadata
        src_key = f"{meta.get('source', 'unknown')}:{meta.get('page',0)}"
        
        if src_key not in seen:
            seen.add(src_key)
            sources.append(RagSource(
                source=os.path.basename(meta.get("source", "unknown")),
                page = meta.get("page", 0) + 1,
                excerpt=doc.page_content[:200] + "...",
            ))
            
    
    return RagResponse(
        answer   = result.get("answer", result.get("result", "No answer found.")),
        sources  = sources,
        question = payload.question,
    )
 
 
def rebuild_vector_store() -> dict:
    """Called by admin endpoint when new PDFs are added to knowledge_base/."""
    store = build_vector_store()
    return {
        "message": "Knowledge base rebuilt successfully.",
        "index":   str(VECTOR_INDEX),
    }