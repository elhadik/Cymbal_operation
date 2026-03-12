import asyncio
from agents.root_agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService

async def main():
    try:
        session_service = InMemorySessionService()
        runner = Runner(agent=root_agent, session_service=session_service, app_name="cymbal_fulfillment")
        print("Runner initialized")
    except Exception as e:
        print("Error:", e)

asyncio.run(main())
