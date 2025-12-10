#!/usr/bin/env python3
"""Migration script to add share_hash column to chat_sessions table"""

import pymysql
import secrets
from dotenv import load_dotenv
import os

load_dotenv()

def generate_share_hash():
    """Generate a secure random hash for chat sharing"""
    return secrets.token_urlsafe(24)

def migrate():
    """Add share_hash column and populate existing records"""
    conn = pymysql.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=int(os.getenv('DB_PORT', 3307)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'zed'),
        charset='utf8mb4'
    )
    
    try:
        with conn.cursor() as cursor:
            # Check if column exists
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'zed' 
                AND TABLE_NAME = 'chat_sessions' 
                AND COLUMN_NAME = 'share_hash'
            """)
            result = cursor.fetchone()
            
            if result[0] == 0:
                print("Adding share_hash column...")
                # Add column
                cursor.execute("""
                    ALTER TABLE chat_sessions 
                    ADD COLUMN share_hash VARCHAR(40) UNIQUE NULL
                """)
                conn.commit()
                print("✓ Column added")
            else:
                print("✓ Column already exists")
            
            # Update existing records without hash
            cursor.execute('SELECT id FROM chat_sessions WHERE share_hash IS NULL OR share_hash = ""')
            sessions = cursor.fetchall()
            
            if sessions:
                print(f"\nUpdating {len(sessions)} sessions with unique hashes...")
                for session in sessions:
                    hash_val = generate_share_hash()
                    cursor.execute(
                        'UPDATE chat_sessions SET share_hash = %s WHERE id = %s',
                        (hash_val, session[0])
                    )
                conn.commit()
                print(f"✓ Updated {len(sessions)} sessions")
            else:
                print("✓ All sessions already have hashes")
            
            # Add index if not exists
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM INFORMATION_SCHEMA.STATISTICS
                WHERE TABLE_SCHEMA = 'zed'
                AND TABLE_NAME = 'chat_sessions'
                AND INDEX_NAME = 'idx_share_hash'
            """)
            result = cursor.fetchone()
            
            if result[0] == 0:
                print("\nAdding index on share_hash...")
                cursor.execute("""
                    ALTER TABLE chat_sessions 
                    ADD INDEX idx_share_hash (share_hash)
                """)
                conn.commit()
                print("✓ Index added")
            else:
                print("✓ Index already exists")
            
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
