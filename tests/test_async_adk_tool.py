import asyncio
from google.adk.agents import Agent
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.runners import Runner

async def my_tool() -> str:
    await asyncio.sleep(1)
    return "Success"

agent = Agent(name="test", model="gemini-2.5-flash", tools=[my_tool], instruction="Call my_tool")
runner = Runner(agent=agent, session_service=InMemorySessionService())
