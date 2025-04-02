# Gemini WebAPI to OpenAI API Bridge (Single Chat Instance)  
  
This FastAPI application acts as a bridge, exposing an OpenAI-compatible `/v1/chat/completions` endpoint that internally uses the unofficial [gemini-webap](https://github.com/HanaokaYuzu/Gemini-API) library to interact with Google Gemini Web. This allows tools configured for the OpenAI API (like Roo Code, configured NOT to use streaming) to potentially use Gemini as the backend model.  
  
**Disclaimer:** This uses the unofficial `gemini-webapi` library, which relies on browser cookies for authentication. Changes to Google's web interface or authentication methods may break this library and, consequently, this bridge. Use at your own risk.  

# ONLY TESTED WITH ROO CODE

**Known Issues**

Since this is the web version of Gemini, it DOES NOT take system prompts.
WORKAROUND: Start a new task on Roo (Just say Hi), then copy/paste the Roo Code prompt for the model you're using into the conversation window + your task.
E.g.: 
"You are Roo, an experienced technical leader who is inquisitive and an excellent planner. Your goal is to gather information and get context to create a detailed plan for accomplishing the user's task, which the user will review and approve before they switch into another mode to implement the solution.
---- rest of the prompt ---
create a CRUD based on the following database schema"

P.s: I THINK that when changing between modes (E.g.: from Architect to Coder), it will then send the whole prompt to the conversation, but I need further investigation.

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
    python gemini_api.py
    ```
    
    Or using Uvicorn directly:
    
    Bash
    
    ```
    uvicorn gemini_api:app --host 0.0.0.0 --port 8099
    ```
    
    The server will listen on port `8099` on all network interfaces. Check the console output to confirm the global chat initialized successfully.
3. **Configure Client (e.g., Roo Code):**
    - Point your client tool to use the API Base URL: `http://<ip-address-of-your-server>:8099/v1`
    - Ensure the client is **NOT** configured to use streaming responses. The endpoint currently only supports non-streaming responses.
    - The client should send requests to the `/chat/completions` path relative to the base URL (e.g., POST to `http://<ip-address-of-your-server>:8099/v1/chat/completions`).

4. **Configure Client (e.g., Roo Code):**
    - Point your client tool to use the API Base URL: `http://<ip-address-of-your-server>:8050/v1`
    - Ensure the client is **NOT** configured to use streaming responses.
    - The client should send requests to the `/chat/completions` path relative to the base URL.
    - The client can now send messages containing image data using the standard OpenAI list format with `type: "image_url"` and `image_url: {"url": "data:image/..."}`.

## CRITICAL LIMITATION: Single Global Chat Instance

- This application currently initializes **one single, global chat instance** when it starts.
- **All incoming requests share this same chat instance.** This means the conversation history and context (including context derived from images sent in previous turns _within the same server run_) are shared across all clients and requests hitting the server simultaneously.
- This can lead to unexpected behavior or context mixing if multiple independent tasks or users interact with the server concurrently.
- **To start a completely fresh conversation** (e.g., for a new, independent task in Roo Code, or if the current shared conversation becomes confused), you **MUST RESTART** the FastAPI application (stop the `python` or `uvicorn` process and start it again). Restarting clears the server's memory and forces the initialization of a new global chat instance.

## Image Handling

- The server expects images encoded as Base64 within `data:` URIs, following the OpenAI vision format.
- It decodes these images and saves them to temporary files on the server filesystem for processing by `gemini-webapi`.
- These temporary files are automatically deleted after the API call completes. Ensure the server process has permissions to write to the system's temporary directory.
- Direct `http`/`https` image URLs sent by the client are currently _ignored_ (support could be added by implementing image downloading).

## Error Handling

- Check the console output of the FastAPI server for errors during initialization, image processing, or request handling.
- Common errors are similar to the previous version (503, 400, 422, 500), with potential new errors related to image decoding or temporary file handling.

This is a PERSONAL project for study purposes only. USE AT YOUR OWN RISK.
