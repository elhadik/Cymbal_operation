import asyncio
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.tool_context import ToolContext
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from agents.order_agent import order_agent
from google.adk.events.invocation_context import InvocationContext
from google.adk.features.plugin_manager import PluginManager
from google.adk.telemetry.tracing import DummyTracerProvider

async def main():
    tool = AgentTool(agent=order_agent)
    
    ctx = ToolContext()
    ctx._invocation_context = InvocationContext(
        app_name="test",
        session_id="test_session",
        user_id="test_user",
        user_name="test",
        agent_name="test",
        agent_id="test",
        trace_provider=DummyTracerProvider(),
        plugin_manager=PluginManager(plugins=[]),
    )
    result = await tool.run_async(args={"request": "test"}, tool_context=ctx)
    print("AgentTool returned:", repr(result))

asyncio.run(main())
