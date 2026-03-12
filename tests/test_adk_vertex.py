import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
print("Has Key?", "GEMINI_API_KEY" in os.environ)

# Force Vertex AI for ADK by deleting the API key and ensuring project is set
os.environ.pop("GEMINI_API_KEY", None)
# vertexai is defaulted to True if API key is missing and project/location env vars are present in google-genai
from google.genai import Client
client = Client()
print("Is Vertex?", client.vertexai)
print("Project:", client.project)

