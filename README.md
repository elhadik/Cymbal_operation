# Cymbal Operation Demo

This is a demonstration of an AI Pharmacy Fulfillment Assistant utilizing the **Gemini Live API** for real-time multimodal interaction (audio/video) and the **Google ADK 2.0 Graph Agent** for backend tool orchestration.

## Architecture
- **Frontend**: A vanilla HTML/JS web interface that captures the user's webcam and microphone and streams it over WebSockets.
- **Backend**: A Flask server (`app.py`) that acts as a bridge. It receives the WebRTC media stream over WebSockets and forwards it to the Gemini Live API.
- **Agent Backend**: A Google ADK 2.0 Agent (`agents/agent.py`) configured as a tool for Gemini. When Gemini extracts the text from a physical order shown to the camera, it calls the tool. The ADK Graph Agent parses the order and determines the inventory aisle and temperature requirements, returning the routing script for Gemini to speak aloud.

## Prerequisites
- Python 3.10+
- [`uv`](https://github.com/astral-sh/uv) (Recommended for dependency management)

## Installation from Scratch

1. **Set up the project folder:**
   ```bash
   mkdir Cymbal_operation
   cd Cymbal_operation
   ```

2. **Install the required dependencies using `uv`:**
   ```bash
   uv add quart google-genai pydantic python-dotenv google-adk
   ```

3. **Configure your Environment Variables:**
   Create a `.env` file in the root of `Cymbal_operation` and add your Gemini API Key:
   ```env
   GEMINI_API_KEY="AIzaSyYourApiKeyHere..."
   ```

## Running the Application

1. **Start the Quart Development Server:**
   Ensure you are in the `Cymbal_operation` directory, then run:
   ```bash
   uv run quart --app app run
   ```
   *Note: Set `--host=0.0.0.0` if you need to access it from another device on your local network.*

2. **Open the App:**
   Open your web browser and navigate to:
   `http://localhost:5000`
   *(Or the URL provided by your development environment)*

## Using the Demo

1. Click **"Connect & Start Live API"**.
2. Allow your browser to access your **Camera** and **Microphone**.
3. The AI (Cymbal) will introduce itself.
4. Write an order on a piece of paper or open a note on your phone (e.g., "Insulin", "Creon").
5. Hold the order up to your webcam so it is clearly visible and tell Cymbal: *"Here is my order."*
6. Cymbal will read the screen, trigger the backend ADK Graph Agent to look up the inventory locations, and read the fulfillment instructions back to you.
