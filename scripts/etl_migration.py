import os
from pathlib import Path
import boto3
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Obtener la ruta de la raíz del proyecto (un nivel arriba de /scripts)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise ValueError("ERROR: No se encontró la variable DATABASE_URL en el archivo .env")

# 1. Configurar conexión a PostgreSQL (Supabase)
conn = psycopg2.connect(db_url)

# 2. Configurar cliente DynamoDB (AWS)
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table_name = "RedCuidado_Data"  # El nombre que definiste en Terraform
table = dynamodb.Table(table_name)

def migrate_users():
    print("Iniciando migración de Usuarios...")
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # EXTRACT
        cursor.execute("SELECT id, email, first_name, last_name FROM auth_user;")
        users = cursor.fetchall()
        
        # TRANSFORM & LOAD
        with table.batch_writer() as batch:
            for user in users:
                item = {
                    'PK': f"USER#{user['id']}",
                    'SK': "PROFILE",
                    'email': user['email'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'entity_type': 'USER'
                }
                # LOAD a DynamoDB
                batch.put_item(Item=item)
    print("Usuarios migrados exitosamente.")

if __name__ == "__main__":
    try:
        migrate_users()
        print("Proceso ETL completado con éxito.")
    except Exception as e:
        print(f"Error durante el ETL: {e}")
    finally:
        conn.close()
