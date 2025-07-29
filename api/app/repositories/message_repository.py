# app/repositories/message_repository.py
import aiosqlite
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.models import Message, MessageCreate, MessageResponse
from app.config import DATABASE_URL

class SqliteMessageRepository:
    """Repository for message data using aiosqlite."""

    db_path = DATABASE_URL.split("///")[-1]

    @staticmethod
    async def initialize_db():
        """Creates the messages table if it doesn't exist."""
        print(f"Initializing database table 'messages' at: {SqliteMessageRepository.db_path}")
        try:
            async with aiosqlite.connect(SqliteMessageRepository.db_path) as db:
                await db.execute("PRAGMA journal_mode=WAL;")
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        chat_id TEXT NOT NULL,
                        role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                        content TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata_json TEXT,
                        FOREIGN KEY (chat_id) REFERENCES sessions(chat_id) ON DELETE CASCADE
                    )
                """)
                await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
                await db.commit()
                print("Database table 'messages' initialized successfully.")
        except Exception as e:
            print(f"!!!!!!!! MESSAGE DATABASE INITIALIZATION FAILED !!!!!!!! Error: {e}")
            raise RuntimeError(f"Failed to initialize messages database: {e}") from e

    async def create_message(self, db: aiosqlite.Connection, chat_id: str, message_data: MessageCreate) -> Message:
        """Creates a new message in the database."""
        message_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        try:
            metadata_json = None
            if message_data.metadata:
                import json
                metadata_json = json.dumps(message_data.metadata)
            
            await db.execute("""
                INSERT INTO messages (id, chat_id, role, content, timestamp, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (message_id, chat_id, message_data.role, message_data.content, timestamp, metadata_json))
            
            return Message(
                id=message_id,
                chat_id=chat_id,
                role=message_data.role,
                content=message_data.content,
                timestamp=timestamp,
                metadata=message_data.metadata
            )
        except Exception as e:
            print(f"Repository Error in create_message: {e}")
            raise

    async def get_messages_by_chat_id(self, db: aiosqlite.Connection, chat_id: str, limit: Optional[int] = None) -> List[Message]:
        """Retrieves all messages for a specific chat."""
        try:
            query = "SELECT id, chat_id, role, content, timestamp, metadata_json FROM messages WHERE chat_id = ? ORDER BY timestamp ASC"
            params = [chat_id]
            
            if limit:
                query += f" LIMIT {limit}"
            
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                messages = []
                
                for row in rows:
                    metadata = None
                    if row["metadata_json"]:
                        import json
                        try:
                            metadata = json.loads(row["metadata_json"])
                        except json.JSONDecodeError:
                            print(f"Warning: Bad JSON metadata for message {row['id']}")
                    
                    message = Message(
                        id=row["id"],
                        chat_id=row["chat_id"],
                        role=row["role"],
                        content=row["content"],
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        metadata=metadata
                    )
                    messages.append(message)
                
                return messages
        except Exception as e:
            print(f"Repository Error in get_messages_by_chat_id: {e}")
            return []

    async def get_message_count(self, db: aiosqlite.Connection, chat_id: str) -> int:
        """Gets the total number of messages for a chat."""
        try:
            async with db.execute("SELECT COUNT(*) FROM messages WHERE chat_id = ?", (chat_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
        except Exception as e:
            print(f"Repository Error in get_message_count: {e}")
            return 0

    async def delete_messages_by_chat_id(self, db: aiosqlite.Connection, chat_id: str) -> bool:
        """Deletes all messages for a specific chat."""
        try:
            await db.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            return True
        except Exception as e:
            print(f"Repository Error in delete_messages_by_chat_id: {e}")
            return False

    async def get_latest_message(self, db: aiosqlite.Connection, chat_id: str) -> Optional[Message]:
        """Gets the most recent message for a chat."""
        try:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT id, chat_id, role, content, timestamp, metadata_json 
                FROM messages 
                WHERE chat_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (chat_id,)) as cursor:
                row = await cursor.fetchone()
                
                if not row:
                    return None
                
                metadata = None
                if row["metadata_json"]:
                    import json
                    try:
                        metadata = json.loads(row["metadata_json"])
                    except json.JSONDecodeError:
                        print(f"Warning: Bad JSON metadata for message {row['id']}")
                
                return Message(
                    id=row["id"],
                    chat_id=row["chat_id"],
                    role=row["role"],
                    content=row["content"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    metadata=metadata
                )
        except Exception as e:
            print(f"Repository Error in get_latest_message: {e}")
            return None