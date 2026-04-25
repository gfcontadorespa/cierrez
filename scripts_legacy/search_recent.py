
import os
from db_manager import PostgresManager
from datetime import datetime, timedelta

db = PostgresManager()
try:
    query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    tables = db.fetch_all(query)
    
    found_any = False
    for t in tables:
        tname = t[0]
        cols_query = f"SELECT column_name FROM information_schema.columns WHERE table_name = '{tname}'"
        cols = [c[0] for c in db.fetch_all(cols_query)]
        
        date_col = next((c for c in cols if c in ['fecha_adicion', 'created_at', 'fecha_modifica']), None)
        if date_col:
            # Check for records in the last 30 minutes
            res = db.fetch_all(f"SELECT * FROM {tname} WHERE {date_col} > NOW() - INTERVAL '30 minutes'")
            if res:
                print(f"Table {tname}: found {len(res)} records in the last 30 minutes.")
                for r in res:
                    print(r)
                found_any = True
    
    if not found_any:
        print("No recent records found in any table.")

finally:
    db.close_all_connections()
