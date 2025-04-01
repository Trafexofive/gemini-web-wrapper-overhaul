# Gemini WebAPI to OpenAI API Bridge (Single Chat Instance)  
  
This FastAPI application acts as a bridge, exposing an OpenAI-compatible `/v1/chat/completions` endpoint that internally uses the unofficial `[gemini-webap](https://github.com/HanaokaYuzu/Gemini-API)i` library to interact with Google Gemini Web. This allows tools configured for the OpenAI API (like Roo Code, configured NOT to use streaming) to potentially use Gemini as the backend model.  
  
**Disclaimer:** This uses the unofficial `gemini-webapi` library, which relies on browser cookies for authentication. Changes to Google's web interface or authentication methods may break this library and, consequently, this bridge. Use at your own risk.  

# ONLY TESTED WITH ROO CODE

**Known Issues**

Currently the Architect mode will NOT send the prompt on the first interaction.
WORKAROUND: Start a new task on Roo (Just say Hi), then copy/paste the Roo Code Architect prompt into the conversation window + your task.
E.g.: 
"You are Roo, an experienced technical leader who is inquisitive and an excellent planner. Your goal is to gather information and get context to create a detailed plan for accomplishing the user's task, which the user will review and approve before they switch into another mode to implement the solution.
---- rest of the prompt ---
create a CRUD based on the following database schema"
  
## Dependencies  
  
* **Python 3.8+** (But tested only with python 3.13)  
* **FastAPI:** For the web server.  
* **gemini-webapi:** The core library interacting with Google Gemini.  
* **browser-cookie3:** Used by `gemini-webapi` to access browser cookies for authentication.  
  
Install dependencies using pip install -r requirements.txt

This is a PERSONAL project for study purposes only. USE AT YOUR OWN RISK.