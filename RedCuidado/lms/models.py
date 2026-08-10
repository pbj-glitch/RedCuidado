from django.db import models
from django.contrib.auth.models import User

# User Profile (Extending standard user with Employee ID)
class UserProfile(models.fields.related.OneToOneField):
    pass # Replaced below to avoid import error loop during draft, but actually we use models.OneToOneField

# Work Areas
class WorkArea(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Área de Trabajo")

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    HEADQUARTER_CHOICES = (
        ('Hualpen', 'Hualpén'),
        ('Coyhaique', 'Coyhaique'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="ID de Colaborador")
    work_area = models.ForeignKey(WorkArea, on_delete=models.SET_NULL, null=True, blank=True, related_name="employees", verbose_name="Área de Trabajo")
    headquarters = models.CharField(max_length=50, choices=HEADQUARTER_CHOICES, default='Hualpen', verbose_name="Sede")

    def __str__(self):
        return f"{self.user.username} - {self.employee_id or 'Sin ID'}"

# --------- COURSE STRUCTURE ---------

class Course(models.Model):
    title = models.CharField(max_length=200, verbose_name="Título del Curso")
    code = models.CharField(max_length=50, unique=True, verbose_name="Código (ej. ELD 101)")
    description = models.TextField(verbose_name="Descripción", blank=True)
    image = models.ImageField(upload_to='course_images/', blank=True, null=True, verbose_name="Imagen de Portada")
    image_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL de Imagen Externa")
    assigned_work_areas = models.ManyToManyField(WorkArea, blank=True, related_name="assigned_courses", verbose_name="Áreas de Trabajo Asignadas")
    duration_days = models.PositiveIntegerField(default=30, verbose_name="Plazo para completar (días)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.code}] {self.title}"

class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200, verbose_name="Título del Módulo")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.code} - {self.title}"

class Content(models.Model):
    CONTENT_TYPES = (
        ('video', 'Video'),
        ('pdf', 'PDF / Documento'),
        ('powerpoint', 'Presentación (PPT/PPTX)'),
        ('text', 'Texto / Lectura'),
    )
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=200, verbose_name="Título del Contenido")
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES, verbose_name="Tipo de Contenido")
    file = models.FileField(upload_to='course_content/', verbose_name="Archivo", blank=True, null=True)
    text_content = models.TextField(blank=True, null=True, verbose_name="Contenido de Texto")
    duration = models.CharField(max_length=50, blank=True, help_text="Ej: '5 min'")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.get_content_type_display()})"

# --------- ASSESSMENTS ---------

class Test(models.Model):
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='test', null=True, blank=True)
    title = models.CharField(max_length=200, default="Evaluación Final")
    passing_score = models.PositiveIntegerField(default=70, help_text="Porcentaje mínimo para aprobar")
    due_date = models.DateField(null=True, blank=True, verbose_name="Plazo de Entrega")

    def __str__(self):
        return f"Examen: {self.title} - {self.course.title}"

class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(verbose_name="Pregunta")

    def __str__(self):
        return self.text

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255, verbose_name="Respuesta")
    is_correct = models.BooleanField(default=False, verbose_name="Es correcta")

    def __str__(self):
        return self.text

# --------- USER PROGRESS ---------

class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_pinned = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user.username} -> {self.course.code}"

class ContentProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='content_progress')
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'content')

class TestResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_results')
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    score = models.FloatField(verbose_name="Puntaje (%)")
    passed = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.test.title} - {self.score}%"

# --------- ACTIVITY BOARD (TABLÓN) ---------

class BitacoraEntry(models.Model):
    ENTRY_TYPES = (
        ('observacion', 'Observación'),
        ('pendiente', 'Pendiente'),
        ('evaluacion', 'Evaluación'),
        ('incidente', 'Incidente'),
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bitacora_entries')
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES, verbose_name="Tipo de Registro")
    resident_name = models.CharField(max_length=150, blank=True, null=True, verbose_name="Residente (Opcional)")
    description = models.TextField(verbose_name="Descripción")
    incident_data = models.JSONField(blank=True, null=True, default=dict, verbose_name="Datos Adicionales del Incidente")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_entry_type_display()}] {self.author.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
