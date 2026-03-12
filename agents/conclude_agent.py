from google.adk.workflow import Workflow
from google.adk.workflow.workflow_graph import START
from google.adk.events.event import Event
from pydantic import BaseModel
from typing import Any

# -----------------------------------------------------
# Schemas
# -----------------------------------------------------
class ConcludeInstructions(BaseModel):
    instructions: str

from google.genai import types

from google.adk.events.event import Event, EventActions

# -----------------------------------------------------
# Node: Conclude Operator
# -----------------------------------------------------
def generate_conclusion(input_data: Any = None):
    # Depending on complex state or context later, this could be dynamic.
    # For now, it returns the standard conclusion.
    instruction_text = "You can now start the second order."
    return Event(
        content=types.Content(
            role='model',
            parts=[types.Part.from_text(text=instruction_text)]
        ),
        actions=EventActions(
            is_terminal_output=True,
            state_delta={"conclusion": instruction_text}
        )
    )

# -----------------------------------------------------
# Assemble the graph
# -----------------------------------------------------
conclude_agent = Workflow(
    name="conclude_order",
    edges=[
        (START, generate_conclusion)
    ],
)
