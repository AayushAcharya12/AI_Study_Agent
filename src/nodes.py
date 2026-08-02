#Creating nodes for chatbot
from .states import AgentState
from langchain_core.messages import SystemMessage
from src.prompts import SYSTEM_PROMPT
from tools_used.tool_binding import bind_tool
llm_with_tools=bind_tool()

def chatbot_node(state:AgentState)->AgentState:
    """"
        Main reasoning node of the AI Study Agent.

    This node receives the current AgentState containing the conversation
    history and processes the user's query using the configured LLM.

    The LLM acts as the decision-maker and determines whether the query
    can be answered directly or requires external tools.

    Available tools:
        1. PDF RAG Tool:
            - Retrieves relevant information from uploaded study materials.
            - Used for answering questions based on user-provided documents.

        2. Tavily Search Tool:
            - Performs web searches for up-to-date or external information.
            - Used when required information is not available in the knowledge base.

        3. YouTube Search Tool:
            - Finds relevant educational videos related to the user's query.
            - Used for visual learning resources and additional explanations.

    Workflow:
        - Reads previous conversation messages from the state.
        - Sends the context to the LLM.
        - Allows the LLM to decide tool usage.
        - Generates an AI response.
        - Updates the message history in AgentState.

    Args:
        state (AgentState):
            Current graph state containing conversation messages
            and other shared information.

    Returns:
        dict:
            Updated state containing the AI-generated response.
    """
    MAX_HISTORY = 10
    messages=state['messages']
    messages=[SystemMessage(content=SYSTEM_PROMPT)]+state['messages'][-MAX_HISTORY:]
    response=llm_with_tools.invoke(messages)
    return {'messages':[response]}
    