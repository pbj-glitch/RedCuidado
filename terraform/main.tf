terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Tabla DynamoDB (Single-Table Design base)
resource "aws_dynamodb_table" "red_cuidado" {
  name           = "RedCuidado_Data"
  billing_mode   = "PROVISIONED"
  read_capacity  = 25
  write_capacity = 25
  hash_key       = "PK"
  range_key      = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  tags = {
    Proyecto = "RedCuidado"
    Entorno  = "Laboratorio"
  }
}

# Bucket S3 para reemplazo de Supabase Storage
resource "aws_s3_bucket" "storage" {
  bucket_prefix = "red-cuidado-storage-"
  force_destroy = true
}