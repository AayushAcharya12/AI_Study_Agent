from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_classic.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
import pypdf
from pypdf import PdfReader
from pathlib import Path
import docx2txt

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

#Lets make our reteriver
def get_retriever():
    retriever=vectorstore.as_retriever(search_type='similarity',search_kwargs={"k": 4})
    return retriever

def document_loader(file_path: str) -> int:
    """Read, split, embed, and add a document to the vectorstore.
 
    Returns the number of chunks that were added.
    """
    text = _extract_text(file_path)
    if not text.strip():
        raise ValueError("No extractable text was found in this document.")
 
    chunks = splitter.split_documents([Document(page_content=text, metadata={"source": Path(file_path).name})])
    vectorstore.add_documents(chunks)
    return len(chunks)