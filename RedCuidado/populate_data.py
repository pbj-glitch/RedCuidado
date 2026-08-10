import os
import django
import random
from datetime import datetime, timedelta

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RedCuidado.settings')
django.setup()

from django.contrib.auth.models import User, Group
from lms.models import Course, Module, Content, Enrollment, Test, Question, Answer, TestResult, UserProfile, WorkArea

def populate_data():
    print("🚀 Iniciando repoblación de datos dinámicos...")
    
    # 1. Obtener Áreas de Trabajo REALES (ya deberían existir en el sistema)
    areas = list(WorkArea.objects.all())
    if not areas:
        # Fallback si no hay ninguna, pero el usuario dice que ya se dan de opción
        print("⚠️ No se encontraron áreas de trabajo. Asegúrate de que estén cargadas.")
        return

    # 2. Sedes Correctas
    sedes = ['Hualpen', 'Coyhaique']

    # 3. Crear Colaboradores (15 en total)
    nombres = ['Juan', 'María', 'Pedro', 'Ana', 'Luis', 'Carla', 'Diego', 'Elena', 'Roberto', 'Sonia', 'Miguel', 'Lucía', 'Gabriel', 'Rosa', 'Felipe']
    apellidos = ['Pérez', 'González', 'Soto', 'Muñoz', 'Rojas', 'Díaz', 'Morales', 'Silva', 'Sepúlveda', 'Castro', 'Tapia', 'Lara', 'Vidal', 'Ortiz', 'Garrido']
    
    colaborador_group, _ = Group.objects.get_or_create(name='Trabajador')
    
    users = []
    for i in range(15):
        username = f"user_{i+1}"
        first_name = nombres[i]
        last_name = apellidos[i]
        
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': f"{username}@redcuidado.cl"
            }
        )
        if created:
            user.set_password('demo123')
            user.save()
            user.groups.add(colaborador_group)
            
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.employee_id = f"COL-{1000 + i}"
            profile.headquarters = random.choice(sedes)
            profile.work_area = random.choice(areas)
            profile.save()
            print(f"✅ Usuario creado: {username}")
        users.append(user)


    # 4. Asegurar Tests y Preguntas para todos los cursos
    courses = Course.objects.all()
    for course in courses:
        test, created = Test.objects.get_or_create(
            course=course,
            defaults={
                'title': f'Evaluación: {course.title}', 
                'passing_score': 70
            }
        )
        if created:
            q = Question.objects.create(test=test, text="¿Es este un curso obligatorio?")
            Answer.objects.create(question=q, text="Sí", is_correct=True)
            Answer.objects.create(question=q, text="No", is_correct=False)
            print(f"📝 Test creado para: {course.code}")

    # 5. Generar Resultados y Completitudes (Aleatoriedad histórica)
    # Vamos a simular que algunos terminaron hace meses y otros hace poco
    base_date = datetime.now()
    
    for user in users:
        # Cada usuario se matricula en 2 a 4 cursos
        num_courses = random.randint(2, min(4, len(courses)))
        my_courses = random.sample(list(courses), num_courses)
        
        for course in my_courses:
            enr, _ = Enrollment.objects.get_or_create(user=user, course=course)
            
            # 80% de probabilidad de haber terminado el test
            if random.random() < 0.8:
                test = course.test
                # Fecha aleatoria en los últimos 5 meses
                days_ago = random.randint(0, 150)
                completion_date = base_date - timedelta(days=days_ago)
                
                score = random.randint(70, 100)
                # Crear resultado (Hackeamos la fecha de creación si es posible o asumimos actual)
                res = TestResult.objects.create(
                    user=user,
                    test=test,
                    score=score,
                    passed=True
                )
                # Forzar fecha para que el gráfico de meses se vea bien
                TestResult.objects.filter(id=res.id).update(attempted_at=completion_date)
                
                enr.is_completed = True
                enr.save()
                # También hackeamos la fecha de enrolamiento para reportes si fuera necesario
                Enrollment.objects.filter(id=enr.id).update(enrolled_at=completion_date)

    print("\n✨ ¡Datos poblados con éxito! El dashboard ahora debería mostrar curvas y barras reales.")

if __name__ == "__main__":
    populate_data()
