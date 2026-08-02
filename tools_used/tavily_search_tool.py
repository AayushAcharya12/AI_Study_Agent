#Making tavily search tool
from  pydantic import Field
from pydantic import BaseModel
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from src.config import tavily_api
class tavily_search(BaseModel):
   query: str = Field(description="The search query.")

@tool(args_schema=tavily_search)
def tavily_tool(query:str)->str:
    """
    Search the web using Tavily and return relevant information for the query.
    """
    search=TavilySearch(max_results=5,topic="general",search_depth="advanced",tavily_api_key=tavily_api)
    response=search.invoke({'query':query})
    return str(response)