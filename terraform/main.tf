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

resource "aws_security_group" "sg_web" {
  name        = "redcuidado-web-sg"
  description = "Permitir HTTP, HTTPS y SSH"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "sg_mongo" {
  name        = "redcuidado-mongo-sg"
  description = "Permitir tráfico interno de MongoDB y SSH"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 27017
    to_port     = 27017
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_key_pair" "deployer" {
  key_name   = "mongo_key_aws"
  public_key = file("~/.ssh/mongo_key.pub")
}

resource "aws_instance" "web" {
  ami                    = "ami-0c7217cdde317cfec"
  instance_type          = "t2.micro"
  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.sg_web.id]
  tags                   = { Name = "RedCuidado-App" }
}

resource "aws_instance" "mongo_primary" {
  ami                    = "ami-0c7217cdde317cfec"
  instance_type          = "t2.micro"
  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.sg_mongo.id]
  tags                   = { Name = "Mongo-Primary" }
}

resource "aws_instance" "mongo_secondary" {
  ami                    = "ami-0c7217cdde317cfec"
  instance_type          = "t2.micro"
  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.sg_mongo.id]
  tags                   = { Name = "Mongo-Secondary-1" }
}

resource "aws_instance" "mongo_secondary2" {
  ami                    = "ami-0c7217cdde317cfec"
  instance_type          = "t2.micro"
  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.sg_mongo.id]
  tags                   = { Name = "Mongo-Secondary-2" }
}

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

resource "aws_glue_catalog_database" "athena_analytics" {
  name = "redcuidado_analytics"
}


output "ip_web" {
  value = aws_instance.web.public_ip
}

output "ip_mongo_primary" {
  value = aws_instance.mongo_primary.public_ip
}

output "ip_mongo_secondary" {
  value = aws_instance.mongo_secondary.public_ip
}

output "ip_mongo_secondary2" {
  value = aws_instance.mongo_secondary2.public_ip
}


resource "local_file" "ansible_inventory" {
  content = <<EOF
[webserver]
${aws_instance.web.public_ip} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/mongo_key

[mongodb_primary]
${aws_instance.mongo_primary.public_ip} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/mongo_key private_ip=${aws_instance.mongo_primary.private_ip}

[mongodb_secondary]
${aws_instance.mongo_secondary.public_ip} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/mongo_key private_ip=${aws_instance.mongo_secondary.private_ip}

[mongodb_secondary2]
${aws_instance.mongo_secondary2.public_ip} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/mongo_key private_ip=${aws_instance.mongo_secondary2.private_ip}

[mongodb:children]
mongodb_primary
mongodb_secondary
mongodb_secondary2

[all:vars]
ansible_ssh_common_args='-o StrictHostKeyChecking=no'
EOF

  filename = "${path.module}/../ansible/inventory.ini"
}

resource "null_resource" "ejecutar_ansible" {
  depends_on = [
    local_file.ansible_inventory,
    aws_instance.web,
    aws_instance.mongo_primary,
    aws_instance.mongo_secondary,
    aws_instance.mongo_secondary2
  ]

  provisioner "local-exec" {
    command = "sleep 30 && ansible-playbook -i ../ansible/inventory.ini ../ansible/01_setup_mongodb.yml"
  }
}
