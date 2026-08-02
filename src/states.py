#Creating states
from typing import TypedDict,List,Annotated
from langgraph.graph import START,END,add_messages
from langchain_core.messages  import BaseMessage


"Container of information that moves between nodes."

class AgentState(TypedDict):
    """Shared State is passed to all the states"""
    messages:Annotated[List[BaseMessage],add_messages]
    
    #User query
    query:str
    
    #Search result
    search_result:List[str]
    
    #Confidence
    confidence:float
    
    #Reterived documents
    docs:List[str]
    
    