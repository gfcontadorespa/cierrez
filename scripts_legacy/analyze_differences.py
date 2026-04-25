import pandas as pd
from db_manager import PostgresManager

print("Connecting to DB...")
db = PostgresManager()

print("Executing query...")
query = """
WITH db_daily AS (
    SELECT 
        s.prefijo,
        s.etiqueta_suc,
        c.invoice_date::date as date,
        SUM(c.total_ingresos) as total_db
    FROM tblcierresz c
    JOIN tblsucursales s ON c.branch_id = s.branch_id
    WHERE EXTRACT(MONTH FROM c.invoice_date) = 1 AND EXTRACT(YEAR FROM c.invoice_date) = 2026
    GROUP BY s.prefijo, s.etiqueta_suc, c.invoice_date::date
),
excel_daily AS (
    SELECT 
        sucursal_prefijo as prefijo,
        fecha as date,
        SUM(monto) as total_excel
    FROM tbl_ventas_excel
    WHERE EXTRACT(MONTH FROM fecha) = 1 AND EXTRACT(YEAR FROM fecha) = 2026
    GROUP BY sucursal_prefijo, fecha
)
SELECT 
    COALESCE(d.etiqueta_suc, e.prefijo) as sucursal,
    COALESCE(d.date, e.date) as fecha,
    COALESCE(d.total_db, 0) as total_db,
    COALESCE(e.total_excel, 0) as total_excel,
    ROUND((COALESCE(d.total_db, 0) - COALESCE(e.total_excel, 0))::numeric, 2) as diferencia
FROM db_daily d
FULL OUTER JOIN excel_daily e ON d.prefijo = e.prefijo AND d.date = e.date
WHERE ABS(COALESCE(d.total_db, 0) - COALESCE(e.total_excel, 0)) > 0.01
ORDER BY sucursal, fecha
"""

print("Fetching results...")
results = db.fetch_all(query)
print("Query done.")
if results:
    df = pd.DataFrame(results, columns=["Sucursal", "Fecha", "Total DB", "Total Excel", "Diferencia"])
    print(df.to_string(index=False))
else:
    print("No se encontraron diferencias diarias > $0.01 en Enero 2026.")
