# db.py
import json
import sqlite3
from pathlib import Path
from typing import Any, List, Tuple # Importar Tuple

DB_FILE = Path("chat_sessions.db")
db_conn: sqlite3.Connection | None = None

def _init_db_sync():
    """Inicializa o DB e a tabela (com coluna 'description') se não existirem."""
    global db_conn
    if db_conn:
        # print(f"Database already connected: {DB_FILE}") # Log menos verboso
        return True
    try:
        print(f"Attempting to connect/create database: {DB_FILE.resolve()}")
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        db_conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = db_conn.cursor()
        # <<< MODIFICADO: Adicionada coluna 'description' >>>
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                chat_id TEXT PRIMARY KEY,
                metadata_json TEXT NOT NULL,
                description TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
        if not cursor.fetchone():
             raise sqlite3.DatabaseError("Table 'sessions' was not created successfully.")
        db_conn.commit()
        print(f"Database initialized/connected successfully: {DB_FILE}")
        return True
    except sqlite3.Error as e:
        print(f"!!!!!!!! CRITICAL SQLITE ERROR during init !!!!!!!!: {e}")
        db_conn = None
        return False
    except Exception as e:
        print(f"!!!!!!!! CRITICAL GENERIC ERROR during init !!!!!!!!: {e}")
        db_conn = None
        return False

def _load_sessions_sync() -> dict:
    """Carrega apenas os METADADOS das sessões do DB para um dicionário em memória."""
    if not db_conn:
        print("ERROR inside _load_sessions_sync: Cannot load sessions, DB connection not available.")
        return {}
    sessions_metadata = {}
    try:
        cursor = db_conn.cursor()
        # Seleciona apenas id e metadata para o cache em memória
        cursor.execute("SELECT chat_id, metadata_json FROM sessions")
        rows = cursor.fetchall()
        for row in rows:
            chat_id, metadata_json = row
            try:
                metadata = json.loads(metadata_json)
                sessions_metadata[chat_id] = metadata
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON metadata for chat_id {chat_id}. Skipping.")
        print(f"Loaded metadata for {len(sessions_metadata)} chat sessions from database.")
        return sessions_metadata
    except Exception as e:
        print(f"Error loading session metadata from database: {e}")
        return {}

# <<< NOVO: Função para buscar ID e Descrição >>>
def _get_all_chats_info_sync() -> List[Tuple[str, str | None]]:
    """Busca chat_id e description de todas as sessões no DB."""
    if not db_conn:
        print("ERROR inside _get_all_chats_info_sync: DB connection not available.")
        return []
    chats_info = []
    try:
        cursor = db_conn.cursor()
        cursor.execute("SELECT chat_id, description FROM sessions ORDER BY last_updated DESC")
        rows = cursor.fetchall()
        return rows # Retorna lista de tuplas (chat_id, description)
    except Exception as e:
        print(f"Error getting chats info from database: {e}")
        return []

# <<< MODIFICADO: Função específica para CRIAR uma sessão >>>
def _create_session_sync(chat_id: str, metadata: dict, description: str | None):
    """Insere uma NOVA sessão no DB."""
    if not db_conn:
        print(f"ERROR inside _create_session_sync: Cannot create session {chat_id}, DB connection not available.")
        return False
    try:
        metadata_json = json.dumps(metadata)
        cursor = db_conn.cursor()
        # INSERT simples, pois é para criar (não deve existir)
        cursor.execute("""
            INSERT INTO sessions (chat_id, metadata_json, description)
            VALUES (?, ?, ?)
        """, (chat_id, metadata_json, description))
        db_conn.commit()
        print(f"Session CREATED in DB: {chat_id} - Desc: '{description or 'N/A'}'")
        return True
    except sqlite3.IntegrityError:
         # Caso raro onde o UUID colide ou a lógica de chamar falhou
         print(f"ERROR: Tried to create session {chat_id}, but it already exists (IntegrityError).")
         return False
    except Exception as e:
        print(f"Error CREATING session {chat_id} in database: {e}")
        return False

# <<< MODIFICADO: Função específica para ATUALIZAR METADATA >>>
def _update_session_metadata_sync(chat_id: str, metadata: dict):
    """Atualiza APENAS o metadata_json e last_updated de uma sessão existente."""
    if not db_conn:
        print(f"ERROR inside _update_session_metadata_sync: Cannot update session {chat_id}, DB connection not available.")
        return False
    try:
        metadata_json = json.dumps(metadata)
        cursor = db_conn.cursor()
        cursor.execute("""
            UPDATE sessions
            SET metadata_json = ?, last_updated = CURRENT_TIMESTAMP
            WHERE chat_id = ?
        """, (metadata_json, chat_id))
        # Verifica se alguma linha foi realmente atualizada
        if cursor.rowcount == 0:
            print(f"Warning: Tried to update metadata for non-existent chat_id {chat_id}.")
            return False # Ou talvez True, dependendo se considera erro? Vamos retornar False.
        db_conn.commit()
        # print(f"Session metadata UPDATED in DB: {chat_id}") # Log opcional
        return True
    except Exception as e:
        print(f"Error UPDATING session metadata for {chat_id} in database: {e}")
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