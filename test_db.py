import psycopg2

conn=psycopg2.connect(host='5.161.186.198', port=5433, dbname='db-cierres-z', user='contapan01', password='Lobito0807*')
cur=conn.cursor()
try:
    query_master = """
        INSERT INTO tbl_cierres_z_master 
        (company_id, branch_id, z_number, date_closed, taxable_sales, exempt_sales, tax_amount, total_sales, total_receipt, difference_amount, status, image_url, pos_receipt_url, deposit_receipt_url, workflow_status) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'draft') RETURNING id;
    """
    cur.execute(query_master, (
        1, 1, "Z-999", "2026-05-01", 10.0, 0.0, 0.7, 10.0, 10.7, 0.0, "balanced", None, None, None
    ))
    id = cur.fetchone()[0]
    print("Inserted ID:", id)
    conn.rollback()
except Exception as e:
    print("Error:", e)
