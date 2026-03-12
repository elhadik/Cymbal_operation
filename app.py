import asyncio
import json
import base64
import os
import traceback
from quart import Quart, render_template, websocket, request, jsonify
from dotenv import load_dotenv

from google import genai
from google.genai import types

# ADK 2 imports
from google.adk.runners import Runner
from google.adk.events.event import Event
from google.adk.agents.live_request_queue import LiveRequestQueue, LiveRequest
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from agents.root_agent import root_agent

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path)

# Verify environment
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "elhadik-sandbox-2")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")

app = Quart(__name__)

@app.route("/")
async def index():
    return await render_template("index.html")

@app.websocket("/ws")
async def ws():
    print("--> [DEBUG] Client connected to WebSocket /ws")
    
    # 1. Initialize ADK Live Queue and Runner
    live_request_queue = LiveRequestQueue()
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent, 
        session_service=session_service, 
        app_name="cymbal_fulfillment",
        auto_create_session=True
    )
    
    # We will use a dummy user id/session id to bind state
    session_id = "demo-session-1"
    user_id = "demo-user-1"
    
    # 2. Forward Live API Output from ADK to Frontend
    async def forward_events():
        from google.adk.agents.run_config import RunConfig
        try:
            # We must pass the LiveRequestQueue here as an iterator
            async for event in runner.run_live(
                user_id=user_id,
                session_id=session_id,
                live_request_queue=live_request_queue
            ):
                # We expect events to be ADK Event objects.
                # If there are content parts, convert them back to the frontend ABI
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        # AUDIO part
                        if part.inline_data and part.inline_data.mime_type.startswith("audio/"):
                            # The frontend expects a JSON payload matching the raw Gemini ABI roughly
                            audio_data = part.inline_data.data
                            audio_b64 = base64.b64encode(audio_data).decode("utf-8") if isinstance(audio_data, bytes) else audio_data
                            audio_msg = {
                                "serverContent": {
                                    "modelTurn": {
                                        "parts": [{"inlineData": {"mimeType": "audio/pcm", "data": audio_b64}}]
                                    }
                                }
                            }
                            await websocket.send(json.dumps(audio_msg))
                        
                        # TEXT part
                        elif part.text:
                            is_partial = getattr(event, "partial", False)
                            text_msg = {
                                "serverContent": {
                                    "modelTurn": {
                                        "parts": [{"text": part.text}],
                                        "isPartial": is_partial
                                    }
                                }
                            }
                            await websocket.send(json.dumps(text_msg))
                            print(f"[LIVE AGENT] -> '{part.text}'")
                            
                if getattr(event, "is_final_response", lambda: False)():
                    await websocket.send(json.dumps({"serverContent": {"turnComplete": True}}))
                
                
        except Exception as e:
            print(f"--> [DEBUG] Error in ADK forward_events: {e}")
            traceback.print_exc()
            
    # 3. Process incoming raw socket from frontend (audio/PCM base64 + JSON text)
    async def process_messages():
        try:
            while True:
                msg = await websocket.receive()
                
                # Just ignore None messages if WS closes
                if msg is None:
                    break
                    
                if isinstance(msg, str):
                    client_data = json.loads(msg)
                    
                    # 1. Handle incoming User Audio Base64 -> LiveRequest blob
                    if "realtimeInput" in client_data:
                        for media_chunk in client_data["realtimeInput"]["mediaChunks"]:
                            b64_data = media_chunk["data"]
                            mime_type = media_chunk["mimeType"] # expected audio/pcm
                            
                            req = LiveRequest(blob={"mime_type": mime_type, "data": b64_data})
                            live_request_queue.send(req)
                    
                    # 2. Handle Text "Client Content" (Tool responses are now native to ADK!)
                    elif "clientContent" in client_data:
                        # E.g. user sends simple text message
                        turns = client_data["clientContent"]["turns"]
                        for turn in turns:
                            for part in turn["parts"]:
                                if "text" in part:
                                    content = types.Content(role="user", parts=[types.Part.from_text(text=part["text"])])
                                    req = LiveRequest(content=content)
                                    live_request_queue.send(req)
                                    
                    # 3. Handle Image Frames
                    elif client_data.get("type") == "image":
                        base64_img = client_data.get("data")
                        if base64_img and "," in base64_img:
                            mime_header, b64_data = base64_img.split(",", 1)
                            mime_type = "image/jpeg" if "jpeg" in mime_header else "image/png"
                            req = LiveRequest(blob={"mime_type": mime_type, "data": b64_data})
                            live_request_queue.send(req)

                    # 4. Handle Scan Completed Signal
                    elif client_data.get("type") == "scan_completed":
                        print("--> [DEBUG] Received scan_completed from frontend")
                        from agents.root_agent import get_scan_complete_event
                        get_scan_complete_event().set()

                    # Note: We no longer need to send Tool Responses manually.
                    # ADK intercepts the LLM tool requests, executes the functions, and sends the ToolResponse payloads automatically!
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"--> [DEBUG] Error in process_messages loop: {e}")
            traceback.print_exc()
            
    async def forward_ui_signals():
        from agents.root_agent import get_ui_queue
        ui_queue = get_ui_queue()
        try:
            while True:
                msg = await ui_queue.get()
                await websocket.send(json.dumps(msg))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"--> [DEBUG] Error in forward_ui_signals: {e}")
            traceback.print_exc()

    # Launch ADK graph engine and network socket proxy
    tasks = [
        asyncio.create_task(forward_events()),
        asyncio.create_task(process_messages()),
        asyncio.create_task(forward_ui_signals())
    ]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
    
    for task in pending:
        task.cancel()
    
    # Notify Queue to shutdown gracefully
    live_request_queue.close()
    print("--> [DEBUG] WebSocket connection closed")

@app.route("/barcode", methods=['POST'])
async def generate_barcode():
    # Helper to spoof barcode ID values based on medicine name
    data = await request.get_json()
    item_id = data.get('item_id', 'unknown')
    if item_id.lower() == 'insulin':
         barcode_number = 'A2-REF-INS-001'
    elif item_id.lower() == 'creon':
         barcode_number = 'A4-ROOM-CRE-002'
    else:
         barcode_number = 'UNK-000-000'
    return jsonify({"barcode": barcode_number})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
