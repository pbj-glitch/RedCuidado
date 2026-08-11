"""
Genera los mismos CSV que sube etl_from_sqlite.py a S3, pero LOCALMENTE
y sin necesitar boto3 ni credenciales de AWS.

Uso:
    python scripts/generate_csv_local.py
    python scripts/generate_csv_local.py --output-dir mis_csvs

Los archivos quedan en <output_dir>/<tabla>/data.csv (por defecto en
csv_export/<tabla>/data.csv), listos para:
  a) que alguien con acceso a la consola de AWS los arrastre al bucket S3
     en la ruta athena/source/<tabla>/data.csv, o
  b) subirlos manualmente cuando recuperes credenciales.

El esquema y el orden de columnas es IDÉNTICO al de scripts/etl_from_sqlite.py
para que las tablas externas de Athena (definidas en ese mismo script) lean
estos archivos sin cambios.
"""

import argparse
import csv
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SQLITE_DB_PATH = BASE_DIR / "RedCuidado" / "db.sqlite3"

# Debe coincidir exactamente con EXPORTS en scripts/etl_from_sqlite.py
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
            print(f"Extraidas {len(extracted[table_name])} filas de {table_name}.")
        except sqlite3.OperationalError as exc:
            extracted[table_name] = []
            print(f"Advertencia: no se pudo extraer {table_name}: {exc}")
    return extracted


def write_local_csv(data, output_dir):
    output_dir = Path(output_dir)
    for table_name, rows in data.items():
        columns = [name for name, _ in EXPORTS[table_name]["columns"]]
        boolean_columns = {
            name for name, data_type in EXPORTS[table_name]["columns"] if data_type == "boolean"
        }
        table_dir = output_dir / table_name
        table_dir.mkdir(parents=True, exist_ok=True)
        csv_path = table_dir / "data.csv"

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                serialized = dict(row)
                for column in boolean_columns:
                    serialized[column] = "true" if bool(serialized.get(column)) else "false"
                writer.writerow(serialized)

        print(f"Generado: {csv_path} ({len(rows)} filas)")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Genera localmente los CSV que espera Athena, sin usar AWS."
    )
    parser.add_argument(
        "--output-dir",
        default=str(BASE_DIR / "csv_export"),
        help="Carpeta donde se guardan los CSV (por defecto: ./csv_export)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not SQLITE_DB_PATH.exists():
        raise FileNotFoundError(
            f"No existe la base SQLite en {SQLITE_DB_PATH}. "
            "Corre primero: python manage.py migrate y los scripts populate_*.py"
        )

    with sqlite3.connect(SQLITE_DB_PATH) as connection:
        connection.row_factory = dict_factory
        data = extract_sqlite_data(connection)

    write_local_csv(data, args.output_dir)

    print("\nListo. Sube cada carpeta a S3 en la ruta:")
    print("  s3://<tu-bucket>/athena/source/<tabla>/data.csv")
    print("(arrastrando el archivo data.csv de cada subcarpeta desde la consola de AWS)")


if __name__ == "__main__":
    main()
