# 🏥 RedCuidado LMS 
### Plataforma de Capacitación Inteligente para ONGs y ELEAM

[![Deploy with Vercel](https://vercel.com/button)](https://red-cuidado.vercel.app/)
[![Django](https://img.shields.io/badge/Framework-Django%205.0-092e20?logo=django)](https://www.djangoproject.com/)
[![Supabase](https://img.shields.io/badge/Database-Supabase%20(PostgreSQL)-3ecf8e?logo=supabase)](https://supabase.com/)

**RedCuidado** es una solución integral de gestión del aprendizaje (LMS) diseñada específicamente para Establecimientos de Larga Estadía para Adultos Mayores (ELEAM). La plataforma optimiza la formación continua del personal de salud y cuidado, garantizando el cumplimiento de estándares y la mejora en la calidad del servicio.

🔗 **Demo en Vivo:** [https://red-cuidado.vercel.app/](https://red-cuidado.vercel.app/)

---

## ✨ Características Principales

### 👨‍💼 Gestión Multi-Rol
- **Administradores:** Control total sobre el personal, áreas de trabajo y métricas globales.
- **Profesores:** Creación de contenido pedagógico, gestión de módulos multimedia y diseño de evaluaciones.
- **Colaboradores:** Acceso intuitivo a cursos, seguimiento de progreso personal y obtención de certificados.

### 📊 Dashboard de Analítica Avanzada
- **Visualización en tiempo real:** Gráficos dinámicos (Chart.js) que muestran la evolución mensual de capacitaciones.
- **Métricas por Sede:** Comparativa de desempeño entre sedes (Hualpén, Coyhaique).
- **Control de Completitud:** Seguimiento detallado por área de trabajo (Enfermería, Kinesiología, Nutrición, etc.).

### 📚 Experiencia de Aprendizaje (LXP)
- **Multimedia:** Soporte para videos, PDF y visor integrado de Microsoft Office Online para presentaciones PPTX.
- **Evaluaciones Inteligentes:** Exámenes con corrección automática y requisitos de puntaje mínimo.
- **Gamificación Ligera:** Sistema de "Pinning" para fijar cursos prioritarios en el inicio del usuario.
- **Calendario Integrado:** Gestión de plazos y fechas de inicio mediante FullCalendar.

---

###Prerrequisitos
En Linux / macOS
Asegúrate de contar con las siguientes herramientas en tu terminal:

AWS CLI (configurado con credenciales activas)

Terraform (>= 1.0)

Ansible (>= 2.10)

OpenSSH Client

###Como conectarse local: 
En Windows
Ansible requiere un entorno de tipo POSIX. La forma más sencilla y recomendada de ejecutar el proyecto en Windows es utilizando WSL2:

Abre PowerShell como Administrador e instala WSL:

PowerShell
wsl --install
Reinicia tu equipo e inicia la distribución de Ubuntu.

Instala las dependencias necesarias dentro de Ubuntu/WSL2:
sudo apt update && sudo apt install -y terraform ansible awscli git openssh-client

Paso a Paso para el Desplegado
1. Clonar el Repositorio
``` bash
git clone <URL_DE_TU_REPOSITORIO>
cd RedCuidado
git checkout feature/migracion-dynamodb
```

3. Configurar Credenciales de AWS
Si utilizas AWS Learner Lab, copia tus credenciales temporales (ubicadas en AWS Details -> AWS CLI) y ejecútalas en la terminal:
``` bash
export AWS_ACCESS_KEY_ID="TU_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="TU_SECRET_KEY"
export AWS_SESSION_TOKEN="TU_SESSION_TOKEN"
export AWS_DEFAULT_REGION="us-east-1"
```

3. Crear la Clave SSH Local
El archivo main.tf registra automáticamente tu clave pública local en AWS. Si aún no tienes la clave mongo_key creada en ~/.ssh/, genérala ejecutando:
``` bash
ssh-keygen -t rsa -b 4000 -f ~/.ssh/mongo_key -N ""
chmod 400 ~/.ssh/mongo_key
```

4. Ejecutar la Automatización (Terraform + Ansible)
Navega al directorio terraform e inicia el despliegue:
``` bash
cd terraform
terraform init
terraform apply -auto-approve
```
¿Qué ocurre durante este paso?
Terraform crea la infraestructura en AWS (Servidor Web, Nodos MongoDB, Bucket S3 y Tabla DynamoDB).

Genera automáticamente el archivo ansible/inventory.ini con las IPs Privadas para la comunicación interna entre nodos y las IPs Públicas para el acceso SSH.

Ejecuta el provisionador local-exec que llama al Playbook de Ansible.

Ansible instala MongoDB 7.0, configura los parámetros de red e inicializa el Replica Set (rs0).

Verificación del Clúster MongoDB
Una vez completado el terraform apply, obtén las IPs asignadas:
terraform output
Conéctate por SSH al nodo primario e inspecciona el estado del clúster:
``` bash
ssh -i ~/.ssh/mongo_key ubuntu@<IP_MONGO_PRIMARY>
mongosh --eval "rs.status()"
```
Deberás observar que el nodo al que te conectaste reporta "stateStr": "PRIMARY" y el nodo secundario reporta "stateStr": "SECONDARY".

Destruir la Infraestructura
Para eliminar todos los recursos creados en AWS y evitar consumos indeseados:

``` bash
cd terraform
terraform destroy -auto-approve
```

## 🛠️ Stack Tecnológico

1. Infraestructura Cloud (AWS)
Amazon EC2 (t2.micro): Instancias de cómputo para el servidor web (RedCuidado-App) y los nodos del clúster de base de datos (Mongo-Primary, Mongo-Secondary).
Amazon S3: Almacenamiento de objetos para archivos del proyecto (red-cuidado-storage-*).
Amazon DynamoDB: Base de datos NoSQL gestionada (RedCuidado_Data).
AWS VPC & Security Groups: Red privada virtual y reglas de firewall para aislar el tráfico (SSH en puerto 22, MongoDB en puerto 27017 en red privada).

2. Infraestructura como Código (IaC) y Automatización
Terraform: Creación, orquestación y gestión declarativa de todos los recursos en AWS.
Ansible: Configuración de servidor, aprovisionamiento de software y automatización del Replica Set de MongoDB.
OpenSSH / SSH Keys: Autenticación segura mediante llaves RSA/PEM (mongo_key).

3. Base de Datos NoSQL
MongoDB Community Server (v7.0): Motor de base de datos documento-orientado.
MongoDB Replica Set (rs0): Configuración de alta disponibilidad con nodos Primary y Secondary comunicados por IPs privadas de AWS VPC.
mongosh: Shell oficial de MongoDB para administración y verificación del estado del clúster.

4. Capa de Aplicación y Sistema Operativo
Sistema Operativo: Ubuntu 22.04 LTS (Jammy Jellyfish).
Entorno de Ejecución: Python 3.10.
Framework Web: Django.

5. Herramientas de Control de Versiones y Entorno Local
Git & GitHub: Control de versiones (rama feature/migracion-dynamodb).
WSL2 (Ubuntu en Windows) / macOS Terminal: Entorno de ejecución local para Terraform y Ansible.

---

## 📁 Estructura del Proyecto

```text
RedCuidado/
├── ansible/
│   ├── 01_setup_mongodb.yml   # Playbook para instalar y configurar el Replica Set
│   └── inventory.ini          # Generado automáticamente por Terraform
├── terraform/
│   ├── main.tf                # Configuración de AWS (EC2, S3, DynamoDB, Security Groups)
│   └── outputs.tf             # Salida con las IPs y recursos creados
├── .gitignore
└── README.md
```

---



## 🛡️ Seguridad y Roles

La plataforma implementa un sistema robusto de permisos mediante decoradores personalizados:
- `@admin_required`: Acceso exclusivo para directores y administradores de sistema.
- `@staff_required`: Permisos para creación y edición de material educativo.
- `@login_required`: Acceso restringido para colaboradores autenticados.

---

## 👥 Equipo de Desarrollo

*   **Benjamín Pinto**
*   **Benjamín Levitt**
*   **Ian Spikin**

---
© 2026 RedCuidado - Innovación en el Cuidado del Adulto Mayor.
