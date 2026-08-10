import os
import django

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RedCuidado.settings')
django.setup()

from django.contrib.auth.models import User, Group

groups = ["Empleado", "Profesor", "Administrador"]
for g in groups:
    Group.objects.get_or_create(name=g)

# Create users
def create_user(username, group_name):
    if not User.objects.filter(username=username).exists():
        u = User.objects.create_user(username=username, password='demo123')
        g = Group.objects.get(name=group_name)
        u.groups.add(g)
        print(f"Created {username} in {group_name}")

create_user('empleado', 'Empleado')
create_user('profesor', 'Profesor')
create_user('admin', 'Administrador')
