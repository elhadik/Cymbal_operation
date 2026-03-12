import asyncio
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from agents.conclude_agent import conclude_agent

# -----------------------------------------------------
# Tool Definition connecting Gemini Live to ADK Graph
# -----------------------------------------------------
# Define the tool that Gemini can call
async def conclude_order() -> str:
    """Trigger this tool after the user has confirmed they added both items to the order package."""
    
    print(f"--> Live API Toolkit Triggered: conclude_order")
    
    # Initialize our ADK Graph Runner
    runner = Runner(
        app_name="cymbal_operation_app",
        agent=conclude_agent,
        session_service=InMemorySessionService(),
        auto_create_session=True,
    )
    
    events = runner.run_async(
        user_id="live_api_user",
        session_id="conclude_api_session",
        new_message=types.Content(parts=[types.Part.from_text(text="Please generate the conclusion.")])
    )
    
    final_instructions = "Thank you."
    async for event in events:
        if event.is_final_response():
            if event.content and event.content.parts:
                final_instructions = event.content.parts[0].text
            elif getattr(event, 'data', None):
                if hasattr(event.data, 'instructions'):
                    final_instructions = event.data.instructions
                else:
                    final_instructions = str(event.data)
                    
    print(f"--> Tool Result: {final_instructions}")
    return final_instructions
