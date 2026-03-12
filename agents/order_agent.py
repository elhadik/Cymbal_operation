from google.adk.workflow import Workflow
from google.adk.workflow.workflow_graph import START
from google.adk.events.event import Event
from pydantic import BaseModel
from typing import Any

# -----------------------------------------------------
# Schemas
# -----------------------------------------------------
class OrderInstructions(BaseModel):
    instructions: str

from google.genai import types

from google.adk.events.event import Event, EventActions

# -----------------------------------------------------
# Node: Order Processor
# -----------------------------------------------------
def process_order(input_data: Any = None):
    # This replaces the get_order_details tool functionality 
    # and processes the simulated DB lookup
    from agents.root_agent import _ui_queues
    try:
        if _ui_queues:
            loop = list(_ui_queues.keys())[0]
            queue = list(_ui_queues.values())[0]
            loop.call_soon_threadsafe(queue.put_nowait, {"type": "order_parsed", "medicine": "multiple", "aisle": "multiple"})
    except Exception as e:
        print(f"--> [DEBUG] Failed to put UI signal in process_order: {e}")
    
    order_details = "The fulfillment order contains Insulin, which is in aisle 2 and needs to be refrigerated, and Creon, which is in aisle 4 and needs to be stored at room temperature."
    return Event(
        content=types.Content(
            role='model',
            parts=[types.Part.from_text(text=order_details)]
        ),
        actions=EventActions(
            is_terminal_output=True,
            state_delta={"order_details": order_details}
        )
    )

# -----------------------------------------------------
# Assemble the graph
# -----------------------------------------------------
order_agent = Workflow(
    name="get_order_details",
    edges=[
        (START, process_order)
    ],
)
