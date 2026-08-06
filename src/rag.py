from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_classic.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
import pypdf
from pypdf import PdfReader
from pathlib import Path
import docx2txt
import os
from tools_used.rrf_fusion import rrf_fusion

#Creating 2 new directories for storing uplodaded files and embeddings
Path("Uploaded_Documents").mkdir(exist_ok=True)
Path("Chroma_db").mkdir(exist_ok=True)


def _extract_text(file_path:str)->str:
    path=Path(file_path)
    suffix=path.suffix.lower()
    if suffix==".pdf":
        loader=PyPDFLoader(file_path)
        docs=loader.load()
        return "\n\n".join(doc.page_content for doc in docs)
    elif suffix==".docx":
        return docx2txt.process(file_path)
    if suffix in ['.txt','.csv','.md','.py']:
        return path.read_text(encoding="utf-8",errors='ignore')
    
    raise ValueError("Error loading  the documents.")


#Embedding model
embedding_model=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
 

#Splitter
splitter=RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=200)


#Vector Database
vectorstore=Chroma(embedding_function=embedding_model,
                   persist_directory="Chroma_db",
                   collection_name="ai_study_docs")


#Store all the chunks to new file
all_chunks=[]
def document_loader(file_path: str) -> int:
    """Read, split, embed, and add a document to the vectorstore.
    Returns the number of chunks that were added.
    """
    text = _extract_text(file_path)
    if not text.strip():
        raise ValueError("No extractable text was found in this document.")
 
    chunks = splitter.split_documents([Document(page_content=text, metadata={"source": Path(file_path).name})])
    vectorstore.add_documents(chunks)
    all_chunks.extend(chunks)
    return len(chunks)



#Lets make our reteriver
def get_retriever():
    semantic_reteriver=vectorstore.as_retriever(search_type='similarity',search_kwargs={"k": 10})
    return semantic_reteriver


#BM25 
from langchain_community.retrievers import BM25Retriever
def get_bm25(all_chunks):
    bm25_retriever = BM25Retriever.from_documents(all_chunks)
    bm25_retriever.k = 10
    return bm25_retriever

#Cohere Reranker
import cohere
co = cohere.Client(os.getenv("COHERE_API_KEY"))
def cohere_reranker(query,fused_docs):
    #using reranker
    documents=[doc.page_content for doc in fused_docs]
    response = co.rerank(model="rerank-v3.5",query=query,documents=documents,top_n=5)
    reranked_docs = [fused_docs[result.index] for result in response.results]
    return reranked_docs


def fusion(all_chunks,query):
    bm25=get_bm25(all_chunks=all_chunks)
    semantic=get_retriever()
    bm25_docs = bm25.invoke(query)
    semantic_docs = semantic.invoke(query)
    fused_docs=rrf_fusion([bm25_docs,semantic_docs])
    return fused_docs


 #Reteriving from both reteriver(bm25 and semanit) 
def combine_retriever(fused_docs,query): 
    reranked_docs=cohere_reranker(query,fused_docs)
    return reranked_docs