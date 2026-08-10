import os
import django

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RedCuidado.settings')
django.setup()

from django.contrib.auth.models import User
from lms.models import Course, Module, Content, Enrollment

# Course Data
COURSES = [
    {
        'title': 'Fundamentos del Cuidado del Paciente',
        'code': 'ELD 101',
        'desc': 'Un curso detallado sobre el cuidado inicial.',
        'duration_days': 15,
    },
    {
        'title': 'Protocolos de Seguridad y Prevención de Caídas',
        'code': 'SAF 205',
        'desc': 'Cómo mantener seguros a los pacientes mayores.',
        'duration_days': 20,
    },
    {
        'title': 'Cuidado de Demencia y Memoria',
        'code': 'DEM 310',
        'desc': 'Aspectos clave del tratado moderno de la demencia.',
        'duration_days': 30,
    }
]

for cd in COURSES:
    c, created = Course.objects.get_or_create(code=cd['code'], defaults={'title': cd['title'], 'description': cd['desc'], 'duration_days': cd['duration_days']})
    if created:
        print(f"Created course {c.code}")
        # Add a module
        m = Module.objects.create(course=c, title="Módulo 1: Introducción", order=1)
        # Add basic content
        Content.objects.create(module=m, title="Bienvenida", content_type="video", duration="5 min", order=1)
        Content.objects.create(module=m, title="Manual de Normativas", content_type="pdf", duration="15 min", order=2)
        print(f"Added module and content to {c.code}")

# Enroll Empleado
try:
    empleado = User.objects.get(username='empleado')
    for course in Course.objects.all()[:2]: # Enroll in first 2
        enr, created = Enrollment.objects.get_or_create(user=empleado, course=course)
        if created:
            print(f"Enrolled {empleado.username} in {course.code}")
            
    # Mark first one as completed
    if Enrollment.objects.filter(user=empleado).exists():
        enr = Enrollment.objects.filter(user=empleado).first()
        enr.is_completed = True
        enr.save()
        print(f"Marked {enr.course.code} as completed for {empleado.username}")
        
except User.DoesNotExist:
    print("Empleado user not found")
