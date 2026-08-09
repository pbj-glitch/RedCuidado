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

# -----------------------------------------------------------------------------
# SECURITY GROUPS (REGLAS DE RED)
# -----------------------------------------------------------------------------

# Security Group para la Aplicacion Web
resource "aws_security_group" "sg_web" {
  name        = "redcuidado-web-sg"
  description = "Permitir HTTP, HTTPS y SSH"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # SSH desde cualquier IP
  }

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Django / Web
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Security Group para los Nodos de MongoDB
resource "aws_security_group" "sg_mongo" {
  name        = "redcuidado-mongo-sg"
  description = "Permitir traffic interno de MongoDB y SSH"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # SSH para Ansible
  }

  # Permitir puerto 27017 entre los nodos del cluster y desde la App Web
  ingress {
    from_port   = 27017
    to_port     = 27017
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # En producción se limita a las IPs de la VPC
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# -----------------------------------------------------------------------------
# INSTANCIAS EC2
# -----------------------------------------------------------------------------
# 1. Registrar tu clave local en AWS automáticamente
resource "aws_key_pair" "deployer" {
  key_name   = "mongo_key_aws"
  public_key = file("~/.ssh/mongo_key.pub")
}

# 2. Asignar esa clave registrada a tus instancias
resource "aws_instance" "web" {
  ami                    = "ami-0c7217cdde317cfec"
  instance_type          = "t2.micro"
  key_name               = aws_key_pair.deployer.key_name  # <--- Asignación automática
  vpc_security_group_ids = [aws_security_group.sg_web.id]
  tags                   = { Name = "RedCuidado-App" }
}

resource "aws_instance" "mongo_primary" {
  ami                    = "ami-0c7217cdde317cfec"
  instance_type          = "t2.micro"
  key_name               = aws_key_pair.deployer.key_name  # <--- Asignación automática
  vpc_security_group_ids = [aws_security_group.sg_mongo.id]
  tags                   = { Name = "Mongo-Primary" }
}

resource "aws_instance" "mongo_secondary" {
  ami                    = "ami-0c7217cdde317cfec"
  instance_type          = "t2.micro"
  key_name               = aws_key_pair.deployer.key_name  # <--- Asignación automática
  vpc_security_group_ids = [aws_security_group.sg_mongo.id]
  tags                   = { Name = "Mongo-Secondary" }
}

# -----------------------------------------------------------------------------
# DYNAMODB & S3 (RECURSOS COMPLEMENTARIOS)
# -----------------------------------------------------------------------------

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

resource "aws_s3_bucket" "storage" {
  bucket_prefix = "red-cuidado-storage-"
  force_destroy = true
}

# -----------------------------------------------------------------------------
# OUTPUTS (PARA OBTENER LAS IPs AUTOMÁTICAMENTE PARA ANSIBLE)
# -----------------------------------------------------------------------------

output "ip_web" {
  value = aws_instance.web.public_ip
}

output "ip_mongo_primary" {
  value = aws_instance.mongo_primary.public_ip
}

output "ip_mongo_secondary" {
  value = aws_instance.mongo_secondary.public_ip
}

# -----------------------------------------------------------------------------
# EJECUCIÓN DE ANSIBLE
# -----------------------------------------------------------------------------

resource "local_file" "ansible_inventory" {
  content = <<EOF
[webserver]
${aws_instance.web.public_ip} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/mongo_key

[mongodb_primary]
${aws_instance.mongo_primary.public_ip} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/mongo_key private_ip=${aws_instance.mongo_primary.private_ip}

[mongodb_secondary]
${aws_instance.mongo_secondary.public_ip} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/mongo_key private_ip=${aws_instance.mongo_secondary.private_ip}

[mongodb:children]
mongodb_primary
mongodb_secondary

[all:vars]
ansible_ssh_common_args='-o StrictHostKeyChecking=no'
EOF

  filename = "${path.module}/../ansible/inventory.ini"
}

# 2. Ejecutar Ansible usando el inventario recién creado
resource "null_resource" "ejecutar_ansible" {
  depends_on = [
    local_file.ansible_inventory,
    aws_instance.web,
    aws_instance.mongo_primary,
    aws_instance.mongo_secondary
  ]

  provisioner "local-exec" {
    command = "sleep 30 && ansible-playbook -i ../ansible/inventory.ini ../ansible/01_setup_mongodb.yml"
  }
}