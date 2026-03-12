from google.adk.tools import AgentTool
from agents.order_agent import order_agent
from agents.conclude_agent import conclude_agent

# Wrapping the Workflows as callable AgentTools for the Root Agent
get_order_details = AgentTool(agent=order_agent)
conclude_order = AgentTool(agent=conclude_agent)
