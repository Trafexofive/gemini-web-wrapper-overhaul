# Gemini WebAPI to OpenAI API Bridge (Single Chat Instance)  
  
This FastAPI application acts as a bridge, exposing an OpenAI-compatible `/v1/chat/completions` endpoint that internally uses the unofficial [gemini-webap](https://github.com/HanaokaYuzu/Gemini-API) library to interact with Google Gemini Web. This allows tools configured for the OpenAI API (like Roo Code, configured NOT to use streaming) to potentially use Gemini as the backend model.  
  
**Disclaimer:** This uses the unofficial `gemini-webapi` library, which relies on browser cookies for authentication. Changes to Google's web interface or authentication methods may break this library and, consequently, this bridge. Use at your own risk.  

# ONLY TESTED WITH ROO CODE

**Known Issues**

Currently the Architect mode will NOT send the prompt on the first interaction.
WORKAROUND: Start a new task on Roo (Just say Hi), then copy/paste the Roo Code Architect prompt into the conversation window + your task.
E.g.: 
"You are Roo, an experienced technical leader who is inquisitive and an excellent planner. Your goal is to gather information and get context to create a detailed plan for accomplishing the user's task, which the user will review and approve before they switch into another mode to implement the solution.
---- rest of the prompt ---
create a CRUD based on the following database schema"

Also when on coding mode, it will randomly start returning error 500 and the only way to work around it is to start a new task.
  
## Dependencies  
  
* **Python 3.8+** (But tested only with python 3.13)  
* **FastAPI:** For the web server.  
* **gemini-webapi:** The core library interacting with Google Gemini.  
* **browser-cookie3:** Used by `gemini-webapi` to access browser cookies for authentication.  
  
Install dependencies using pip install -r requirements.txt

## Authentication

`gemini-webapi` authenticates by accessing the cookies stored by your web browser. Therefore, **you must be logged into the Google Gemini website** (e.g., [https://gemini.google.com/app](https://gemini.google.com/app)) in your **default web browser** on the machine where you run this script. Ensure the browser is closed before running the script if you encounter cookie loading issues.

## Usage

1. **Configure Model:** Edit the `GEMINI_MODEL_NAME` variable in the Python script (`gemini_api.py` or your filename) to the desired Gemini model string supported by `gemini-webapi` (e.g., `"gemini-2.5-exp-advanced"`).
2. **Run the Server:**
    
    Bash
    
    ```
    python your_script_name.py
    ```
    
    Or using Uvicorn directly:
    
    Bash
    
    ```
    uvicorn your_script_name:app --host 0.0.0.0 --port 8099
    ```
    
    The server will listen on port `8099` on all network interfaces. Check the console output to confirm the global chat initialized successfully.
3. **Configure Client (e.g., Roo Code):**
    - Point your client tool to use the API Base URL: `http://<ip-address-of-your-server>:8099/v1`
    - Ensure the client is **NOT** configured to use streaming responses. The endpoint currently only supports non-streaming responses.
    - The client should send requests to the `/chat/completions` path relative to the base URL (e.g., POST to `http://<ip-address-of-your-server>:8099/v1/chat/completions`).

## CRITICAL LIMITATION: Single Global Chat Instance

- This application currently initializes **one single, global chat instance** when it starts.
- **All incoming requests share this same chat instance.** This means the conversation history and context are shared across all clients and requests hitting the server simultaneously.
- This can lead to unexpected behavior or context mixing if multiple independent tasks or users interact with the server concurrently.
- **To start a completely fresh conversation** (e.g., for a new, independent task in Roo Code, or if the current shared conversation becomes confused), you **MUST RESTART** the FastAPI application (stop the `python` or `uvicorn` process and start it again). Restarting clears the server's memory and forces the initialization of a new global chat instance.

## Error Handling

- Check the console output of the FastAPI server for critical errors during initialization or request processing.
- `503 Service Unavailable` likely means the `gemini-webapi` client or the global chat failed to initialize.
- `400 Bad Request` might indicate invalid JSON from the client.
- `422 Unprocessable Entity` indicates the JSON structure sent by the client doesn't match the expected OpenAI format (check Pydantic validation errors in the server console).
- `500 Internal Server Error` likely indicates a problem during the interaction with the `gemini-webapi` library itself (check server console logs and tracebacks).

This is a PERSONAL project for study purposes only. USE AT YOUR OWN RISK.
