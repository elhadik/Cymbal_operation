import asyncio
import websockets
import json

async def test_ws():
    try:
        async with websockets.connect('ws://localhost:8080/ws') as ws:
            msg = {
                "clientContent": {
                    "turns": [{
                        "role": "user",
                        "parts": [{"text": "hello"}]
                    }]
                }
            }
            await ws.send(json.dumps(msg))
            print("Message sent, waiting for response...")
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                print("Received:", response)
            except asyncio.TimeoutError:
                print("Timeout waiting for response")
    except Exception as e:
        print("WS Connection Error:", e)

asyncio.run(test_ws())
