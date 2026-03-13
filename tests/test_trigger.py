import asyncio
import websockets
import json

async def main():
    async with websockets.connect("ws://localhost:8080/ws") as ws:
        await ws.send(json.dumps({"type": "scan_completed"}))
        await asyncio.sleep(1)
        # Emulate saying we finished the checklst
        await ws.send(json.dumps({
            "clientContent": {
                "turns": [{
                    "parts": [{"text": "User clicked: Added both items to package. Please run pathfinder analysis now."}]
                }]
            }
        }))
        for i in range(10):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                m = json.loads(msg)
                print("WS RECV:", m)
            except asyncio.TimeoutError:
                break

if __name__ == "__main__":
    asyncio.run(main())
