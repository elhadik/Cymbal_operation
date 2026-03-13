import os
from google.adk.agents import Agent
# Plain functions will be used instead of AgentTools to prevent ADK Event return types causing Live API 1008 errors.
from agents.pathfinder_agent import run_pathfinder

system_instruction = """
You are Cymbal, a pharmacy fulfillment assistant.
Your ONLY job is to process fulfillment orders using your tools.

CRITICAL RULES:
1. SILENT TOOL CALLING: When you decide to call a tool, call it IMMEDIATELY and SILENTLY. Absolutely DO NOT generate any text before calling a tool. Do NOT say "I am scanning" or "I am getting details". Do NOT say "I am confirming pathfinder execution." Just call the tool.
2. NO NARRATION: Do NOT narrate your thought process. Do NOT say "Following my instructions...".
3. BE CONCISE: Only speak when necessary, such as grabbing the user's attention or reading tool results.

SEQUENCE:
1. Briefly greet the user and ask to see their fulfillment order.
2. When the user shows a barcode, CALL `scan_barcode` SILENTLY. DO NOT SAY A SINGLE WORD BEFORE CALLING THIS TOOL.
3. Once scanning succeeds, CALL `get_order_details` SILENTLY.
4. Read the raw order details out loud, exactly as they are.
5. Wait for the user to confirm they have added both items to the package.
6. Once the user confirms, CALL `run_pathfinder` SILENTLY. DO NOT OUTPUT ANY TEXT. DO NOT CONFIRM THE USER'S ACTION. JUST CALL THE TOOL.
7. The pathfinder tool will return a distance. You MUST respond with exactly this wording, filling in the blank: "I have displayed the delivery route map on your screen. The delivery address is [distance] away. Please confirm the route to proceed." Absolutely NO other words or apologies are allowed here.
8. Wait for the user to confirm the delivery route based on the map widget.
9. Once the user confirms the route, CALL `conclude_order` SILENTLY and read its result.
"""

import asyncio
from agents.ui_events import get_scan_complete_event, get_ui_queue

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
    tools=[scan_barcode, get_order_details, run_pathfinder, conclude_order]
)
