#!/usr/bin/env python3
import asyncio
import tempfile
import shutil
import os
from pathlib import Path
import sqlite3

# Test the async issue
async def test_async():
    try:
        from gemini_webapi import GeminiClient
        
        # Extract cookies first
        firefox_path = Path("/root/.mozilla/firefox")
        profile_name = "nfdugc1f.default-release"
        profile_path = firefox_path / profile_name
        cookies_db = profile_path / "cookies.sqlite"
        
        print(f"Looking for cookies in: {cookies_db}")
        
        if not cookies_db.exists():
            print(f"Cookies database not found at: {cookies_db}")
            return
        
        print(f"Found cookies database at: {cookies_db}")
        
        # Extract cookies
        temp_db = None
        cookies = {}
        try:
            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite')
            shutil.copy2(cookies_db, temp_db.name)
            
            conn = sqlite3.connect(temp_db.name)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name, value FROM moz_cookies 
                WHERE host LIKE '%google.com%' 
                AND (name LIKE '%__Secure-1PSID%' OR name LIKE '%__Secure-1PSIDTS%')
            """)
            
            found_cookies = cursor.fetchall()
            for name, value in found_cookies:
                cookies[name] = value
                print(f"Found cookie: {name}")
            
            conn.close()
            
        finally:
            if temp_db and os.path.exists(temp_db.name):
                try:
                    os.unlink(temp_db.name)
                except:
                    pass
        
        # Create client
        client = GeminiClient(cookies=cookies)
        print("Client created with cookies")
        
        # Test connection - this should NOT be awaited
        print("Testing connection...")
        test_session = client.start_chat()  # NOT await!
        print("Connection test successful!")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_async())
    print(f"Test result: {result}")
