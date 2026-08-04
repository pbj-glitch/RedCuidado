import sqlite3
import boto3
from pathlib import Path

# Ruta a la base de datos SQLite recién poblada
BASE_DIR = Path(__file__).resolve().parent.parent
SQLITE_DB_PATH = BASE_DIR / "RedCuidado" / "db.sqlite3"

# Instanciar cliente de DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table("RedCuidado_Data")

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row) if value is not None}

def run_etl():
    if not SQLITE_DB_PATH.exists():
        print(f"ERROR: No existe el archivo en {SQLITE_DB_PATH}")
        return

    print(f"Conectando a {SQLITE_DB_PATH}...")
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = dict_factory
    cursor = conn.cursor()

    print("Iniciando ETL desnormalizado hacia AWS DynamoDB...")

    with table.batch_writer() as batch:
        # 1. Migrar USUARIOS (auth_user)
        cursor.execute("SELECT id, username, email, first_name, last_name FROM auth_user;")
        users = cursor.fetchall()
        for user in users:
            batch.put_item(Item={
                'PK': f"USER#{user['id']}",
                'SK': "PROFILE",
                'entity_type': 'USER',
                'username': user['username'],
                'email': user['email'],
                'full_name': f"{user['first_name']} {user['last_name']}".strip()
            })
        print(f"✅ Migrados {len(users)} usuarios.")

        # 2. Migrar CURSOS (lms_course)
        try:
            cursor.execute("SELECT id, title, code, description, duration_days FROM lms_course;")
            courses = cursor.fetchall()
            for course in courses:
                batch.put_item(Item={
                    'PK': f"COURSE#{course['id']}",
                    'SK': "METADATA",
                    'entity_type': 'COURSE',
                    'title': course['title'],
                    'code': course['code'],
                    'description': course.get('description', ''),
                    'duration_days': course.get('duration_days', 30)
                })
            print(f"✅ Migrados {len(courses)} cursos.")
        except sqlite3.OperationalError as e:
            print(f"⚠️ Error al migrar cursos: {e}")

        # 3. Migrar INSCRIPCIONES (lms_enrollment)
        try:
            cursor.execute("SELECT id, user_id, course_id, enrolled_at, is_completed FROM lms_enrollment;")
            enrollments = cursor.fetchall()
            for enr in enrollments:
                batch.put_item(Item={
                    'PK': f"USER#{enr['user_id']}",
                    'SK': f"ENROLLMENT#COURSE#{enr['course_id']}",
                    'entity_type': 'ENROLLMENT',
                    'enrolled_at': str(enr['enrolled_at']),
                    'is_completed': bool(enr['is_completed'])
                })
            print(f"✅ Migradas {len(enrollments)} inscripciones.")
        except sqlite3.OperationalError as e:
            print(f"⚠️ Error al migrar inscripciones: {e}")

        # 4. Migrar BITÁCORA (lms_bitacoraentry)
        try:
            cursor.execute("SELECT id, author_id, entry_type, description, created_at FROM lms_bitacoraentry;")
            bitacoras = cursor.fetchall()
            for b in bitacoras:
                batch.put_item(Item={
                    'PK': f"BITACORA#{b['id']}",
                    'SK': "ENTRY",
                    'entity_type': 'BITACORA',
                    'author_id': b['author_id'],
                    'entry_type': b['entry_type'],
                    'description': b['description'],
                    'created_at': str(b['created_at'])
                })
            print(f"✅ Migradas {len(bitacoras)} entradas de bitácora.")
        except sqlite3.OperationalError as e:
            print(f"⚠️ Error al migrar bitácora: {e}")

    conn.close()
    print("🚀 ¡Proceso de migración ETL completado con éxito!")

if __name__ == "__main__":
    run_etl()
