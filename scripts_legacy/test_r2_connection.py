import os
import boto3
from dotenv import load_dotenv

def test_connection():
    load_dotenv()
    
    endpoint_url = os.environ.get("R2_ENDPOINT_URL")
    access_key = os.environ.get("R2_ACCESS_KEY_ID")
    secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")
    bucket_name = os.environ.get("R2_BUCKET_NAME")

    print(f"Probando conexión a R2...")
    print(f"Endpoint: {endpoint_url}")
    print(f"Bucket: {bucket_name}")
    
    if not all([endpoint_url, access_key, secret_key, bucket_name]):
        print("❌ Error: Faltan variables de entorno en el archivo .env")
        return

    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        
        # Intentar listar objetos para probar credenciales (limit a 1 para no demorar)
        print("\nAutenticando y conectando...")
        response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        
        print("✅ ¡Conexión exitosa a Cloudflare R2!")
        print(f"✅ Se pudo acceder al bucket '{bucket_name}' correctamente.")
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    test_connection()
