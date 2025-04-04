# Gemini WebAPI to OpenAI API Bridge (Multi-Session & Modes)

This FastAPI application acts as a bridge, exposing an OpenAI-compatible `/v1/chat/completions` endpoint that internally uses the unofficial [gemini-webap](https://github.com/HanaokaYuzu/Gemini-API) library to interact with Google Gemini Web. This allows tools configured for the OpenAI API (like Roo Code, configured NOT to use streaming) to potentially use Gemini as the backend model.

**Disclaimer:** This uses the unofficial `gemini-webapi` library, which relies on browser cookies for authentication. Changes to Google's web interface or authentication methods may break this library and, consequently, this bridge. Use at your own risk.

## Key Features

* **OpenAI-Compatible API:** Provides `/v1/chat/completions` endpoint.
* **Multiple Chat Sessions:** Manage multiple independent chat conversations via API.
* **Session Persistence:** Chat history and metadata are stored in a local SQLite database (`chat_sessions.db`).
* **Chat Modes:** Supports different modes (e.g., `Code`, `Architect`, `Debug`, `Ask`, `Default`) with distinct system prompts defined in `prompts.py`.
* **System Prompt Handling:** Automatically sends the appropriate system prompt when a chat session is first activated or when the mode of the active chat is changed.
* **Image Support:** Accepts Base64-encoded images within requests using the OpenAI vision format.
* **Simple Web UI:** Includes a basic web interface (served at `/`) for viewing, creating, deleting, activating, and changing the mode of chat sessions.

## Limitations

* Relies on the unofficial `gemini-webapi` and browser cookie authentication.
* Currently requires the `prompts.py` file to be present at the project root for defining mode behaviors.
* Error handling and stability, particularly regarding `gemini-webapi` interactions, might require further testing and refinement.

## Dependencies

* **Python 3.8+** (Tested primarily with Python 3.13)
* **FastAPI:** For the web server framework.
* **Uvicorn:** ASGI server to run FastAPI.
* **gemini-webapi:** The core library interacting with Google Gemini Web.
* **browser-cookie3:** Used by `gemini-webapi` for cookie access.
* **aiosqlite:** For asynchronous SQLite database access.

Install dependencies using:
```bash
pip install -r requirements.txt
```

## Authentication

`gemini-webapi` authenticates by accessing the cookies stored by your web browser. Therefore, **you must be logged into the Google Gemini website** (e.g., [https://gemini.google.com/app](https://gemini.google.com/app)) in your **default web browser** on the machine where you run this script. Ensure the browser is closed before running the script if you encounter cookie loading issues.

## Project Structure

The application code is organized within the `app/` directory:

* `app/main.py`: Main FastAPI application instance, lifespan management, static file serving.
* `app/config.py`: Static configuration (DB URL, Gemini Model, Allowed Modes).
* `app/models.py`: Pydantic models for API requests/responses.
* `app/routers/`: Defines API endpoints (e.g., `chats.py`).
    * `dependencies.py`: Reusable FastAPI dependencies.
* `app/services/`: Contains business logic (`chat_service.py`). Manages state (cache, active chat).
* `app/repositories/`: Handles data access (`chat_repository.py` for SQLite).
* `app/core/`: Core components like the Gemini client wrapper (`gemini_client.py`).
* `prompts.py`: (Located at project root) Defines the system prompts for different modes.
* `static/`: Contains frontend HTML, CSS, and JavaScript files.

## Configuration

* **Gemini Model:** Set the `GEMINI_MODEL_NAME` in `app/config.py`.
* **Database:** The database file path (`chat_sessions.db`) is configured via `DATABASE_URL` in `app/config.py`.
* **System Prompts:** The text for system prompts used by different modes is defined in `prompts.py` at the project root.

## Running the Server

Ensure you are in the project root directory (the one containing the `app/` directory and `requirements.txt`).

Run using Uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
* Replace `8000` with your desired port.
* The `--reload` flag enables auto-reloading during development. Remove it for production.
* The server will listen on the specified port on all network interfaces. Check console output for startup confirmation and potential errors.

## API Usage / Session Management

This application manages multiple chat sessions. The `/v1/chat/completions` endpoint always operates on the currently **active** session.

**Workflow:**

1.  **List Existing Chats (Optional):** `GET /v1/chats`
    * Returns a list of `ChatInfo` objects (`chat_id`, `description`, `mode`).
2.  **Create a New Chat:** `POST /v1/chats`
    * Body: `{ "description": "Optional description", "mode": "Optional ModeName" }` (Mode defaults to "Default").
    * Returns the `chat_id` (string) of the newly created session.
3.  **Activate a Chat:** `POST /v1/chats/active`
    * Body: `{ "chat_id": "your-chat-id" }`
    * Sets the specified chat as the active one for subsequent `/completions` requests.
    * **Important:** This step also triggers sending the appropriate system prompt to the Gemini session if it hasn't been sent yet for this chat's current mode (e.g., on first activation or after a mode change while inactive).
    * To deactivate, send `{ "chat_id": null }`.
4.  **Get Active Chat (Optional):** `GET /v1/chats/active`
    * Returns `{ "active_chat_id": "current-active-id" }` or `{ "active_chat_id": null }`.
5.  **Change Chat Mode:** `PUT /v1/chats/{chat_id}/mode`
    * Body: `{ "mode": "NewModeName" }` (e.g., "Code", "Ask").
    * Updates the mode for the specified chat.
    * **Important:** If the specified `chat_id` is the *currently active* chat, this endpoint immediately sends the system prompt for the *new* mode to the Gemini session. If the chat is inactive, the prompt is sent the next time it's activated via `POST /v1/chats/active`.
6.  **Send Message / Get Completion:** `POST /v1/chat/completions`
    * Uses the currently **active** chat session (set via step 3).
    * Body: Standard OpenAI format `{ "messages": [{"role": "user", "content": "Your message" or [{"type":"text",...},{"type":"image_url",...}] }], ... }`.
    * Sends *only* the user message content to the active Gemini session.
    * Returns an OpenAI-compatible `ChatCompletionResponse`.
7.  **Delete a Chat:** `DELETE /v1/chats/{chat_id}`
    * Permanently deletes the specified chat session.

**Roo Code Configuration:**
* Point Roo Code to use the API Base URL: `http://<server-ip>:<port>/v1` (e.g., `http://localhost:8000/v1`).
* Ensure that Roo is **NOT** configured to use streaming responses.

## Web UI

A simple web interface is available at the root URL (`http://<server-ip>:<port>/`) for basic chat management:
* View existing chats.
* Create new chats with descriptions and modes.
* Delete chats.
* Set the active chat.
* Change the mode (prompt) of existing chats.

## Image Handling

- The server expects images encoded as Base64 within `data:` URIs, following the OpenAI vision format.
- It decodes these images and saves them to temporary files on the server filesystem for processing by `gemini-webapi`.
- These temporary files are automatically deleted after the API call completes. Ensure the server process has permissions to write to the system's temporary directory.
- Direct `http`/`https` image URLs sent by the client are currently _ignored_.

## Error Handling

- Check the console output of the FastAPI server for errors during initialization, request handling, or interactions with the Gemini API or database.
- Common HTTP status codes include 404 (Not Found), 422 (Validation Error), 500 (Internal Server Error), 503 (Service Unavailable - e.g., DB/Gemini client init failure).

This is a PERSONAL project for study purposes only. USE AT YOUR OWN RISK.
