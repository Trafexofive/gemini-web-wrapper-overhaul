#!/usr/bin/env python3
import sqlite3
import tempfile
import shutil
import os
from pathlib import Path

def extract_firefox_cookies():
    """Extract cookies from Firefox profile automatically."""
    cookies = {}
    
    try:
        # Use the specific profile that has cookies
        firefox_path = Path.home() / ".mozilla" / "firefox"
        profile_name = "nfdugc1f.default-release"
        profile_path = firefox_path / profile_name
        cookies_db = profile_path / "cookies.sqlite"
        
        print(f"Looking for cookies in: {cookies_db}")
        
        if not cookies_db.exists():
            print(f"Cookies database not found at: {cookies_db}")
            return {}
        
        print(f"Found cookies database at: {cookies_db}")
        
        # Extract Gemini cookies
        temp_db = None
        try:
            # Copy the database to avoid locking issues
            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite')
            shutil.copy2(cookies_db, temp_db.name)
            
            conn = sqlite3.connect(temp_db.name)
            cursor = conn.cursor()
            
            # Query for Gemini cookies - FIXED: use correct cookie names
            cursor.execute("""
                SELECT name, value FROM moz_cookies 
                WHERE host LIKE '%google.com%' 
                AND (name LIKE '%__Secure-1PSID%' OR name LIKE '%__Secure-1PSIDTS%')
            """)
            
            found_cookies = cursor.fetchall()
            if not found_cookies:
                print(f"No Gemini cookies found in {cookies_db}")
            else:
                for name, value in found_cookies:
                    cookies[name] = value
                    print(f"Found cookie: {name}")
            
            conn.close()
            
            if cookies:
                print(f"Successfully extracted {len(cookies)} cookies from Firefox")
                return cookies
                
        except sqlite3.Error as e:
            print(f"SQLite error extracting cookies from {cookies_db}: {e}")
        except Exception as e:
            print(f"Error extracting cookies from {cookies_db}: {e}")
        finally:
            if temp_db and os.path.exists(temp_db.name):
                try:
                    os.unlink(temp_db.name)
                except:
                    pass
        
        print("No valid cookies found in Firefox profiles")
        return {}
        
    except Exception as e:
        print(f"Critical error during Firefox cookie extraction: {e}")
        return {}

if __name__ == "__main__":
    cookies = extract_firefox_cookies()
    print(f"\nFinal result: {len(cookies)} cookies found")
    for name, value in cookies.items():
        print(f"  {name}: {value[:50]}...")
