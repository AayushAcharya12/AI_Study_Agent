#lets create our supervisor agent
from langgraph_supervisor import create_supervisor
from src.agents import exam_intelligent_agent,research_agent,reteriver_agent,tutor_agent,visual_learning_agent,youtube_agent
from src.prompts import SUPERVISOR_PROMPT
from tools_used import llm

#Creating supervisor agent
supervisor_agent=create_supervisor([exam_intelligent_agent,research_agent,reteriver_agent,tutor_agent,visual_learning_agent,youtube_agent],prompt=SUPERVISOR_PROMPT,model=llm)

#Compiling before invoking
supervisor_agent = supervisor_workflow.compile()