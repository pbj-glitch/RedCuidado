import argparse
import csv
import io
import os
import sqlite3
import time
from pathlib import Path

import boto3


BASE_DIR = Path(__file__).resolve().parent.parent
SQLITE_DB_PATH = BASE_DIR / "RedCuidado" / "db.sqlite3"
AWS_REGION = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
ATHENA_DATABASE = os.getenv("ATHENA_DATABASE", "redcuidado_analytics")
ATHENA_PREFIX = "athena"

EXPORTS = {
    "users": {
        "query": "SELECT id, username, email, first_name, last_name, is_active FROM auth_user",
        "columns": [
            ("id", "bigint"),
            ("username", "string"),
            ("email", "string"),
            ("first_name", "string"),
            ("last_name", "string"),
            ("is_active", "boolean"),
        ],
    },
    "courses": {
        "query": "SELECT id, title, code, description, duration_days FROM lms_course",
        "columns": [
            ("id", "bigint"),
            ("title", "string"),
            ("code", "string"),
            ("description", "string"),
            ("duration_days", "bigint"),
        ],
    },
    "enrollments": {
        "query": "SELECT id, user_id, course_id, enrolled_at, is_completed FROM lms_enrollment",
        "columns": [
            ("id", "bigint"),
            ("user_id", "bigint"),
            ("course_id", "bigint"),
            ("enrolled_at", "string"),
            ("is_completed", "boolean"),
        ],
    },
    "test_results": {
        "query": "SELECT id, user_id, test_id, score, passed, attempted_at FROM lms_testresult",
        "columns": [
            ("id", "bigint"),
            ("user_id", "bigint"),
            ("test_id", "bigint"),
            ("score", "double"),
            ("passed", "boolean"),
            ("attempted_at", "string"),
        ],
    },
    "bitacora": {
        "query": "SELECT id, author_id, entry_type, description, created_at FROM lms_bitacoraentry",
        "columns": [
            ("id", "bigint"),
            ("author_id", "bigint"),
            ("entry_type", "string"),
            ("description", "string"),
            ("created_at", "string"),
        ],
    },
}


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row) if value is not None}


def extract_sqlite_data(connection):
    cursor = connection.cursor()
    extracted = {}
    for table_name, definition in EXPORTS.items():
        try:
            cursor.execute(definition["query"])
            extracted[table_name] = cursor.fetchall()
            print(f"Extraídas {len(extracted[table_name])} filas de {table_name}.")
        except sqlite3.OperationalError as exc:
            extracted[table_name] = []
            print(f"Advertencia: no se pudo extraer {table_name}: {exc}")
    return extracted


def load_dynamodb(data, table_name):
    table = boto3.resource("dynamodb", region_name=AWS_REGION).Table(table_name)
    with table.batch_writer() as batch:
        for user in data["users"]:
            batch.put_item(Item={
                "PK": f"USER#{user['id']}",
                "SK": "PROFILE",
                "entity_type": "USER",
                "username": user["username"],
                "email": user.get("email", ""),
                "full_name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                "is_active": bool(user.get("is_active", False)),
            })
        for course in data["courses"]:
            batch.put_item(Item={
                "PK": f"COURSE#{course['id']}",
                "SK": "METADATA",
                "entity_type": "COURSE",
                "title": course["title"],
                "code": course["code"],
                "description": course.get("description", ""),
                "duration_days": course.get("duration_days", 30),
            })
        for enrollment in data["enrollments"]:
            batch.put_item(Item={
                "PK": f"USER#{enrollment['user_id']}",
                "SK": f"ENROLLMENT#COURSE#{enrollment['course_id']}",
                "entity_type": "ENROLLMENT",
                "enrolled_at": str(enrollment["enrolled_at"]),
                "is_completed": bool(enrollment["is_completed"]),
            })
        for entry in data["bitacora"]:
            batch.put_item(Item={
                "PK": f"BITACORA#{entry['id']}",
                "SK": "ENTRY",
                "entity_type": "BITACORA",
                "author_id": entry["author_id"],
                "entry_type": entry["entry_type"],
                "description": entry["description"],
                "created_at": str(entry["created_at"]),
            })
    print(f"Carga a DynamoDB completada en {table_name}.")


def resolve_bucket(s3_client, explicit_bucket):
    if explicit_bucket:
        return explicit_bucket
    candidates = sorted(
        bucket["Name"]
        for bucket in s3_client.list_buckets().get("Buckets", [])
        if bucket["Name"].startswith("red-cuidado-storage-")
    )
    if not candidates:
        raise RuntimeError("Indica el bucket mediante --s3-bucket o S3_BUCKET_NAME.")
    return candidates[-1]


