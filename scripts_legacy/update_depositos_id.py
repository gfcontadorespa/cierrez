from db_manager import PostgresManager

def update_depositos_schema():
    db = PostgresManager()
    try:
        print("1. Verificando si existe la columna 'deposito_id'...")
        # Comprobar si existe deposito_id
        check_col = db.fetch_one("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'tbl_depositos' AND column_name = 'deposito_id';
        """)
        
        if check_col:
            print("Renombrando 'deposito_id' a 'iddeposito'...")
            # Si existe como Primary Key, Postgres permitirá renombrarla
            db.execute_query("ALTER TABLE tbl_depositos RENAME COLUMN deposito_id TO iddeposito;")
        
        print("2. Cambiando tipo de 'iddeposito' a TEXT...")
        # Cambiar el tipo a TEXT
        db.execute_query("ALTER TABLE tbl_depositos ALTER COLUMN iddeposito TYPE TEXT USING iddeposito::text;")
        
        print("3. Asegurando que 'iddeposito' sea PRIMARY KEY...")
        # Verificar si ya es PK
        pk_check = db.fetch_one("""
            SELECT a.attname
            FROM   pg_index i
            JOIN   pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE  i.indrelid = 'tbl_depositos'::regclass
            AND    i.indisprimary;
        """)
        
        if not pk_check or pk_check[0] != 'iddeposito':
            print("Estableciendo 'iddeposito' como PRIMARY KEY...")
            # Si hay otra PK, la quitamos primero (poco probable pero por seguridad)
            if pk_check:
                db.execute_query("ALTER TABLE tbl_depositos DROP CONSTRAINT IF EXISTS tbl_depositos_pkey;")
            db.execute_query("ALTER TABLE tbl_depositos ADD PRIMARY KEY (iddeposito);")

        print("✅ Esquema de tbl_depositos actualizado correctamente.")
        
    except Exception as e:
        print(f"❌ Error al actualizar el esquema: {e}")
    finally:
        db.close_all_connections()

if __name__ == "__main__":
    update_depositos_schema()
