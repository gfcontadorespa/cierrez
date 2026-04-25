from db_manager import PostgresManager

db = PostgresManager()
try:
    print("--- Stats for tblsucursales ---")
    count = db.fetch_one("SELECT COUNT(*) FROM tblsucursales;")[0]
    null_names = db.fetch_one("SELECT COUNT(*) FROM tblsucursales WHERE display_name IS NULL OR display_name = '';")[0]
    sample = db.fetch_all("SELECT branch_id, display_name, email_suc FROM tblsucursales LIMIT 5;")
    
    print(f"Total rows: {count}")
    print(f"Rows with empty/null display_name: {null_names}")
    print("Sample data:")
    for row in sample:
        print(row)
        
    print("\n--- Stats for tblcierresz ---")
    cierres_count = db.fetch_one("SELECT COUNT(*) FROM tblcierresz;")[0]
    cierres_unlinked = db.fetch_one("SELECT COUNT(*) FROM tblcierresz WHERE branch_id IS NULL;")[0]
    print(f"Total cierres: {cierres_count}")
    print(f"Unlinked cierres: {cierres_unlinked}")

finally:
    db.close_all_connections()
