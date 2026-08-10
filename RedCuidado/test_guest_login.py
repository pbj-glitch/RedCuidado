import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "RedCuidado.settings")
django.setup()

from django.test import RequestFactory
from lms.views import login_view
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import User

factory = RequestFactory()
request = factory.post('/login/', {'action': 'guest', 'guest_name': 'Tester'})

# Add session middleware
middleware = SessionMiddleware(lambda r: None)
middleware.process_request(request)
request.session.save()

# Execute view
response = login_view(request)
print("Response status:", response.status_code)

user = User.objects.filter(username='guest_tester').first()
print("Created User:", user.username if user else None)
if user:
    courses = user.enrollment_set.all()
    print("Enrolled in courses:", len(courses))
