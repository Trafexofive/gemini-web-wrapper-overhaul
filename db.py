import json
import sqlite3
from pathlib import Path
from typing import Any, List, Tuple, Dict

DB_FILE = Path("chat_sessions.db")
db_conn: sqlite3.Connection | None = None

def _init_db_sync():
    """Inicializa DB com colunas 'description', 'mode', e 'system_prompt_sent'."""
    global db_conn
    if db_conn: return True
    try:
        print(f"Attempting to connect/create database: {DB_FILE.resolve()}")
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        db_conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = db_conn.cursor()
        # <<< MODIFICADO: Adicionada coluna 'system_prompt_sent' >>>
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                chat_id TEXT PRIMARY KEY,
                metadata_json TEXT NOT NULL,
                description TEXT,
                mode TEXT,
                system_prompt_sent BOOLEAN DEFAULT FALSE NOT NULL, -- Flag para prompt inicial
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_chat_id ON sessions(chat_id)")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
        if not cursor.fetchone(): raise sqlite3.DatabaseError("Table 'sessions' not created.")
        db_conn.commit()
        print(f"Database initialized/connected successfully: {DB_FILE}")
        return True
    except sqlite3.Error as e: print(f"SQLITE ERROR during init: {e}"); db_conn = None; return False
    except Exception as e: print(f"GENERIC ERROR during init: {e}"); db_conn = None; return False

# <<< MODIFICADO: Carrega METADATA, MODO e FLAG PROMPT_SENT para cache >>>
def _load_sessions_sync() -> Dict[str, Dict[str, Any]]:
    """Carrega metadata, mode e system_prompt_sent das sessões para cache."""
    if not db_conn: print("ERROR inside _load_sessions_sync: DB down."); return {}
    # Estrutura do cache: { chat_id: {"metadata": obj, "mode": str|None, "prompt_sent": bool} }
    sessions_cache: Dict[str, Dict[str, Any]] = {}
    try:
        cursor = db_conn.cursor()
        # <<< MODIFICADO: Seleciona system_prompt_sent também >>>
        cursor.execute("SELECT chat_id, metadata_json, mode, system_prompt_sent FROM sessions")
        rows = cursor.fetchall()
        for row in rows:
            chat_id, metadata_json, mode, prompt_sent_db = row
            try:
                metadata = json.loads(metadata_json)
                # Converte valor do DB (0 ou 1) para booleano
                prompt_sent = bool(prompt_sent_db)
                sessions_cache[chat_id] = {"metadata": metadata, "mode": mode, "prompt_sent": prompt_sent}
            except json.JSONDecodeError: print(f"Warning: Bad JSON metadata for {chat_id}. Skipping.")
        print(f"Loaded data for {len(sessions_cache)} chat sessions into memory cache.")
        return sessions_cache
    except Exception as e: print(f"Error loading session data from DB: {e}"); return {}

# <<< Sem alterações: Busca ID, Descrição e Modo para a lista >>>
def _get_all_chats_info_sync() -> List[Tuple[str, str | None, str | None]]:
    """Busca chat_id, description e mode de todas as sessões no DB."""
    if not db_conn: print("ERROR inside _get_all_chats_info_sync: DB down."); return []
    try:
        cursor = db_conn.cursor(); cursor.execute("SELECT chat_id, description, mode FROM sessions ORDER BY last_updated DESC")
        return cursor.fetchall()
    except Exception as e: print(f"Error getting chats info from DB: {e}"); return []

# <<< Sem alterações: Cria sessão (flag prompt_sent usa default FALSE) >>>
def _create_session_sync(chat_id: str, metadata: dict, description: str | None, mode: str | None):
    """Insere uma NOVA sessão no DB (prompt_sent será FALSE por default)."""
    if not db_conn: print(f"ERROR inside _create_session_sync: Cannot create {chat_id}, DB down."); return False
    try:
        metadata_json = json.dumps(metadata); cursor = db_conn.cursor()
        # system_prompt_sent não precisa ser listado, usará o DEFAULT FALSE
        cursor.execute("""
            INSERT INTO sessions (chat_id, metadata_json, description, mode) VALUES (?, ?, ?, ?)
        """, (chat_id, metadata_json, description, mode))
        db_conn.commit(); print(f"Session CREATED in DB: {chat_id} ..."); return True
    except sqlite3.IntegrityError: print(f"ERROR: Session {chat_id} already exists."); return False
    except Exception as e: print(f"Error CREATING session {chat_id} in DB: {e}"); return False

