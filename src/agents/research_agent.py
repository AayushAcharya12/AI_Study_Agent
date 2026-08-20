from langchain.agents import create_agent
from src.prompts import TAVILY_SEARCH_PROMPT

research_agent = create_agent(model=llm,tools=[tavily_tool],system_prompt=TAVILY_SEARCH_PROMPT)