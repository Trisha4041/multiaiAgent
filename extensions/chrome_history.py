import sqlite3
import os
import shutil
import csv
from datetime import datetime, timedelta

def get_chrome_history():
    # Base Chrome directory on macOS
    chrome_base = os.path.expanduser("~/Library/Application Support/Google/Chrome/")
    
    # Find all History files in Chrome profiles
    history_files = []
    for root, dirs, files in os.walk(chrome_base):
        if "History" in files:
            history_files.append(os.path.join(root, "History"))
    
    if not history_files:
        print("No Chrome history files found!")
        return []
    
    all_history = []
    
    for history_path in history_files:
        temp_db = "temp_history.db"
        
        try:
            # Make a copy of the history file
            shutil.copy2(history_path, temp_db)
            
            # Connect to the copied database
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            # Get profile name from path
            profile_name = os.path.basename(os.path.dirname(history_path))
            
            # Fetch visits
            cursor.execute("""
                SELECT url, title, last_visit_time 
                FROM urls 
                ORDER BY last_visit_time DESC 
                LIMIT 200
            """)
            
            # Format results
            for url, title, timestamp in cursor.fetchall():
                if timestamp:
                    epoch_start = datetime(1601, 1, 1)
                    visit_time = epoch_start + timedelta(microseconds=timestamp)
                    all_history.append({
                        "time": visit_time,
                        "title": title,
                        "url": url,
                        "profile": profile_name
                    })
            
        except Exception as e:
            print(f"Error reading {history_path}: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
            if os.path.exists(temp_db):
                os.remove(temp_db)
    
    # Sort all entries by time (newest first)
    all_history.sort(key=lambda x: x["time"], reverse=True)
    return all_history

def save_to_csv(history, filename="chrome_history.csv"):
    """Save history to CSV file"""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["No.", "Time", "Profile", "Title", "URL"])
        for idx, entry in enumerate(history, 1):
            writer.writerow([
                idx,
                entry['time'].strftime('%Y-%m-%d %H:%M:%S'),
                entry['profile'],
                entry['title'],
                entry['url']
            ])
    print(f"\n✅ Saved {len(history)} entries to {filename}")

def filter_by_days(history, days=1):
    """Filter history from last N days"""
    cutoff = datetime.now() - timedelta(days=days)
    return [h for h in history if h['time'] >= cutoff]

def search_history(history, keyword):
    """Search history for keyword in title/URL"""
    keyword = keyword.lower()
    return [
        h for h in history 
        if keyword in h['title'].lower() or keyword in h['url'].lower()
    ]

def print_history(history, limit=20):
    """Print history in readable format"""
    for idx, entry in enumerate(history[:limit], 1):
        print(f"\n{idx}. {entry['time'].strftime('%Y-%m-%d %H:%M:%S')} [{entry['profile']}]")
        print(f"Title: {entry['title']}")
        print(f"URL: {entry['url'][:80]}{'...' if len(entry['url']) > 80 else ''}")

# Main execution
if __name__ == "__main__":
    print("🚀 Fetching Chrome history from all profiles...")
    history = get_chrome_history()
    
    if not history:
        print("No history found. Possible reasons:")
        print("- Chrome is not installed in the default location")
        print("- Permission issues (try running with 'sudo')")
        exit()
    
    print(f"\nFound {len(history)} total entries across all profiles")
    
    while True:
        print("\nOptions:")
        print("1. Show recent history")
        print("2. Search history")
        print("3. Export to CSV")
        print("4. Exit")
        
        choice = input("\nChoose an option (1-4): ").strip()
        
        if choice == "1":
            days = int(input("Show history from last how many days? (1-30): ") or 1)
            recent = filter_by_days(history, days)
            print(f"\n📅 Last {days} day(s) history ({len(recent)} entries):")
            print_history(recent)
            
        elif choice == "2":
            keyword = input("Enter search keyword: ").strip()
            results = search_history(history, keyword)
            print(f"\n🔍 Found {len(results)} matching entries:")
            print_history(results)
            
        elif choice == "3":
            filename = input("Enter CSV filename (default: chrome_history.csv): ").strip() or "chrome_history.csv"
            save_to_csv(history, filename)
            
        elif choice == "4":
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice, please try again")