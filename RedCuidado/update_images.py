import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RedCuidado.settings')
django.setup()

from lms.models import Course

IMAGE_MAPPING = {
    'ELD 101': 'https://images.unsplash.com/photo-1708461859488-2a0c081ff826?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxlbGRlcmx5JTIwY2FyZSUyMHRyYWluaW5nJTIwbnVyc2V8ZW58MXx8fHwxNzczOTY0MTM2fDA&ixlib=rb-4.1.0&q=80&w=1080',
    'SAF 205': 'https://images.unsplash.com/photo-1758691462413-b07dee2933fe?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzZW5pb3IlMjBwYXRpZW50JTIwc2FmZXR5JTIwbWVkaWNhbHxlbnwxfHx8fDE3NzM5NjQxMzZ8MA&ixlib=rb-4.1.0&q=80&w=1080',
    'DEM 310': 'https://images.unsplash.com/photo-1738454738501-7e6626ccfcd2?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxkZW1lbnRpYSUyMGNhcmUlMjBlbGRlcmx5fGVufDF8fHx8MTc3Mzk2NDEzN3ww&ixlib=rb-4.1.0&q=80&w=1080'
}

for code, url in IMAGE_MAPPING.items():
    try:
        course = Course.objects.get(code=code)
        course.image_url = url
        course.save()
        print(f"Updated image URL for {code}")
    except Course.DoesNotExist:
        print(f"Course {code} not found, skipping...")

print("Done updating images.")
