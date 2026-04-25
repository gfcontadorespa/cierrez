
import os
from db_manager import PostgresManager
from datetime import datetime

db = PostgresManager()
try:
    # Get all tables
    query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    tables = db.fetch_all(query)
    
    print(f"Checking {len(tables)} tables for records from today (2026-02-23)...")
    
    for table in tables:
        tname = table[0]
        # Check if table has created_at or fecha_adicion or similar
        cols_query = f"SELECT column_name FROM information_schema.columns WHERE table_name = '{tname}'"
        cols = [c[0] for c in db.fetch_all(cols_query)]
        
        date_col = None
        if 'fecha_adicion' in cols: date_col = 'fecha_adicion'
        elif 'created_at' in cols: date_col = 'created_at'
        elif 'fecha_modifica' in cols: date_col = 'fecha_modifica'
        
        if date_col:
            today_query = f"SELECT count(*) FROM {tname} WHERE {date_col}::date = '2026-02-23'::date"
            count = db.fetch_one(today_query)[0]
            print(f"{tname}: {count} records added/modified today")
            if count > 0:
                print(f"  Fetching latest record from {tname}:")
                latest = db.fetch_all(f"SELECT * FROM {tname} WHERE {date_col}::date = '2026-02-23'::date ORDER BY {date_col} DESC LIMIT 1")
                print(f"  {latest}")
        else:
            count = db.fetch_one(f"SELECT count(*) FROM {tname}")[0]
            print(f"{tname}: {count} total records (no date column found)")

finally:
    db.close_all_connections()
