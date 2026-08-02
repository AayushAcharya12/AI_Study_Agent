from typing import Annotated,List,TypedDict
from pydantic import BaseModel
from src.rag import get_retriever
from langchain_core.tools import tool

class retriever_model(BaseModel):
    query:str
    
@tool(args_schema=retriever_model)
def retriever_tool(query:str)->str:
    """
    Retrieve relevant information from uploaded study documents.

    Use this tool when the answer can be found in the user's PDFs or
    stored knowledge base. It performs similarity search and returns
    relevant document chunks for generating grounded responses.

    Args:
        query (str): User's question or search query.

    Returns:
        Relevant document contents from the knowledge base.
    """
    retriever=get_retriever()
    output=retriever.invoke(query)
    if not output:
        raise ValueError("Relevent Info Not Found")
    
    return "\n\n".join(doc.page_content for doc in output)