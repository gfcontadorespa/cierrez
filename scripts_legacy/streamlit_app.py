import streamlit as st
import pandas as pd
from db_manager import PostgresManager
import plotly.express as px
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Reconciliador de Ventas Z", layout="wide")

def get_db():
    return PostgresManager()

def load_excel_to_db(file):
    db = get_db()
    df = pd.read_excel(file)
    
    # Limpieza básica
    df['FECHA'] = pd.to_datetime(df['FECHA'], dayfirst=True).dt.date
    df['sucursal_prefijo'] = df['NUMSERIE'].str[:2]
    
    # Eliminar datos previos del mismo mes/año para evitar duplicados en la carga
    fechas = df['FECHA'].unique()
    if len(fechas) > 0:
        min_date = min(fechas)
        max_date = max(fechas)
        delete_query = "DELETE FROM tbl_ventas_excel WHERE fecha BETWEEN %s AND %s"
        db.execute_query(delete_query, (min_date, max_date))
    
    # Insertar nuevos datos usando execute_batch
    insert_query = """
    INSERT INTO tbl_ventas_excel (fecha, sucursal_prefijo, referencia, monto, iva, nombre_almacen, numserie)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    params_list = []
    for _, row in df.iterrows():
        params_list.append((
            row['FECHA'],
            row['sucursal_prefijo'],
            str(row['REFERENCIA']),
            float(row['PVPDCTO']),
            float(row['IVA']),
            row['NOMBREALMACEN'],
            row['NUMSERIE']
        ))
    
    db.execute_batch(insert_query, params_list)
        
    return len(params_list)

# Sidebar
st.sidebar.title("Navegación")
page = st.sidebar.radio("Ir a:", ["Dashboard de Reconciliación", "Cargar Ventas Excel", "Exportar Reportes", "Configuración"])

if page == "Cargar Ventas Excel":
    st.title("📤 Cargar Reporte de Ventas (Excel)")
    uploaded_file = st.file_uploader("Sube tu archivo reporteventas.xlsx", type=["xlsx"])
    
    if uploaded_file is not None:
        if st.button("Procesar y Cargar a Base de Datos"):
            with st.spinner("Procesando..."):
                count = load_excel_to_db(uploaded_file)
                st.success(f"¡Éxito! Se cargaron {count} registros correctamente.")

elif page == "Dashboard de Reconciliación":
    st.title("📊 Dashboard de Reconciliación")
    
    col1, col2 = st.columns(2)
    with col1:
        mes = st.selectbox("Mes", range(1, 13), index=datetime.now().month - 2)
    with col2:
        anio = st.selectbox("Año", [2025, 2026], index=1)
        
    db = get_db()
    
    # Query de reconciliación
    query = """
    WITH db_totals AS (
        SELECT 
            s.prefijo,
            s.etiqueta_suc,
            SUM(c.total_ingresos) as total_db,
            COUNT(*) as count_db
        FROM tblcierresz c
        JOIN tblsucursales s ON c.branch_id = s.branch_id
        WHERE EXTRACT(MONTH FROM c.invoice_date) = %s AND EXTRACT(YEAR FROM c.invoice_date) = %s
        GROUP BY s.prefijo, s.etiqueta_suc
    ),
    excel_totals AS (
        SELECT 
            sucursal_prefijo as prefijo,
            SUM(monto) as total_excel,
            COUNT(DISTINCT fecha) as count_excel_days -- Contamos días únicos en excel para comparar con registros Z
        FROM tbl_ventas_excel
        WHERE EXTRACT(MONTH FROM fecha) = %s AND EXTRACT(YEAR FROM fecha) = %s
        GROUP BY sucursal_prefijo
    )
    SELECT 
        COALESCE(d.etiqueta_suc, e.prefijo) as sucursal,
        COALESCE(d.total_db, 0) as total_db,
        COALESCE(e.total_excel, 0) as total_excel,
        (COALESCE(d.total_db, 0) - COALESCE(e.total_excel, 0)) as diferencia,
        d.count_db as dias_db,
        e.count_excel_days as dias_excel
    FROM db_totals d
    FULL OUTER JOIN excel_totals e ON d.prefijo = e.prefijo
    ORDER BY sucursal
    """
    
    results = db.fetch_all(query, (mes, anio, mes, anio))
    
    if not results:
        st.warning("No se encontraron datos para el periodo seleccionado.")
    else:
        df_res = pd.DataFrame(results, columns=["Sucursal", "Total DB (Z)", "Total Excel", "Diferencia", "Días DB", "Días Excel"])
        
        # Formateo
        df_res["Total DB (Z)"] = df_res["Total DB (Z)"].apply(lambda x: f"${float(x):,.2f}")
        df_res["Total Excel"] = df_res["Total Excel"].apply(lambda x: f"${float(x):,.2f}")
        df_res["Diferencia"] = df_res["Diferencia"].apply(lambda x: f"${float(x):,.2f}")
        
        st.table(df_res)
        
        # Gráfico simple
        fig = px.bar(df_res, x="Sucursal", y=[float(x[3]) for x in results], title="Diferencia por Sucursal")
        st.plotly_chart(fig)

        # --- SECCIÓN DETALLE DIARIO ---
        st.markdown("---")
        st.subheader("🔍 Detalle de Diferencias Diarias")
        
        df_num = pd.DataFrame(results, columns=["Sucursal", "Total DB", "Total Excel", "Diferencia", "Días DB", "Días Excel"])
        df_num["Diferencia"] = df_num["Diferencia"].astype(float)
        sucursales_con_diff = df_num[df_num["Diferencia"].abs() > 0.01]["Sucursal"].tolist()

        if sucursales_con_diff:
            selected_suc = st.selectbox("Ver detalle por sucursal con diferencias totales:", ["Todas"] + sucursales_con_diff)
            
            detail_query = """
            WITH db_daily AS (
                SELECT 
                    s.prefijo,
                    s.etiqueta_suc,
                    c.invoice_date::date as date,
                    SUM(c.total_ingresos) as total_db
                FROM tblcierresz c
                JOIN tblsucursales s ON c.branch_id = s.branch_id
                WHERE EXTRACT(MONTH FROM c.invoice_date) = %s AND EXTRACT(YEAR FROM c.invoice_date) = %s
                GROUP BY s.prefijo, s.etiqueta_suc, c.invoice_date::date
            ),
            excel_daily AS (
                SELECT 
                    sucursal_prefijo as prefijo,
                    fecha as date,
                    SUM(monto) as total_excel
                FROM tbl_ventas_excel
                WHERE EXTRACT(MONTH FROM fecha) = %s AND EXTRACT(YEAR FROM fecha) = %s
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
            """
            params = [mes, anio, mes, anio]
            
            if selected_suc != "Todas":
                detail_query += " AND COALESCE(d.etiqueta_suc, e.prefijo) = %s"
                params.append(selected_suc)
                
            detail_query += " ORDER BY sucursal, fecha"
            
            det_results = db.fetch_all(detail_query, tuple(params))
            
            if det_results:
                df_det = pd.DataFrame(det_results, columns=["Sucursal", "Fecha", "Total DB (Z)", "Total Excel", "Diferencia"])
                df_det["Total DB (Z)"] = df_det["Total DB (Z)"].apply(lambda x: f"${float(x):,.2f}")
                df_det["Total Excel"] = df_det["Total Excel"].apply(lambda x: f"${float(x):,.2f}")
                
                def format_diff(val):
                    val_float = float(val)
                    if val_float < 0:
                         return f"-${abs(val_float):,.2f}"
                    return f"${val_float:,.2f}"
                
                df_det["Diferencia"] = df_det["Diferencia"].apply(format_diff)
                st.dataframe(df_det, use_container_width=True, hide_index=True)
            else:
                st.info("No se encontraron diferencias diarias para la selección actual.")
        else:
            st.success("¡No hay discrepancias en ninguna sucursal este mes!")

elif page == "Exportar Reportes":
    st.title("📥 Exportar Reportes de Ventas")
    st.write("Genera un archivo Excel con el resumen y detalle de ventas por sucursal.")
    
    db = get_db()
    
    # Obtener sucursales
    sucs_res = db.fetch_all("SELECT prefijo, etiqueta_suc FROM tblsucursales ORDER BY etiqueta_suc")
    suc_options = {f"{s[1]} ({s[0]})": s[0] for s in sucs_res}
    suc_display = ["Todas las Sucursales"] + list(suc_options.keys())
    
    selected_display = st.selectbox("Selecciona la Sucursal", suc_display)
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Fecha Inicio", datetime(2026, 1, 1))
    with col2:
        end_date = st.date_input("Fecha Fin", datetime.now())
        
    if st.button("Generar Archivo Excel"):
        with st.spinner("Generando reporte..."):
            prefijo = suc_options.get(selected_display)
            
            # Query para Detalle
            det_query = """
            SELECT fecha, nombre_almacen as nombrealmacen, sucursal_prefijo as numserie, referencia, monto as pvpdcto, iva
            FROM tbl_ventas_excel
            WHERE fecha BETWEEN %s AND %s
            """
            params = [start_date, end_date]
            if prefijo:
                det_query += " AND sucursal_prefijo = %s"
                params.append(prefijo)
            det_query += " ORDER BY fecha, numserie"
            
            df_detalle = pd.DataFrame(db.fetch_all(det_query, tuple(params)), 
                                     columns=["fecha", "nombrealmacen", "numserie", "referencia", "pvpdcto", "iva"])
            
            # Query para Resumen (diario por sucursal)
            res_query = """
            SELECT fecha, nombre_almacen, sucursal_prefijo, SUM(monto) as total_ventas
            FROM tbl_ventas_excel
            WHERE fecha BETWEEN %s AND %s
            """
            params_res = [start_date, end_date]
            if prefijo:
                res_query += " AND sucursal_prefijo = %s"
                params_res.append(prefijo)
            res_query += " GROUP BY fecha, nombre_almacen, sucursal_prefijo ORDER BY fecha, sucursal_prefijo"
            
            df_resumen = pd.DataFrame(db.fetch_all(res_query, tuple(params_res)), 
                                     columns=["fecha", "nombre_almacen", "sucursal_prefijo", "total_ventas"])
            
            if df_detalle.empty:
                st.error("No hay datos para los filtros seleccionados.")
            else:
                # Ajustes solicitados por el usuario para el Resumen
                df_resumen['total_ventas'] = df_resumen['total_ventas'].astype(float)
                df_resumen = df_resumen.drop(columns=['sucursal_prefijo'])
                
                import io
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
                    df_detalle.to_excel(writer, sheet_name='Detalle', index=False)
                
                st.download_button(
                    label="⬇️ Descargar Excel",
                    data=output.getvalue(),
                    file_name=f"Reporte_Ventas_{selected_display.replace(' ', '_')}_{start_date}_{end_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

elif page == "Configuración":
    st.title("⚙️ Configuración")
    st.info("Aquí podrás configurar prefijos de sucursales y otros parámetros en el futuro.")
