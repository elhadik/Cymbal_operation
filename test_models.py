import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client()

for model in client.models.list():
    actions = getattr(model, "supported_actions", [])
    if actions and "bidiGenerateContent" in actions:
        print("Supported Bidi Model:", model.name)
