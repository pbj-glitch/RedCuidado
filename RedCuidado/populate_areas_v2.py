import os
import django
import random

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RedCuidado.settings')
django.setup()

from django.contrib.auth.models import User, Group
from lms.models import WorkArea, UserProfile

# 1. Define exact required areas
REQUIRED_AREAS = [
    "Profesional de Atención Directa",
    "Técnico de Atención Directa",
    "Asistente de Trato Directo",
    "Auxiliares de Servicio",
    "Manipuladores de Alimentos",
    "Administración y Apoyo",
    "Directivos"
]

def run():
    print(" Limpiando áreas de trabajo antiguas...")
    # NOTE: This won't delete courses, but removes the M2M relations and old profiles.
    WorkArea.objects.all().delete()
    
    # Also clean test users (starting with 'test_') to maintain clean state
    User.objects.filter(username__startswith='test_').delete()

    print(" Creando nuevas áreas de trabajo...")
    areas_objects = {}
    for area_name in REQUIRED_AREAS:
        wa, created = WorkArea.objects.get_or_create(name=area_name)
        areas_objects[area_name] = wa
        print(f"   => {'Creada' if created else 'Ya existía'}: {area_name}")

    print("\n Generando usuarios de prueba por área...")
    
    # We create a random standard user for each area
    for idx, area_name in enumerate(REQUIRED_AREAS):
        username = f"test_user_{idx+1}"
        email = f"{username}@redcuidado.org"
        password = "password123"
        
        user, ucreated = User.objects.get_or_create(username=username, email=email)
        if ucreated:
            user.set_password(password)
            user.save()
            print(f"   => Usuario creado: {username} (Contraseña: {password})")
        
        # Ensure profile exists and assign area
        profile, pcreated = UserProfile.objects.get_or_create(user=user)
        profile.work_area = areas_objects[area_name]
        profile.employee_id = f"EMP-{1000+idx}"
        profile.headquarters = random.choice(['Hualpen', 'Coyhaique'])
        profile.save()
        
        print(f"      -> Asignado a: {area_name} ({profile.get_headquarters_display()})")

    print("\n Proceso completado exitosamente.")

if __name__ == '__main__':
    run()
