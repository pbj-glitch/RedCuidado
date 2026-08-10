output "dynamodb_table_name" {
  value = aws_dynamodb_table.red_cuidado.name
}

output "s3_bucket_name" {
  value = aws_s3_bucket.storage.id
}