def export_to_s3(data, bucket, s3_client):
    for table_name, rows in data.items():
        columns = [name for name, _ in EXPORTS[table_name]["columns"]]
        boolean_columns = {
            name for name, data_type in EXPORTS[table_name]["columns"] if data_type == "boolean"
        }
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            serialized = dict(row)
            for column in boolean_columns:
                serialized[column] = "true" if bool(serialized.get(column)) else "false"
            writer.writerow(serialized)
        key = f"{ATHENA_PREFIX}/source/{table_name}/data.csv"
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=stream.getvalue().encode("utf-8"),
            ContentType="text/csv; charset=utf-8",
        )
        print(f"Exportado s3://{bucket}/{key} ({len(rows)} filas).")


def run_athena_query(client, query, output_location, database=None, timeout=300):
    request = {
        "QueryString": query,
        "ResultConfiguration": {"OutputLocation": output_location},
    }
    if database:
        request["QueryExecutionContext"] = {"Database": database}
    query_id = client.start_query_execution(**request)["QueryExecutionId"]
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        execution = client.get_query_execution(QueryExecutionId=query_id)["QueryExecution"]
        state = execution["Status"]["State"]
        if state == "SUCCEEDED":
            return query_id
        if state in {"FAILED", "CANCELLED"}:
            reason = execution["Status"].get("StateChangeReason", "sin detalle")
            raise RuntimeError(f"La consulta Athena {query_id} terminó en {state}: {reason}")
        time.sleep(2)
    client.stop_query_execution(QueryExecutionId=query_id)
    raise TimeoutError(f"La consulta Athena {query_id} superó {timeout} segundos.")


def create_athena_tables(bucket, client):
    output_location = f"s3://{bucket}/{ATHENA_PREFIX}/query-results/"
    run_athena_query(
        client,
        f"CREATE DATABASE IF NOT EXISTS {ATHENA_DATABASE}",
        output_location,
    )
    for table_name, definition in EXPORTS.items():
        columns = ",\n  ".join(f"{name} {data_type}" for name, data_type in definition["columns"])
        ddl = f"""
CREATE EXTERNAL TABLE IF NOT EXISTS {ATHENA_DATABASE}.{table_name} (
  {columns}
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
  'separatorChar' = ',',
  'quoteChar' = '\"',
  'escapeChar' = '\\'
)
STORED AS TEXTFILE
LOCATION 's3://{bucket}/{ATHENA_PREFIX}/source/{table_name}/'
TBLPROPERTIES ('skip.header.line.count' = '1')
"""
        run_athena_query(client, ddl, output_location, ATHENA_DATABASE)
        print(f"Tabla externa Athena disponible: {ATHENA_DATABASE}.{table_name}")
    return output_location


def execute_analytics_queries(client, output_location):
    queries = {
        "cursos_totales": "SELECT COUNT(*) AS total_courses FROM courses",
        "tasa_finalizacion": (
            "SELECT COALESCE(ROUND(100.0 * SUM(CASE WHEN is_completed THEN 1 ELSE 0 END) "
            "/ NULLIF(COUNT(*), 0), 1), 0) AS completion_rate FROM enrollments"
        ),
        "puntaje_promedio": "SELECT COALESCE(ROUND(AVG(score), 1), 0) AS average_score FROM test_results",
    }
    for name, query in queries.items():
        query_id = run_athena_query(client, query, output_location, ATHENA_DATABASE)
        rows = client.get_query_results(QueryExecutionId=query_id, MaxResults=2)["ResultSet"]["Rows"]
        value = rows[1]["Data"][0].get("VarCharValue", "0") if len(rows) > 1 else "0"
        print(f"Athena KPI {name}: {value}")


def parse_args():
    parser = argparse.ArgumentParser(description="Migra SQLite a DynamoDB, S3 y Athena.")
    parser.add_argument("--s3-bucket", default=os.getenv("S3_BUCKET_NAME"))
    parser.add_argument("--dynamodb-table", default=os.getenv("DYNAMODB_TABLE", "RedCuidado_Data"))
    parser.add_argument("--skip-dynamodb", action="store_true")
    return parser.parse_args()


def run_etl():
    args = parse_args()
    if not SQLITE_DB_PATH.exists():
        raise FileNotFoundError(f"No existe la base SQLite en {SQLITE_DB_PATH}")

    with sqlite3.connect(SQLITE_DB_PATH) as connection:
        connection.row_factory = dict_factory
        data = extract_sqlite_data(connection)

    if not args.skip_dynamodb:
        load_dynamodb(data, args.dynamodb_table)

    s3_client = boto3.client("s3", region_name=AWS_REGION)
    bucket = resolve_bucket(s3_client, args.s3_bucket)
    export_to_s3(data, bucket, s3_client)

    athena_client = boto3.client("athena", region_name=AWS_REGION)
    output_location = create_athena_tables(bucket, athena_client)
    execute_analytics_queries(athena_client, output_location)
    print("Proceso ETL completado con éxito.")


if __name__ == "__main__":
    run_etl()
