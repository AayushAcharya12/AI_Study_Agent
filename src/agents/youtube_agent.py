from langchain.agents import create_agent
from src.prompts import YOUTUBE_AGENT_PROMPT

youtube_agent = create_agent(model=llm,tools=[youtube_search_tool],system_prompt=YOUTUBE_AGENT_PROMPT)