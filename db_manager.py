import os
import psycopg2
from psycopg2 import pool, extras
from dotenv import load_dotenv

load_dotenv()

class PostgresManager:
    _connection_pool = None

    def __init__(self):
        """
        Inicializa el pool de conexiones a Postgres usando variables de entorno.
        """
        if PostgresManager._connection_pool is None:
            try:
                PostgresManager._connection_pool = psycopg2.pool.SimpleConnectionPool(
                    1, 10,
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    host=os.getenv("DB_HOST"),
                    port=os.getenv("DB_PORT"),
                    database=os.getenv("DB_NAME")
                )
                print("Pool de conexiones creado con éxito.")
                
                # Ensure missing columns from recent features exist
                conn = PostgresManager._connection_pool.getconn()
                try:
                    with conn.cursor() as cur:
                        cur.execute("ALTER TABLE tbl_cierres_z_master ADD COLUMN IF NOT EXISTS workflow_status VARCHAR(50) DEFAULT 'draft';")
                        cur.execute("ALTER TABLE tbl_cierres_z_master ADD COLUMN IF NOT EXISTS credit_notes NUMERIC(15,2) DEFAULT 0.00;")
                        cur.execute("ALTER TABLE tbl_companies ADD COLUMN IF NOT EXISTS logo_url TEXT;")
                        conn.commit()
                except Exception as e:
                    print(f"Error asegurando el esquema de base de datos: {e}")
                    conn.rollback()
                finally:
                    PostgresManager._connection_pool.putconn(conn)

            except (Exception, psycopg2.DatabaseError) as error:
                print(f"Error al conectar con PostgreSQL: {error}")
                raise

    def get_connection(self):
        return PostgresManager._connection_pool.getconn()

    def release_connection(self, conn):
        PostgresManager._connection_pool.putconn(conn)

    def execute_query(self, query, params=None):
        """
        Ejecuta una consulta que no devuelve resultados (INSERT, UPDATE, DELETE).
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                conn.commit()
                return cur.rowcount
        finally:
            self.release_connection(conn)

    def fetch_all(self, query, params=None):
        """
        Ejecuta una consulta que devuelve múltiples resultados (SELECT).
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()
        finally:
            self.release_connection(conn)

    def fetch_one(self, query, params=None):
        """
        Ejecuta una consulta que devuelve un solo resultado.
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchone()
        finally:
            self.release_connection(conn)

    def execute_batch(self, query, params_list, page_size=100):
        """
        Ejecuta múltiples inserciones/actualizaciones en lotes.
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                extras.execute_batch(cur, query, params_list, page_size=page_size)
                conn.commit()
                return len(params_list)
        except Exception:
            conn.rollback()
            raise
        finally:
            self.release_connection(conn)
            
    def close_all_connections(self):
        if PostgresManager._connection_pool:
            PostgresManager._connection_pool.closeall()
            print("Conexiones de PostgreSQL cerradas.")

# Ejemplo de uso:
if __name__ == "__main__":
    db = PostgresManager()
    try:
        version = db.fetch_one("SELECT version();")
        print(f"Conectado a: {version[0]}")
    finally:
        db.close_all_connections()
