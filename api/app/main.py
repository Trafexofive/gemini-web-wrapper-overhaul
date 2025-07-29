# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import aiosqlite
import os
from pathlib import Path

from app.repositories.chat_repository import SqliteChatRepository
from app.repositories.message_repository import SqliteMessageRepository
from app.core.gemini_client_hybrid import GeminiClientHybrid
from app.services.chat_service_hybrid import ChatServiceHybrid
from app.services.auth_service import AuthService
from app.routers.chats import router as chats_router
from app.routers.messages import router as messages_router
from app.routers.auth import router as auth_router
from app.config import DATABASE_URL

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- Application Lifespan: Startup Initiated ---")
    app.state.db_conn = None
    app.state.gemini_client = None
    app.state.repository = None
    app.state.chat_service = None
    app.state.auth_service = None

    # 1. Initialize Database Tables (creates if not exists)
    try:
        await SqliteChatRepository.initialize_db()
        await SqliteMessageRepository.initialize_db()
        await AuthService.initialize_db()  # Initialize auth tables
    except Exception as init_db_e:
        print(f"FATAL: Database table initialization failed: {init_db_e}")
        raise RuntimeError("Failed to initialize database tables") from init_db_e

    # 2. Establish Shared Database Connection
    db_conn = None
    try:
        db_conn = await aiosqlite.connect(DATABASE_URL)
        app.state.db_conn = db_conn
        print("Database connection established successfully.")
    except Exception as db_e:
        print(f"FATAL: Database connection failed: {db_e}")
        raise RuntimeError("Failed to establish database connection") from db_e

    # 3. Initialize Authentication Service
    auth_service = None
    try:
        auth_service = AuthService()
        app.state.auth_service = auth_service
        print("Authentication service initialized successfully.")
    except Exception as auth_e:
        print(f"FATAL: Authentication service initialization failed: {auth_e}")
        if db_conn: await db_conn.close()
        raise RuntimeError("Failed to initialize authentication service") from auth_e

    # 4. Initialize Gemini Client Hybrid (supports both free and paid modes)
    gemini_client = None
    try:
        gemini_client = GeminiClientHybrid()
        # Initialize in free mode by default
        success = await gemini_client.init_client(mode="free")
        if not success:
            print("WARNING: Failed to initialize in free mode, trying paid mode...")
            success = await gemini_client.init_client(mode="paid")
            if not success:
                raise RuntimeError("Failed to initialize in both free and paid modes")
        
        app.state.gemini_client = gemini_client
        print(f"Gemini Client Hybrid initialized successfully in {gemini_client.mode} mode.")
    except Exception as gemini_e:
        print(f"FATAL: Gemini Client Hybrid initialization failed: {gemini_e}")
        if db_conn: await db_conn.close()
        raise RuntimeError("Failed to initialize Gemini client") from gemini_e

    # 5. Create Chat Repository Instance
    repository = SqliteChatRepository()
    app.state.repository = repository
    print("Chat Repository instance created.")

    # 6. Create Service Hybrid Instance (injecting repository and client)
    chat_service = ChatServiceHybrid(repository=repository, gemini_client=gemini_client)
    app.state.chat_service = chat_service
    print("Chat Service Hybrid instance created.")

    # 7. Load Initial Service Cache from DB
    try:
        await chat_service.load_initial_cache(db_conn)
        print("Initial service cache loaded from database.")
    except Exception as cache_e:
        print(f"WARNING: Failed to load initial cache: {cache_e}")

    yield  # Application runs

    # Cleanup: Close resources in reverse order of creation
    # 1. Close Gemini Client Hybrid
    if hasattr(app.state, 'gemini_client') and app.state.gemini_client:
        try:
            await app.state.gemini_client.close_client()
            print("Gemini Client Hybrid closed during shutdown.")
        except Exception as close_gemini_e:
            print(f"Error closing Gemini Client Hybrid during shutdown: {close_gemini_e}")

    # 2. Close Database Connection
    if hasattr(app.state, 'db_conn') and app.state.db_conn:
        try:
            await app.state.db_conn.close()
            print("Database connection closed during shutdown.")
        except Exception as close_db_e:
            print(f"Error closing database connection during shutdown: {close_db_e}")

    print("--- Application Lifespan: Shutdown Complete ---")

# Create FastAPI app
app = FastAPI(
    title="Gemini Web Wrapper API",
    description="A hybrid API for Gemini Web Wrapper supporting both free (cookies) and paid (API key) modes with full authentication",
    version="4.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://gemini-frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(chats_router)
app.include_router(messages_router)

@app.get("/test-main")
async def test_main():
    """Test endpoint in main.py."""
    return {"message": "Main router is working"}

# Serve static files if directory exists
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")
    print(f"Static files mounted at /static")
else:
    print("WARNING: Static directory not found, skipping static file mounting")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page."""
    try:
        if static_dir.exists():
            with open("static/manage_chats.html", "r") as f:
                return HTMLResponse(content=f.read())
    except FileNotFoundError:
        pass
    
    # Fallback response
    return HTMLResponse(content="""
    <html>
        <head><title>Gemini Web Wrapper API</title></head>
        <body>
            <h1>Gemini Web Wrapper API</h1>
            <p>API is running. Check the <a href="/docs">docs</a> for endpoints.</p>
            <p>Current client mode: <span id="mode">Loading...</span></p>
            <script>
                fetch('/api/v1/chats/client-mode')
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('mode').textContent = data.mode + ' - ' + data.description;
                    })
                    .catch(e => {
                        document.getElementById('mode').textContent = 'Error loading mode';
                    });
            </script>
        </body>
    </html>
    """)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "4.0.0"}