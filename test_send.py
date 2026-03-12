import inspect
from google import genai
import asyncio

async def test():
    client = genai.Client()
    # We can't easily instantiate a session without connecting, but we can look at the Session class.
    # Where does the Session class live?
    from google.genai.live import Session
    print("Session.send signature:", inspect.signature(Session.send))

asyncio.run(test())
