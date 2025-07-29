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
        # Common Firefox profile locations
        firefox_paths = [
            Path.home() / ".mozilla" / "firefox",
            Path("/root/.mozilla/firefox"),  # Docker
            Path("/home/user/.mozilla/firefox"),  # Alternative Docker
        ]
        
        for firefox_path in firefox_paths:
            if not firefox_path.exists():
                print(f"Firefox path does not exist: {firefox_path}")
                continue
            
            print(f"Checking Firefox profile at: {firefox_path}")
            
            # Find the default profile
            profiles_ini = firefox_path / "profiles.ini"
            if not profiles_ini.exists():
                print(f"profiles.ini not found at: {profiles_ini}")
                continue
            
            # Parse profiles.ini to find default profile
            default_profile = None
            with open(profiles_ini, 'r') as f:
                current_profile = None
                for line in f:
                    line = line.strip()
                    if line.startswith('[Profile'):
                        current_profile = None
                    elif line.startswith('Path='):
                        current_profile = line.split('=', 1)[1].strip()
                    elif line.startswith('Default=1'):
                        if current_profile:
                            default_profile = current_profile
                            break
            
            # If no default found, try to find the most recent profile
            if not default_profile:
                print("No default profile found, looking for most recent profile...")
                profile_dirs = [d for d in firefox_path.iterdir() if d.is_dir() and d.name.endswith('.default') or d.name.endswith('.default-release')]
                if profile_dirs:
                    # Sort by modification time, get the most recent
                    profile_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    default_profile = profile_dirs[0].name
                    print(f"Using most recent profile: {default_profile}")
            
            if not default_profile:
                print("No profile found")
                continue
            
            print(f"Using profile: {default_profile}")
            
            # Look for cookies.sqlite in the profile
            profile_path = firefox_path / default_profile
            cookies_db = profile_path / "cookies.sqlite"
            
            if not cookies_db.exists():
                print(f"Cookies database not found at: {cookies_db}")
                continue
            
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
