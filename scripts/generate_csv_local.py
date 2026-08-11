"""
Genera los mismos CSV que espera Athena leyendo directamente desde DynamoDB.
Soporta uso local y automatizado con Ansible / AWS CLI.

Uso:
    python scripts/generate_csv_local.py
    python scripts/generate_csv_local.py --output-dir mis_csvs
"""

import argparse
import csv
from decimal import Decimal
from pathlib import Path
import boto3

BASE_DIR = Path(__file__).resolve().parent.parent

# Mapeo de esquema requerido por Athena
EXPORTS = {
    "users": {
        "entity_type": "user",
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
        "entity_type": "course",
        "columns": [
            ("id", "bigint"),
            ("title", "string"),
            ("code", "string"),
            ("description", "string"),
            ("duration_days", "bigint"),
        ],
    },
    "enrollments": {
        "entity_type": "enrollment",
        "columns": [
            ("id", "bigint"),
            ("user_id", "bigint"),
            ("course_id", "bigint"),
            ("enrolled_at", "string"),
            ("is_completed", "boolean"),
        ],
    },
    "test_results": {
        "entity_type": "test_result",
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
        "entity_type": "bitacora",
        "columns": [
            ("id", "bigint"),
            ("author_id", "bigint"),
            ("entry_type", "string"),
            ("description", "string"),
            ("created_at", "string"),
        ],
    },
}


def parse_decimal(val):
    if isinstance(val, Decimal):
        return int(val) if val % 1 == 0 else float(val)
    return val


def extract_dynamodb_data(table_name="RedCuidado_Data", region_name="us-east-1"):
    dynamodb = boto3.resource("dynamodb", region_name=region_name)
    table = dynamodb.Table(table_name)

    print(f"Escaneando tabla DynamoDB '{table_name}'...")
    response = table.scan()
    items = response.get("Items", [])

    # Paginación en caso de que la tabla sea grande
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    extracted = {table_key: [] for table_key in EXPORTS.keys()}

    for item in items:
        # Convierte números de DynamoDB (Decimal) a float/int
        clean_item = {k: parse_decimal(v) for k, v in item.items()}
        entity = clean_item.get("entity_type")

        for table_key, definition in EXPORTS.items():
            if entity == definition["entity_type"]:
                extracted[table_key].append(clean_item)

    for table_key, rows in extracted.items():
        print(f"Extraídas {len(rows)} filas de entidad '{EXPORTS[table_key]['entity_type']}' -> {table_key}")

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
                    val = serialized.get(column)
                    serialized[column] = "true" if str(val).lower() in ["true", "1"] else "false"
                writer.writerow(serialized)

        print(f"Generado: {csv_path} ({len(rows)} filas)")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extrae datos de DynamoDB y genera CSVs para AWS Athena."
    )
    parser.add_argument(
        "--output-dir",
        default=str(BASE_DIR / "csv_export"),
        help="Carpeta donde se guardan los CSV (por defecto: ./csv_export)",
    )
    parser.add_argument(
        "--table-name",
        default="RedCuidado_Data",
        help="Nombre de la tabla de DynamoDB",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    data = extract_dynamodb_data(table_name=args.table_name)
    write_local_csv(data, args.output_dir)

    print("\nProceso finalizado con éxito.")


if __name__ == "__main__":
    main()