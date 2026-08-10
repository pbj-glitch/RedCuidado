from django.contrib.auth.models import User
try:
    u = User.objects.get(username='admin')
    u.is_superuser = True
    u.is_staff = True
    u.save()
    print("Admin user is now a superuser")
except User.DoesNotExist:
    pass
