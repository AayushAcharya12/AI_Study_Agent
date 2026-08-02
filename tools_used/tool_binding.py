from .pdf_retriever_tool import retriever_tool
from .tavily_search_tool import tavily_tool
from .youtube_tool import youtube_search_tool
from src.models import llm

def bind_tool(use_gemini=False):
    """
    Bind available tools to the language model and return an LLM instance
    capable of calling retrieval, web search, and YouTube search tools.
    """
    Tools=[tavily_tool,retriever_tool,youtube_search_tool]
    llm_with_tools=llm.bind_tools(Tools)
    return llm_with_tools