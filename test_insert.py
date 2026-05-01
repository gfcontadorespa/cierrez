from db_manager import PostgresManager

db = PostgresManager()
conn = db.get_connection()
try:
    with conn.cursor() as cur:
        query = "INSERT INTO tbl_companies (name, ruc, z_sequence_type, z_current_sequence, use_ai_validation) VALUES (%s, %s, 'manual', 0, FALSE) RETURNING id;"
        cur.execute(query, ("Test Company", "12345"))
        print(cur.fetchone()[0])
        conn.rollback() # don't actually save it
except Exception as e:
    print("ERROR:", e)
finally:
    db.release_connection(conn)