# <<< Sem alterações: Atualiza apenas metadata >>>
def _update_session_metadata_sync(chat_id: str, metadata: dict):
    """Atualiza APENAS o metadata_json e last_updated."""
    # (Código como antes)
    if not db_conn: print(f"ERROR inside _update_metadata: Cannot update {chat_id}, DB down."); return False
    try:
        metadata_json = json.dumps(metadata); cursor = db_conn.cursor()
        cursor.execute("UPDATE sessions SET metadata_json = ?, last_updated = CURRENT_TIMESTAMP WHERE chat_id = ?", (metadata_json, chat_id))
        if cursor.rowcount == 0: print(f"Warning: Tried to update metadata for non-existent chat_id {chat_id}."); return False
        db_conn.commit(); return True
    except Exception as e: print(f"Error UPDATING metadata for {chat_id} in DB: {e}"); return False


# <<< NOVO: Função para marcar que o prompt do sistema foi enviado >>>
def _mark_system_prompt_sent_sync(chat_id: str):
    """Define system_prompt_sent = TRUE para um chat_id."""
    if not db_conn:
        print(f"ERROR inside _mark_prompt_sent: Cannot update {chat_id}, DB connection not available.")
        return False
    try:
        cursor = db_conn.cursor()
        cursor.execute("UPDATE sessions SET system_prompt_sent = TRUE WHERE chat_id = ?", (chat_id,))
        if cursor.rowcount == 0:
            print(f"Warning: Tried to mark prompt sent for non-existent chat_id {chat_id}.")
            return False
        db_conn.commit()
        print(f"System prompt marked as SENT for chat_id: {chat_id}")
        return True
    except Exception as e:
        print(f"Error marking system prompt sent for {chat_id} in database: {e}")
        return False

def _update_session_mode_sync(chat_id: str, new_mode: str | None):
    """Atualiza o 'mode' e reseta 'system_prompt_sent' para FALSE."""
    if not db_conn:
        print(f"ERROR inside _update_session_mode_sync: Cannot update {chat_id}, DB down.")
        return False
    try:
        cursor = db_conn.cursor()
        cursor.execute("""
            UPDATE sessions
            SET mode = ?,
                system_prompt_sent = FALSE,
                last_updated = CURRENT_TIMESTAMP
            WHERE chat_id = ?
        """, (new_mode, chat_id))
        if cursor.rowcount == 0:
            print(f"Warning: Tried to update mode for non-existent chat_id {chat_id}.")
            return False
        db_conn.commit()
        print(f"Session mode UPDATED and prompt flag RESET for: {chat_id} (New Mode: {new_mode or 'Default'})")
        return True
    except Exception as e:
        print(f"Error UPDATING session mode for {chat_id} in database: {e}")
        return False

def _delete_session_sync(chat_id: str):
    """Deleta uma sessão do DB (igual antes)."""
    if not db_conn:
        print(f"ERROR inside _delete_session_sync: Cannot delete session {chat_id}, DB connection not available.")
        return False
    try:
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE chat_id = ?", (chat_id,))
        db_conn.commit()
        # Verifica se deletou algo
        if cursor.rowcount > 0:
             print(f"Session deleted from DB: {chat_id}")
             return True
        else:
             print(f"Warning: Tried to delete non-existent chat_id {chat_id}.")
             return False # Indica que não encontrou para deletar
    except Exception as e:
        print(f"Error deleting session {chat_id} from database: {e}")
        return False

def _close_db_sync():
    """Fecha a conexão com o DB (igual antes, com o print de debug)."""
    print("\n\n##################### _close_db_sync FOI CHAMADA #####################\n\n")
    global db_conn
    if db_conn:
        try:
            db_conn.close()
            print("Database connection closed.")
            db_conn = None
        except Exception as e:
            print(f"Error closing database connection: {e}")
    else:
        print("_close_db_sync chamada, mas db_conn já era None.")