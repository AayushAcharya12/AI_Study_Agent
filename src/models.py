from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from .config import groq_api,tavily_api,youtube_api,google_api


#Primary fallback(Gemini)
gemini_llm=ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite",temperature=0.3,api_key=google_api)


#First Model(Groq)
groq_llm1=ChatGroq(model="llama-3.3-70b-versatile",groq_api_key=groq_api,temperature=0.3,max_tokens=500)


#Second fallback(Groq)
groq_llm2=ChatGroq(model="qwen/qwen3-32b",groq_api_key=groq_api,temperature=0.3,max_tokens=500)

from langchain_tavily  import TavilySearch
tavily_search=TavilySearch(max_results=4,topic="general",search_depth="advanced",tavily_api_key=tavily_api)

from googleapiclient.discovery import build
youtube = build("youtube", "v3",developerKey=youtube_api)

llm = groq_llm1.with_fallbacks([groq_llm2, gemini_llm])