# app/main.py
import aiosqlite
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, status # Added status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

# Import components from the app package
from app.config import DATABASE_URL
from app.core.gemini_client import GeminiClientWrapper
from app.repositories.chat_repository import SqliteChatRepository
from app.services.chat_service import ChatService
from app.routers.chats import router as chats_router

# Determine paths relative to this main.py file
current_script_dir = Path(__file__).parent
# Static files are one level up from 'app' directory
static_dir_path = (current_script_dir.parent / "static").resolve()
# Extract DB path from config URL
db_path = DATABASE_URL.split("///")[-1]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events: startup and shutdown.
    Initializes and closes resources like DB connections and external clients.
    Stores shared instances on app.state.
    """
    print("--- Application Lifespan: Startup Initiated ---")
    app.state.db_conn = None # Ensure state attributes exist even if setup fails
    app.state.gemini_wrapper = None
    app.state.repository = None
    app.state.chat_service = None

    # 1. Initialize Database Table (creates if not exists)
    try:
        await SqliteChatRepository.initialize_db()
    except Exception as init_db_e:
        print(f"FATAL: Database table initialization failed: {init_db_e}")
        # Raising prevents app from starting if DB table init fails
        raise RuntimeError("Failed to initialize database table") from init_db_e

    # 2. Establish Shared Database Connection
    db_conn = None
    try:
        print(f"Connecting to database at: {db_path}")
        db_conn = await aiosqlite.connect(db_path)
        # Set WAL mode for better concurrency
        await db_conn.execute("PRAGMA journal_mode=WAL;")
        await db_conn.commit() # Commit journal mode change
        app.state.db_conn = db_conn # Store connection on app state
        print("Database connection established (WAL mode enabled).")
    except Exception as conn_db_e:
        print(f"FATAL: Database connection failed: {conn_db_e}")
        if db_conn: await db_conn.close() # Attempt close if connection object exists
        raise RuntimeError("Failed to connect to database") from conn_db_e

    # 3. Initialize Gemini Client Wrapper
    gemini_wrapper = GeminiClientWrapper()
    try:
        await gemini_wrapper.init_client() # Uses default timeout
        if not gemini_wrapper._client: # Verify initialization success internally
             raise RuntimeError("Gemini client initialization method completed but client instance is still None.")
        app.state.gemini_wrapper = gemini_wrapper # Store wrapper on app state
        print("Gemini Client Wrapper initialized successfully.")
    except Exception as gemini_e:
        print(f"FATAL: Gemini Client initialization failed: {gemini_e}")
        # Close DB connection before raising error, as Gemini client is essential
        if db_conn: await db_conn.close()
        raise RuntimeError("Failed to initialize Gemini client") from gemini_e

    # 4. Create Repository Instance (stateless, just needs creation)
    repository = SqliteChatRepository()
    app.state.repository = repository
    print("Chat Repository instance created.")

    # 5. Create Service Instance (injecting repository and client wrapper)
    # Service instance holds in-memory state (cache, active_id)
    chat_service = ChatService(repository=repository, gemini_wrapper=gemini_wrapper)
    app.state.chat_service = chat_service
    print("Chat Service instance created.")

    # 6. Load Initial Service Cache from DB
    try:
        print("Attempting to load initial chat service cache...")
        await chat_service.load_initial_cache(db_conn) # Pass the established connection
        print("Initial chat service cache loading process completed.")
    except Exception as cache_e:
        # Log error but allow app to continue, cache will be empty/partially loaded
        print(f"WARNING: Failed to load initial cache during startup: {cache_e}")

    print("--- Application Startup Successfully Completed ---")
    yield # Application runs here...
    print("--- Application Lifespan: Shutdown Initiated ---")

    # Cleanup: Close resources in reverse order of creation

    # 1. Close Gemini Client (via wrapper)
    if hasattr(app.state, 'gemini_wrapper') and app.state.gemini_wrapper:
        print("Closing Gemini Client...")
        await app.state.gemini_wrapper.close_client()
    else:
        print("Gemini Wrapper not found in state or already closed.")

    # 2. Close Database Connection
    if hasattr(app.state, 'db_conn') and app.state.db_conn:
        print("Closing database connection...")
        await app.state.db_conn.close()
        print("Database connection closed.")
    else:
        print("Database connection not found in state or already closed.")

    print("--- Application Shutdown Complete ---")


# Create FastAPI app instance with title, description, version, and lifespan
app = FastAPI(
    title="Gemini FastAPI Wrapper",
    description="A refactored API wrapper for Google Gemini with session management.",
    version="1.1.0", # Incremented version after refactor
    lifespan=lifespan
)

# Include the API router defined in app/routers/chats.py
app.include_router(chats_router)

# Mount static files directory (for the frontend)
if static_dir_path.is_dir():
    print(f"Mounting static directory: {static_dir_path} at /static")
    app.mount("/static", StaticFiles(directory=static_dir_path), name="static")
else:
    # Log a warning if the static directory doesn't exist
    print(f"WARNING: Static directory not found at '{static_dir_path}'. Frontend will not be served.")

# Serve the main frontend HTML page from the static directory at the root URL
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_index_page():
    """Serves the main HTML frontend page (manage_chats.html)."""
    index_path = static_dir_path / "manage_chats.html"
    if not index_path.is_file():
        print(f"ERROR: Frontend entry point file '{index_path}' not found!")
        # Return 404 if the main HTML file is missing
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Frontend entry point not found.")
    try:
        # Read and return the content of the HTML file
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        print(f"ERROR reading frontend file '{index_path}': {e}")
        # Return 500 if there's an error reading the file
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error serving frontend.")

# Basic health check endpoint
@app.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
async def health_check():
    """Simple health check endpoint to confirm the API is running."""
    return {"status": "ok"}

# Reminder for running the application:
# Use a command like: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000