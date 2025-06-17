import sqlite3
import json
from pathlib import Path
from typing import Dict, Optional, List
import os

# Ensure the data directory exists
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "agent_accounts.db"

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create accounts table
    c.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_type TEXT NOT NULL,
            did TEXT NOT NULL UNIQUE,
            address TEXT NOT NULL,
            public_key TEXT NOT NULL,
            private_key TEXT NOT NULL,
            is_registered BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create chat history table
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def store_account(agent_type: str, account_data: Dict) -> bool:
    """Store an agent account in the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if account already exists
        c.execute('SELECT id FROM accounts WHERE did = ?', (account_data['did'],))
        existing = c.fetchone()
        
        if existing:
            # Update existing account
            c.execute('''
                UPDATE accounts 
                SET agent_type = ?, address = ?, public_key = ?, private_key = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE did = ?
            ''', (
                agent_type,
                account_data['address'],
                account_data['public_key'],
                account_data['private_key'],
                account_data['did']
            ))
        else:
            # Insert new account
            c.execute('''
                INSERT INTO accounts 
                (agent_type, did, address, public_key, private_key)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                agent_type,
                account_data['did'],
                account_data['address'],
                account_data['public_key'],
                account_data['private_key']
            ))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error storing account: {e}")
        return False
    finally:
        conn.close()

def get_account(agent_type: str) -> Optional[Dict]:
    """Retrieve an agent account from the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            SELECT did, address, public_key, private_key, is_registered
            FROM accounts 
            WHERE agent_type = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (agent_type,))
        
        result = c.fetchone()
        if result:
            return {
                'did': result[0],
                'address': result[1],
                'public_key': result[2],
                'private_key': result[3],
                'is_registered': bool(result[4])
            }
        return None
    except Exception as e:
        print(f"Error retrieving account: {e}")
        return None
    finally:
        conn.close()

def update_registration_status(agent_type: str, is_registered: bool) -> bool:
    """Update the registration status of an agent account."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            UPDATE accounts 
            SET is_registered = ?, updated_at = CURRENT_TIMESTAMP
            WHERE agent_type = ?
        ''', (is_registered, agent_type))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating registration status: {e}")
        return False
    finally:
        conn.close()

def get_all_accounts() -> Dict[str, Dict]:
    """Retrieve all agent accounts from the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            SELECT agent_type, did, address, public_key, private_key, is_registered
            FROM accounts
            ORDER BY created_at DESC
        ''')
        
        accounts = {}
        for row in c.fetchall():
            accounts[row[0]] = {
                'did': row[1],
                'address': row[2],
                'public_key': row[3],
                'private_key': row[4],
                'is_registered': bool(row[5])
            }
        return accounts
    except Exception as e:
        print(f"Error retrieving all accounts: {e}")
        return {}
    finally:
        conn.close()

def store_chat_message(session_id: str, role: str, content: str) -> bool:
    """Store a chat message in the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO chat_history (session_id, role, content)
            VALUES (?, ?, ?)
        ''', (session_id, role, content))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error storing chat message: {e}")
        return False
    finally:
        conn.close()

def get_chat_history(session_id: str) -> List[Dict]:
    """Retrieve chat history for a specific session."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            SELECT role, content, timestamp
            FROM chat_history
            WHERE session_id = ?
            ORDER BY timestamp ASC
        ''', (session_id,))
        
        return [
            {
                'role': row[0],
                'content': row[1],
                'timestamp': row[2]
            }
            for row in c.fetchall()
        ]
    except Exception as e:
        print(f"Error retrieving chat history: {e}")
        return []
    finally:
        conn.close()

def get_registered_accounts() -> Dict[str, Dict]:
    """Retrieve only registered agent accounts from the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            SELECT agent_type, did, address, public_key, private_key, is_registered
            FROM accounts
            WHERE is_registered = 1
            ORDER BY created_at DESC
        ''')
        
        accounts = {}
        for row in c.fetchall():
            accounts[row[0]] = {
                'did': row[1],
                'address': row[2],
                'public_key': row[3],
                'private_key': row[4],
                'is_registered': bool(row[5])
            }
        return accounts
    except Exception as e:
        print(f"Error retrieving registered accounts: {e}")
        return {}
    finally:
        conn.close()

# Initialize the database when the module is imported
init_db() 