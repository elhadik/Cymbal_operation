import os
from google.adk.agents import Agent
# Plain functions will be used instead of AgentTools to prevent ADK Event return types causing Live API 1008 errors.

system_instruction = """
You are Cymbal, a pharmacy fulfillment assistant.
Your ONLY job is to process fulfillment orders using your tools.

CRITICAL RULES:
1. SILENT TOOL CALLING: When you decide to call a tool, call it IMMEDIATELY and SILENTLY. Absolutely DO NOT generate any text before calling a tool. Do NOT say "I am scanning" or "I am getting details". Just call the tool.
2. NO NARRATION: Do NOT narrate your thought process. Do NOT say "Following my instructions...".
3. BE CONCISE: Only speak when necessary, such as grabbing the user's attention or reading tool results.

SEQUENCE:
1. Briefly greet the user and ask to see their fulfillment order.
2. When the user shows a barcode, CALL `scan_barcode` SILENTLY.
3. Once scanning succeeds, CALL `get_order_details` SILENTLY.
4. Read the raw order details out loud, exactly as they are.
5. Wait for the user to confirm they have added both items.
6. CALL `conclude_order` SILENTLY and read its result.
"""

import asyncio

_events = {}
_ui_queues = {}

def get_scan_complete_event():
    loop = asyncio.get_running_loop()
    if loop not in _events:
        _events[loop] = asyncio.Event()
    return _events[loop]

def get_ui_queue():
    loop = asyncio.get_running_loop()
    if loop not in _ui_queues:
        _ui_queues[loop] = asyncio.Queue()
    return _ui_queues[loop]

async def scan_barcode() -> str:
    """Trigger this tool INSTANTLY the exact moment you physically detect a barcode on the fulfillment order."""
    print(f"--> Live API Toolkit Triggered: scan_barcode")
    
    # Send UI signal immediately to avoid deadlocking the ADK event stream
    queue = get_ui_queue()
    queue.put_nowait({"type": "barcode_detected"})

    # Get the event and clear it FIRST to prevent race conditions
    event = get_scan_complete_event()
    event.clear()
        
    # Wait for the frontend to signal that the scan animation has fully completed
    await event.wait()
    return "Barcode scanned successfully."

async def get_order_details() -> str:
    """Retrieve the fulfillment order details after scanning."""
    print(f"--> Live API Toolkit Triggered: get_order_details")
    queue = get_ui_queue()
    queue.put_nowait({
        "type": "order_parsed",
        "medicine": "Insulin",
        "refrigerated": True,
        "aisle": "Aisle 2"
    })
    return "The fulfillment order contains Insulin, which is in aisle 2 and needs to be refrigerated, and Creon, which is in aisle 4 and needs to be stored at room temperature."

def conclude_order() -> str:
    """Conclude the current order process when user finishes."""
    print(f"--> Live API Toolkit Triggered: conclude_order")
    return "You can now start the second order."

root_agent = Agent(
    name="cymbal_root_agent",
    model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-native-audio-latest"),
    instruction=system_instruction,
    tools=[scan_barcode, get_order_details, conclude_order]
)
