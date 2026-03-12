import asyncio
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from agents.order_agent import order_agent
from google.genai import types

async def main():
    runner = Runner(
        agent=order_agent,
        session_service=InMemorySessionService(),
        app_name="test"
    )
    session = await runner.session_service.create_session(
        app_name="test",
        user_id="user",
    )
    content = types.Content(
        role='user',
        parts=[types.Part.from_text(text="test")],
    )
    async for event in runner.run_async(user_id="user", session_id=session.id, new_message=content):
        print("Event schema:", event)
        if event.content:
            print("Event Content:", event.content)

asyncio.run(main())
