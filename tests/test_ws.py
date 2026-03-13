import asyncio
import websockets
import json

async def test():
    async with websockets.connect("ws://localhost:8080/ws") as ws:
        # Trigger fulfillment flow
        print("Connected. Sending mock events...")
        await ws.send(json.dumps({
            "clientContent": {
                "turns": [{
                    "parts": [{"text": "Hello, here is my order."}]
                }]
            }
        }))
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if "serverContent" in data:
                print("Received server content.")
            else:
                print(f"Received JSON: {data}")
                
if __name__ == "__main__":
    asyncio.run(test())
