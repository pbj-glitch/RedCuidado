from django.contrib.auth.models import User
from lms.models import WorkArea

areas = ["Enfermería", "Administración", "Fisioterapia"]
for a in areas:
    WorkArea.objects.get_or_create(name=a)

for u in User.objects.all():
    profile = u.profile
    if u.username == 'empleado':
        profile.work_area = WorkArea.objects.get(name="Enfermería")
        profile.save()
    elif u.username == 'admin':
        profile.work_area = WorkArea.objects.get(name="Administración")
        profile.save()
    elif u.username == 'profesor':
        profile.work_area = WorkArea.objects.get(name="Administración")
        profile.save()
        
print("Assigned work areas")
