# app/repositories/chat_repository.py
import aiosqlite
import json
from typing import List, Optional, Dict, Any, Tuple
from app.models import ChatInfo # Assuming ChatInfo is defined in app.models
from app.config import DATABASE_URL # Needed for initialization connection

# Could define a Protocol for the interface here for better type hinting and testing

class SqliteChatRepository:
    """Repository for chat session data using aiosqlite."""

    # Store the path extracted from the DATABASE_URL
    db_path = DATABASE_URL.split("///")[-1]

    @staticmethod
    async def initialize_db():
        """Creates the sessions table if it doesn't exist. Should be called during app lifespan startup."""
        print(f"Initializing database table 'sessions' at: {SqliteChatRepository.db_path}")
        try:
            async with aiosqlite.connect(SqliteChatRepository.db_path) as db:
                # Enable Write-Ahead Logging for better concurrency with reads/writes
                await db.execute("PRAGMA journal_mode=WAL;")
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        chat_id TEXT PRIMARY KEY,
                        metadata_json TEXT NOT NULL,
                        description TEXT,
                        mode TEXT,
                        system_prompt_sent BOOLEAN DEFAULT FALSE NOT NULL,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                await db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_chat_id ON sessions(chat_id)")
                # Trigger to update last_updated automatically on UPDATE
                await db.execute("""
                    CREATE TRIGGER IF NOT EXISTS update_last_updated_after_update
                    AFTER UPDATE ON sessions FOR EACH ROW
                    WHEN OLD.metadata_json <> NEW.metadata_json OR OLD.description <> NEW.description OR OLD.mode <> NEW.mode OR OLD.system_prompt_sent <> NEW.system_prompt_sent
                    BEGIN
                        UPDATE sessions SET last_updated = CURRENT_TIMESTAMP WHERE chat_id = OLD.chat_id;
                    END;
                """)
                await db.commit()
                print("Database table 'sessions' initialized successfully.")
        except Exception as e:
            print(f"!!!!!!!! DATABASE INITIALIZATION FAILED !!!!!!!! Error: {e}")
            # Depending on requirements, might want to raise this to stop app startup
            raise RuntimeError(f"Failed to initialize database: {e}") from e

    # Note: Methods below assume an active aiosqlite.Connection 'db' is passed in.
    # This connection should be managed externally (e.g., via lifespan and dependency injection).

    async def get_chat_info_list(self, db: aiosqlite.Connection) -> List[ChatInfo]:
        """Fetches basic info (id, description, mode) for all chats."""
        chats = []
        try:
            db.row_factory = aiosqlite.Row # Access columns by name
            async with db.execute("SELECT chat_id, description, mode FROM sessions ORDER BY last_updated DESC") as cursor:
                rows = await cursor.fetchall()
                chats = [ChatInfo(chat_id=row["chat_id"], description=row["description"], mode=row["mode"]) for row in rows]
        except Exception as e:
            print(f"Repository Error in get_chat_info_list: {e}")
            # Return empty list, let service layer decide how to handle
        return chats

    async def get_all_session_data(self, db: aiosqlite.Connection) -> Dict[str, Dict[str, Any]]:
        """Loads metadata, mode, and prompt flag for all sessions (intended for cache hydration)."""
        sessions_cache: Dict[str, Dict[str, Any]] = {}
        try:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT chat_id, metadata_json, mode, system_prompt_sent FROM sessions") as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    chat_id = row["chat_id"]
                    try:
                        metadata = json.loads(row["metadata_json"])
                        prompt_sent = bool(row["system_prompt_sent"]) # Convert DB 0/1 to bool
                        sessions_cache[chat_id] = {"metadata": metadata, "mode": row["mode"], "prompt_sent": prompt_sent}
                    except json.JSONDecodeError:
                        print(f"Warning: Bad JSON metadata for chat_id '{chat_id}' in get_all_session_data. Skipping.")
                    except Exception as inner_e:
                         print(f"Warning: Error processing row for chat_id '{chat_id}' in get_all_session_data: {inner_e}. Skipping.")

        except Exception as e:
            print(f"Repository Error in get_all_session_data: {e}")
            # Return empty dict, let service layer decide how to handle
        return sessions_cache

    async def get_session_data(self, db: aiosqlite.Connection, chat_id: str) -> Optional[Dict[str, Any]]:
        """Loads metadata, mode, and prompt flag for a single session by ID."""
        try:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT metadata_json, mode, system_prompt_sent FROM sessions WHERE chat_id = ?", (chat_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    try:
                        metadata = json.loads(row["metadata_json"])
                        prompt_sent = bool(row["system_prompt_sent"])
                        return {"metadata": metadata, "mode": row["mode"], "prompt_sent": prompt_sent}
                    except json.JSONDecodeError:
                        print(f"Warning: Bad JSON metadata for chat_id '{chat_id}' in get_session_data. Returning None.")
                        return None
                else:
                    return None # Chat ID not found
        except Exception as e:
            print(f"Repository Error in get_session_data for chat_id '{chat_id}': {e}")
            return None # Return None on error

    async def create_chat(self, db: aiosqlite.Connection, chat_id: str, metadata: dict, description: str | None, mode: str | None) -> bool:
        """Creates a new chat session record."""
        success = False
        try:
            metadata_json = json.dumps(metadata)
            # system_prompt_sent defaults to FALSE in schema definition
            await db.execute(
                "INSERT INTO sessions (chat_id, metadata_json, description, mode) VALUES (?, ?, ?, ?)",
                (chat_id, metadata_json, description, mode)
            )
            await db.commit()
            success = True
            print(f"Repository: Session CREATED in DB: {chat_id}")
        except aiosqlite.IntegrityError:
            # This is an expected error if the chat_id already exists
            print(f"Repository Warning: Session '{chat_id}' already exists (IntegrityError).")
            # Consider if this should return True or False, or raise a specific exception
            # Returning False indicates it wasn't newly created.
            pass # Keep success = False
        except Exception as e:
            print(f"Repository Error CREATING session '{chat_id}': {e}")
            try: await db.rollback()
            except Exception as rb_e: print(f"Rollback failed after create_chat error: {rb_e}")
        return success

    async def update_metadata(self, db: aiosqlite.Connection, chat_id: str, metadata: dict) -> bool:
        """Updates only the metadata for a specific chat session."""
        success = False
        try:
            metadata_json = json.dumps(metadata)
            # The trigger should handle last_updated
            cursor = await db.execute(
                "UPDATE sessions SET metadata_json = ? WHERE chat_id = ?",
                (metadata_json, chat_id)
            )
            await db.commit()
            success = cursor.rowcount > 0
            await cursor.close()
            if not success:
                print(f"Repository Warning: update_metadata - No rows updated for chat_id '{chat_id}'.")
        except Exception as e:
            print(f"Repository Error UPDATING metadata for '{chat_id}': {e}")
            try: await db.rollback()
            except Exception as rb_e: print(f"Rollback failed after update_metadata error: {rb_e}")
        return success

    async def mark_prompt_sent(self, db: aiosqlite.Connection, chat_id: str) -> bool:
        """Sets the system_prompt_sent flag to TRUE for a specific chat session."""
        success = False
        try:
            cursor = await db.execute(
                "UPDATE sessions SET system_prompt_sent = TRUE WHERE chat_id = ?",
                (chat_id,)
            )
            await db.commit()
            success = cursor.rowcount > 0
            await cursor.close()
            if not success:
                print(f"Repository Warning: mark_prompt_sent - No rows updated for chat_id '{chat_id}'.")
        except Exception as e:
            print(f"Repository Error marking prompt sent for '{chat_id}': {e}")
            try: await db.rollback()
            except Exception as rb_e: print(f"Rollback failed after mark_prompt_sent error: {rb_e}")
        return success

    async def update_mode_and_reset_flag(self, db: aiosqlite.Connection, chat_id: str, new_mode: str | None) -> bool:
        """Updates the mode and resets the system_prompt_sent flag to FALSE."""
        success = False
        try:
            cursor = await db.execute(
                "UPDATE sessions SET mode = ?, system_prompt_sent = FALSE WHERE chat_id = ?",
                (new_mode, chat_id)
            )
            await db.commit()
            success = cursor.rowcount > 0
            await cursor.close()
            if not success:
                print(f"Repository Warning: update_mode_and_reset_flag - No rows updated for chat_id '{chat_id}'.")
        except Exception as e:
            print(f"Repository Error updating mode/resetting flag for '{chat_id}': {e}")
            try: await db.rollback()
            except Exception as rb_e: print(f"Rollback failed after update_mode_and_reset_flag error: {rb_e}")
        return success

    async def delete_chat(self, db: aiosqlite.Connection, chat_id: str) -> bool:
        """Deletes a chat session by ID."""
        success = False
        try:
            cursor = await db.execute("DELETE FROM sessions WHERE chat_id = ?", (chat_id,))
            await db.commit()
            success = cursor.rowcount > 0
            await cursor.close()
            if not success:
                 print(f"Repository Warning: delete_chat - No rows deleted for chat_id '{chat_id}'.")
            else:
                 print(f"Repository: Session DELETED from DB: {chat_id}")
        except Exception as e:
            print(f"Repository Error deleting session '{chat_id}': {e}")
            try: await db.rollback()
            except Exception as rb_e: print(f"Rollback failed after delete_chat error: {rb_e}")
        return success