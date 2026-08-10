import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "RedCuidado.settings")
django.setup()

from django.contrib.auth.models import User
from lms.models import BitacoraEntry

user = User.objects.first()
if not user:
    user = User.objects.create(username="testuser")

entry = BitacoraEntry.objects.create(
    author=user,
    entry_type='incidente',
    resident_name='Test Resident',
    description='Test Description',
    incident_data={'category': 'caida'}
)
print("Created entry:", entry.id)
