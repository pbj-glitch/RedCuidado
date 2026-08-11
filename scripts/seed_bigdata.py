import boto3
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Conexión a DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('RedCuidado_Data')

# Parámetros para simulación masiva
NUM_USERS = 1500
NUM_COURSES = 12
NUM_ENROLLMENTS = 4000
NUM_TESTS = 3500
NUM_BITACORA = 2000

FIRST_NAMES = ["Maria", "Juan", "Pedro", "Carla", "Diego", "Ana", "Luis", "Sofia", "Gabriel", "Lucia"]
LAST_NAMES = ["Perez", "Gonzalez", "Tapia", "Soto", "Muñoz", "Rojas", "Diaz", "Contreras", "Silva", "Morales"]
COURSE_NAMES = [
    "Primeros Auxilios Básico", "Cuidado del Adulto Mayor", "Nutrición en la Infancia",
    "Manejo de Pacientes Crónicos", "Higiene y Salud Pública", "Soporte Vital Básico",
    "Atención Domiciliaria", "Ética en los Cuidados", "Prevención de Caídas",
    "Gestión de Medicamentos", "Primeros Auxilios Avanzado", "Salud Mental Comunitaria"
]

def random_date(days_back=180):
    start = datetime.now() - timedelta(days=days_back)
    random_days = random.randint(0, days_back)
    random_seconds = random.randint(0, 86400)
    return (start + timedelta(days=random_days, seconds=random_seconds)).strftime("%Y-%m-%d %H:%M:%S")

print("Generando datos de prueba masivos en DynamoDB...")

with table.batch_writer() as batch:
    # 1. Usuarios
    print(f"-> Insertando {NUM_USERS} usuarios...")
    for i in range(1, NUM_USERS + 1):
        fname = random.choice(FIRST_NAMES)
        lname = random.choice(LAST_NAMES)
        batch.put_item(Item={
            "PK": f"USER#{i}", "SK": "METADATA", "entity_type": "user",
            "id": i, "username": f"{fname.lower()}.{lname.lower()}{i}",
            "email": f"{fname.lower()}{i}@redcuidado.cl",
            "first_name": fname, "last_name": lname,
            "is_active": random.choices([True, False], weights=[0.85, 0.15])[0]
        })

    # 2. Cursos
    print(f"-> Insertando {NUM_COURSES} cursos...")
    for i in range(1, NUM_COURSES + 1):
        batch.put_item(Item={
            "PK": f"COURSE#{i}", "SK": "METADATA", "entity_type": "course",
            "id": i, "title": COURSE_NAMES[i - 1], "code": f"CUR-{i:02d}",
            "description": f"Capacitación profesional en {COURSE_NAMES[i - 1]}",
            "duration_days": random.choice([15, 30, 45, 60])
        })

    # 3. Inscripciones (Enrollments)
    print(f"-> Insertando {NUM_ENROLLMENTS} inscripciones...")
    for i in range(1, NUM_ENROLLMENTS + 1):
        batch.put_item(Item={
            "PK": f"ENROLLMENT#{i}", "SK": "METADATA", "entity_type": "enrollment",
            "id": i, "user_id": random.randint(1, NUM_USERS),
            "course_id": random.randint(1, NUM_COURSES),
            "enrolled_at": random_date(),
            "is_completed": random.choices([True, False], weights=[0.65, 0.35])[0]
        })

    # 4. Resultados de Evaluaciones (Test Results)
    print(f"-> Insertando {NUM_TESTS} evaluaciones...")
    for i in range(1, NUM_TESTS + 1):
        score = round(random.uniform(40.0, 100.0), 1)
        batch.put_item(Item={
            "PK": f"TEST#{i}", "SK": "METADATA", "entity_type": "test_result",
            "id": i, "user_id": random.randint(1, NUM_USERS),
            "test_id": random.randint(101, 120),
            "score": Decimal(str(score)), "passed": score >= 70.0,
            "attempted_at": random_date()
        })

    # 5. Bitácora
    print(f"-> Insertando {NUM_BITACORA} registros de bitácora...")
    for i in range(1, NUM_BITACORA + 1):
        batch.put_item(Item={
            "PK": f"BITACORA#{i}", "SK": "METADATA", "entity_type": "bitacora",
            "id": i, "author_id": random.randint(1, NUM_USERS),
            "entry_type": random.choice(["LOG", "WARN", "INFO", "AUDIT"]),
            "description": "Registro de actividad de sistema", "created_at": random_date()
        })

print("\n¡Carga masiva completada exitosamente en DynamoDB!")
