#Creating our graph(Currently Not Using)
from langgraph.graph import START,END,StateGraph
from langchain_core import tools
from langgraph.prebuilt import ToolNode,tools_condition
from tools_used.pdf_retriever_tool import retriever_tool
from tools_used .tavily_search_tool import tavily_tool
from tools_used.youtube_tool import youtube_search_tool
from pathlib import Path
from src.states import AgentState
from .nodes import chatbot_node

import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

#making a data folder
Path("data").mkdir(exist_ok=True)


def build_graph():
    
    graph=StateGraph(AgentState)
    
    #Adding Nodes
    graph.add_node("Chatbot_node",chatbot_node)
    tool_node = ToolNode([retriever_tool,tavily_tool,youtube_search_tool,])
    graph.add_node("tools",tool_node)
    
    #Adding edges
    graph.add_edge(START,"Chatbot_node")
    graph.add_conditional_edges("Chatbot_node",tools_condition)
    graph.add_edge("tools","Chatbot_node")
    
    
    #Making a connection with sqlite server
    conn=sqlite3.connect("data/langgraph_checkpoints.sqlite",check_same_thread=False)
    checkpointer=SqliteSaver(conn)
    
    workflow=graph.compile(checkpointer=checkpointer)
    
    return workflow