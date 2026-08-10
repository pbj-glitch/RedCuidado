import json
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max, Count, Avg, Sum, Q
from django.db.models.functions import TruncMonth
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from functools import wraps
from datetime import timedelta
from .models import Course, Module, Content, ContentProgress, Enrollment, TestResult, WorkArea, UserProfile, BitacoraEntry
from .forms import CourseForm, ModuleForm, ContentForm, CollaboratorCreationForm

def staff_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or request.user.groups.filter(name__in=['Administrador', 'Profesor']).exists():
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped_view

def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or request.user.groups.filter(name='Administrador').exists():
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped_view

def _setup_guest_courses(user):
    # Ensure guest has UserProfile
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    # Create or get Mock Courses
    c1, _ = Course.objects.get_or_create(
        title="Curso de Inducción RedCuidado",
        defaults={
            'description': "Curso de prueba para invitados. Presentación de los protocolos básicos.",
            'code': 'DEMO-101',
            'duration_days': 7
        }
    )
    
    c2, _ = Course.objects.get_or_create(
        title="Prevención de Caídas",
        defaults={
            'description': "Protocolos y herramientas para evitar caídas en residentes.",
            'code': 'DEMO-102',
            'duration_days': 7
        }
    )
    
    # Enroll user
    Enrollment.objects.get_or_create(user=user, course=c1)
    Enrollment.objects.get_or_create(user=user, course=c2)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    error = None
    if request.method == 'POST':
        action = request.POST.get('action', 'login')
        
        if action == 'guest':
            guest_name = request.POST.get('guest_name', '').strip()
            if guest_name:
                username = f"guest_{guest_name.lower().replace(' ', '_')}"
                # Limit username length to 150 chars max for django User model
                username = username[:150]
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={'first_name': guest_name[:30]}
                )
                if created:
                    user.set_unusable_password()
                    user.save()
                
                _setup_guest_courses(user)
                login(request, user)
                return redirect('home')
            else:
                error = "Debe ingresar un nombre para entrar como invitado."
                
        else:
            u = request.POST.get('username')
            p = request.POST.get('password')
            user = authenticate(request, username=u, password=p)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                error = "Usuario o contraseña incorrectos."
            
    return render(request, 'lms/login.html', {'error': error})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def activity_board_view(request):
    """Renderiza la vista del Tablón de Actividad y procesa nuevas entradas de bitácora."""
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'incidente':
            # Collect Incident Data
            incident_category = request.POST.get('incident_category', 'caida')
            resident_name = request.POST.get('incident_resident', '')
            description = request.POST.get('incident_description', '')
            glasgow = request.POST.get('glasgow', '')
            signos_vitales = request.POST.getlist('signos_vitales')
            
            # Category specific data
            incident_data = {
                'category': incident_category,
                'glasgow': glasgow,
                'signos_vitales': signos_vitales,
                'specific_details': {}
            }
            
            if incident_category == 'caida':
                incident_data['specific_details']['zonas_afectadas'] = request.POST.getlist('zonas')
            elif incident_category == 'medicacion':
                incident_data['specific_details']['farmaco'] = request.POST.get('farmaco_nombre', '')
                incident_data['specific_details']['tipo_error'] = request.POST.get('tipo_error', '')
                incident_data['specific_details']['administrado'] = request.POST.get('admin_paciente', '')
            elif incident_category == 'deterioro':
                incident_data['specific_details']['sintomas'] = request.POST.getlist('sintomas')

            BitacoraEntry.objects.create(
                author=request.user,
                entry_type='incidente',
                resident_name=resident_name,
                description=description,
                incident_data=incident_data
            )
        else:
            # Normal Bitácora Entry
            entry_type = request.POST.get('entry_type')
            resident_name = request.POST.get('resident_name', '')
            description = request.POST.get('description', '')
            
            if entry_type and description:
                BitacoraEntry.objects.create(
                    author=request.user,
                    entry_type=entry_type,
                    resident_name=resident_name,
                    description=description
                )
        return redirect('activity_board')

    entries = BitacoraEntry.objects.all()[:20]  # Últimas 20 entradas
    return render(request, 'lms/activity.html', {'active_menu': 'activity', 'entries': entries})

@login_required
def delete_bitacora_entry(request, entry_id):
    if not (request.user.is_staff or request.user.is_superuser or request.user.username == 'admin'):
        return redirect('activity_board')
    entry = get_object_or_404(BitacoraEntry, id=entry_id)
    if request.method == 'POST':
        entry.delete()
    return redirect('activity_board')


@login_required
def learning_paths_view(request):
    """Renderiza la vista estática (mockup) de Rutas de Aprendizaje."""
    return render(request, 'lms/paths.html', {'active_menu': 'paths'})

@login_required
def home_view(request):
    from django.db.models import Q
    user = request.user
    
    # Admins and Profs see all courses
    if user.is_superuser or user.groups.filter(name__in=['Administrador', 'Profesor']).exists():
        courses = Course.objects.all()
    else:
        # Standard user sees courses assigned to their area OR courses with no area assigned (common courses)
        if hasattr(user, 'profile') and user.profile.work_area:
            courses = Course.objects.filter(
                Q(assigned_work_areas=user.profile.work_area) | 
                Q(assigned_work_areas__isnull=True)
            ).distinct()
        else:
            # User has no area assigned, only sees common courses
            courses = Course.objects.filter(assigned_work_areas__isnull=True)

    # Progress math for home
    course_list = []
    for course in courses:
        enr = Enrollment.objects.filter(user=user, course=course).first()
        is_pinned = enr.is_pinned if enr else False
        
        modules_count = Module.objects.filter(course=course).count()
        total_content = Content.objects.filter(module__course=course).count()
        if total_content > 0:
            completed_content = ContentProgress.objects.filter(user=user, content__module__course=course, is_completed=True).count()
            progress = int((completed_content / total_content) * 100)
        else:
            progress = 0
            
        course_list.append({
            'course': course,
            'progress': progress,
            'modules_count': modules_count,
            'is_pinned': is_pinned
        })

    # Sort by is_pinned (True first)
    course_list.sort(key=lambda x: x['is_pinned'], reverse=True)

    # Estadísticas para el Sidebar de Administrador
    admin_stats = None
    if user.is_superuser or user.groups.filter(name='Administrador').exists():
        from django.utils import timezone
        now = timezone.now()
        admin_stats = {
            'total_users': User.objects.count(),
            'total_courses': Course.objects.count(),
            'certificates_month': Enrollment.objects.filter(is_completed=True, enrolled_at__month=now.month, enrolled_at__year=now.year).count(),
            'total_certificates': Enrollment.objects.filter(is_completed=True).count(),
        }

    context = {
        'courses': course_list,
        'active_menu': 'homepage',
        'admin_stats': admin_stats,
    }
    return render(request, 'lms/home.html', context)

@login_required
def course_detail_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    modules = course.modules.all().prefetch_related('contents')
    
    # Progress math
    total_content = Content.objects.filter(module__course=course).count()
    completed_content = ContentProgress.objects.filter(user=request.user, content__module__course=course, is_completed=True).count()
    progress_percentage = int((completed_content / total_content * 100)) if total_content > 0 else 0
    
    test_available = (total_content > 0 and completed_content == total_content) or (total_content == 0)
    
    # Check if they have a test passed
    test_passed = False
    test_score = 0
    if hasattr(course, 'test'):
        from .models import TestResult
        last_result = TestResult.objects.filter(user=request.user, test=course.test).order_by('-attempted_at').first()
        if last_result and last_result.passed:
            test_passed = True
            test_score = last_result.score
    
    # Get completed content IDs for this user
    completed_ids = list(ContentProgress.objects.filter(
        user=request.user, 
        content__module__course=course, 
        is_completed=True
    ).values_list('content_id', flat=True))

    context = {
        'course': course,
        'modules': modules,
        'progress_percentage': progress_percentage,
        'test_available': test_available,
        'test_passed': test_passed,
        'test_score': test_score,
        'active_menu': 'courses',
        'completed_ids': completed_ids,
    }
    return render(request, 'lms/course_detail.html', context)

@login_required
def reports_view(request):
    if not request.user.groups.filter(name__in=['Administrador', 'Profesor']).exists():
        raise PermissionDenied("No tienes permisos para ver esta página.")
        
    area_id = request.GET.get('area')
    hq = request.GET.get('headquarters')
    
    # Querysets base para métricas
    profiles = UserProfile.objects.filter(user__is_active=True)
    all_enrollments = Enrollment.objects.all()
    results = TestResult.objects.all()
    
    if area_id:
        profiles = profiles.filter(work_area_id=area_id)
        all_enrollments = all_enrollments.filter(user__profile__work_area_id=area_id)
        results = results.filter(user__profile__work_area_id=area_id)
    if hq:
        profiles = profiles.filter(headquarters=hq)
        all_enrollments = all_enrollments.filter(user__profile__headquarters=hq)
        results = results.filter(user__profile__headquarters=hq)

    # Métricas Principales
    total_collaborators = profiles.count()
    enrollments = all_enrollments.filter(is_completed=True)
    total_completions = enrollments.count()
    total_courses = Course.objects.count()
    total_enrollments = all_enrollments.count()
    completion_rate = (total_completions / total_enrollments * 100) if total_enrollments else 0
    avg_score = results.aggregate(Avg('score'))['score__avg'] or 0
    
    # 1. Completitud por Área (Gráfico de Barras)
    # Solo tomamos áreas que tengan colaboradores
    area_stats = WorkArea.objects.annotate(
        completions=Count('employees__user__enrollments', filter=Q(employees__user__enrollments__is_completed=True))
    ).filter(employees__isnull=False).distinct().values('name', 'completions')
    
    # 2. Evolución Mensual (Gráfico de Líneas - Últimos 6 meses)
    monthly_stats = enrollments.annotate(month=TruncMonth('enrolled_at')).values('month').annotate(count=Count('id')).order_by('month')
    
    # Convertimos los meses a strings para JSON
    monthly_data = []
    for entry in monthly_stats:
        if entry['month']:
            monthly_data.append({
                'month': entry['month'].strftime('%b %Y'),
                'count': entry['count']
            })

    # 3. Cursos Populares (Gráfico de barras horizontal)
    popular_courses = Course.objects.annotate(
        enrollment_count=Count('enrollments')
    ).order_by('-enrollment_count')[:5].values('title', 'enrollment_count')

    context = {
        'active_menu': 'reports',
        'work_areas': WorkArea.objects.all(),
        'headquarters': [('Hualpen', 'Hualpén'), ('Coyhaique', 'Coyhaique')],
        'selected_area': area_id,
        'selected_hq': hq,
        'total_collaborators': total_collaborators,
        'total_completions': total_completions,
        'total_courses': total_courses,
        'completion_rate': round(completion_rate, 1),
        'avg_score': round(avg_score, 1),
        'area_stats': list(area_stats),
        'monthly_data': monthly_data,
        'popular_courses': list(popular_courses),
    }
    return render(request, 'lms/reports_dashboard.html', context)

@login_required
def groups_view(request):
    
    area_id = request.GET.get('area')
    hq = request.GET.get('headquarters')
    
    users = User.objects.select_related('profile__work_area').prefetch_related('enrollments__course').all()
    
    if area_id:
        users = users.filter(profile__work_area_id=area_id)
    if hq:
        users = users.filter(profile__headquarters=hq)
        
    work_areas = WorkArea.objects.all()
    headquarters = [('Hualpen', 'Hualpén'), ('Coyhaique', 'Coyhaique')]
    
    context = {
        'users': users,
        'work_areas': work_areas,
        'headquarters': headquarters,
        'selected_area': area_id,
        'selected_hq': hq,
        'active_menu': 'groups',
    }
    return render(request, 'lms/groups.html', context)

@login_required
def calendar_view(request):
    user = request.user
    events = []
    
    # 1. Fechas de Inicio (Inscripciones)
    enrollments = Enrollment.objects.filter(user=user).select_related('course')
    for enr in enrollments:
        events.append({
            'title': f"Inicio: {enr.course.title}",
            'start': enr.enrolled_at.date().isoformat(),
            'backgroundColor': 'rgba(59, 130, 246, 0.1)',
            'borderColor': '#3b82f6',
            'textColor': '#1e40af',
            'allDay': True
        })
        
        # 2. Plazos (Calculado desde inscripción + duración del curso)
        if enr.course.duration_days:
            due_date = enr.enrolled_at + timedelta(days=enr.course.duration_days)
            events.append({
                'title': f"PLAZO: {enr.course.title}",
                'start': due_date.date().isoformat(),
                'backgroundColor': 'rgba(239, 68, 68, 0.1)',
                'borderColor': '#ef4444',
                'textColor': '#991b1b',
                'allDay': True
            })
            
    context = {
        'active_menu': 'calendar',
        'events_list': events,
        'events_json': json.dumps(events), 
        'enrolled_courses': [enr.course for enr in enrollments]
    }
    return render(request, 'lms/calendar.html', context)

# --------- COURSE MANAGEMENT ---------

@staff_required
def course_create_view(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save()
            return redirect('course_manage', course_id=course.id)
    else:
        form = CourseForm()
    return render(request, 'lms/course_form.html', {'form': form, 'title': 'Crear Nuevo Curso'})

@staff_required
def course_edit_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            return redirect('course_manage', course_id=course.id)
    else:
        form = CourseForm(instance=course)
    return render(request, 'lms/course_form.html', {'form': form, 'title': f'Editar {course.title}'})

@staff_required
def course_delete_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        course.delete()
        return redirect('home')
    return render(request, 'lms/course_confirm_delete.html', {'course': course})

@staff_required
def course_manage_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    modules = course.modules.all().prefetch_related('contents')
    context = {
        'course': course,
        'modules': modules,
        'active_menu': 'courses',
    }
    return render(request, 'lms/course_manage.html', context)

@staff_required
def module_create_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = ModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            # Set order to max + 1
            max_order = course.modules.aggregate(Max('order'))['order__max'] or 0
            module.order = max_order + 1
            module.save()
            return redirect('course_manage', course_id=course.id)
    else:
        form = ModuleForm()
    return render(request, 'lms/module_form.html', {'form': form, 'course': course, 'title': 'Añadir Módulo'})

@staff_required
def module_edit_view(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    if request.method == 'POST':
        form = ModuleForm(request.POST, instance=module)
        if form.is_valid():
            form.save()
            return redirect('course_manage', course_id=module.course.id)
    else:
        form = ModuleForm(instance=module)
    return render(request, 'lms/module_form.html', {'form': form, 'course': module.course, 'title': 'Editar Módulo'})

@staff_required
def content_create_view(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    if request.method == 'POST':
        form = ContentForm(request.POST, request.FILES)
        if form.is_valid():
            content = form.save(commit=False)
            content.module = module
            # Set order to max + 1
            max_order = module.contents.aggregate(Max('order'))['order__max'] or 0
            content.order = max_order + 1
            content.save()
            return redirect('course_manage', course_id=module.course.id)
    else:
        form = ContentForm()
    return render(request, 'lms/content_form.html', {'form': form, 'module': module, 'title': 'Añadir Sección'})

@staff_required
def content_edit_view(request, content_id):
    content = get_object_or_404(Content, id=content_id)
    if request.method == 'POST':
        form = ContentForm(request.POST, request.FILES, instance=content)
        if form.is_valid():
            form.save()
            return redirect('course_manage', course_id=content.module.course.id)
    else:
        form = ContentForm(instance=content)
    return render(request, 'lms/content_form.html', {'form': form, 'module': content.module, 'title': 'Editar Sección'})

import json
from django.db import transaction
from .models import Test, Question, Answer

@staff_required
@require_POST
def reorder_modules(request, course_id):
    order_ids = request.POST.getlist('order[]')
    for i, mid in enumerate(order_ids):
        Module.objects.filter(id=mid, course_id=course_id).update(order=i)
    return JsonResponse({'status': 'ok'})

@staff_required
@require_POST
def reorder_contents(request, module_id):
    order_ids = request.POST.getlist('order[]')
    for i, cid in enumerate(order_ids):
        # Update both order and module_id to support cross-module dragging
        Content.objects.filter(id=cid).update(order=i, module_id=module_id)
    return JsonResponse({'status': 'ok'})

@staff_required
@require_POST
def module_delete_view(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    course_id = module.course.id
    module.delete()
    return redirect('course_manage', course_id=course_id)

@staff_required
@require_POST
def content_delete_view(request, content_id):
    content = get_object_or_404(Content, id=content_id)
    course_id = content.module.course.id
    content.delete()
    return redirect('course_manage', course_id=course_id)

@staff_required
def test_builder_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            with transaction.atomic():
                test, _ = Test.objects.get_or_create(course=course)
                test.title = data.get('title', 'Evaluación Final')
                test.passing_score = int(data.get('passing_score', 60))
                test.save()
                
                # Resync questions
                test.questions.all().delete() # Clear old ones
                for q_data in data.get('questions', []):
                    question = Question.objects.create(test=test, text=q_data.get('text', ''))
                    for a_data in q_data.get('answers', []):
                        Answer.objects.create(
                            question=question,
                            text=a_data.get('text', ''),
                            is_correct=bool(a_data.get('is_correct', False))
                        )
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    # GET: Prepare data for frontend
    test = getattr(course, 'test', None)
    context = {
        'course': course,
        'test': test,
        'active_menu': 'lms'
    }
    return render(request, 'lms/test_builder.html', context)

@login_required
def learning_view(request, course_id, content_id=None):
    course = get_object_or_404(Course, id=course_id)
    modules = course.modules.all().prefetch_related('contents').order_by('order')
    
    # Flatten all content items for navigation
    all_content = []
    for m in modules:
        for c in m.contents.all().order_by('order'):
            all_content.append(c)
            
    if not all_content:
        return redirect('course_detail', course_id=course.id)
        
    if content_id:
        current_content = get_object_or_404(Content, id=content_id)
    else:
        current_content = all_content[0]
        
    # Mark as completed
    ContentProgress.objects.get_or_create(user=request.user, content=current_content, defaults={'is_completed': True})
    
    # Get all completed content IDs for this course
    completed_ids = ContentProgress.objects.filter(
        user=request.user, 
        content__module__course=course, 
        is_completed=True
    ).values_list('content_id', flat=True)
    
    # Navigation
    current_index = -1
    for i, c in enumerate(all_content):
        if c.id == current_content.id:
            current_index = i
            break
            
    prev_content = all_content[current_index - 1] if current_index > 0 else None
    next_content = all_content[current_index + 1] if current_index < len(all_content) - 1 else None
    
    context = {
        'course': course,
        'modules': modules,
        'current_content': current_content,
        'prev_content': prev_content,
        'next_content': next_content,
        'completed_ids': completed_ids,
        'active_menu': 'courses',
    }
    return render(request, 'lms/learning.html', context)

@login_required
def take_test_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    test = getattr(course, 'test', None)
    
    if not test:
        return redirect('course_detail', course_id=course.id)
        
    # Check completion
    total_content = Content.objects.filter(module__course=course).count()
    completed_content = ContentProgress.objects.filter(user=request.user, content__module__course=course, is_completed=True).count()
    
    if total_content > 0 and completed_content < total_content:
        # User hasn't finished the course
        return redirect('course_detail', course_id=course.id)

    if request.method == 'POST':
        questions = test.questions.all()
        correct_count = 0
        total_questions = questions.count()
        wrong_questions = []

        if total_questions == 0:
            return redirect('course_detail', course_id=course.id)

        for q in questions:
            selected_answer_id = request.POST.get(f'question_{q.id}')
            if selected_answer_id:
                try:
                    answer = Answer.objects.get(id=selected_answer_id, question=q)
                    if answer.is_correct:
                        correct_count += 1
                    else:
                        wrong_questions.append(q.text)
                except Answer.DoesNotExist:
                    wrong_questions.append(q.text)
            else:
                wrong_questions.append(q.text)

        score = round((correct_count / total_questions) * 100, 1)
        passed = score >= test.passing_score

        # Save result
        TestResult.objects.create(
            user=request.user,
            test=test,
            score=score,
            passed=passed
        )

        if passed:
            Enrollment.objects.update_or_create(
                user=request.user,
                course=course,
                defaults={'is_completed': True}
            )
            request.session[f'wrong_answers_{course.id}'] = wrong_questions
            return redirect('test_result', course_id=course.id)
        else:
            # FAIL PENALTY: WIPE PROGRESS
            ContentProgress.objects.filter(user=request.user, content__module__course=course).delete()
            request.session[f'test_failed_{course.id}'] = True
            return redirect('test_result', course_id=course.id)

    context = {
        'course': course,
        'test': test,
        'questions': test.questions.prefetch_related('answers').all(),
        'active_menu': 'courses'
    }
    return render(request, 'lms/test_take.html', context)

@login_required
def test_result_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    test = getattr(course, 'test', None)
    
    wrong_answers = request.session.pop(f'wrong_answers_{course.id}', [])
    failed = request.session.pop(f'test_failed_{course.id}', False)

    result = TestResult.objects.filter(user=request.user, test=test).order_by('-attempted_at').first()

    context = {
        'course': course,
        'test': test,
        'result': result,
        'failed': failed,
        'wrong_answers': wrong_answers,
        'active_menu': 'courses'
    }
    return render(request, 'lms/test_result.html', context)

@login_required
def profile_view(request):
    user = request.user
    
    # Get completed courses
    completed_enrollments = Enrollment.objects.filter(user=user, is_completed=True).select_related('course')
    
    # Get available courses
    from django.db.models import Q
    if hasattr(user, 'profile') and user.profile.work_area:
        all_courses = Course.objects.filter(
            Q(assigned_work_areas=user.profile.work_area) | Q(assigned_work_areas__isnull=True)
        ).distinct()
    else:
        all_courses = Course.objects.filter(assigned_work_areas__isnull=True)
        
    completed_course_ids = completed_enrollments.values_list('course_id', flat=True)
    available_courses_qs = all_courses.exclude(id__in=completed_course_ids)
    
    # Calculate progress for available courses
    available_courses = []
    for course in available_courses_qs:
        total_content = Content.objects.filter(module__course=course).count()
        if total_content > 0:
            completed_content = ContentProgress.objects.filter(user=user, content__module__course=course, is_completed=True).count()
            progress = int((completed_content / total_content) * 100)
        else:
            progress = 0
            
        available_courses.append({
            'course': course,
            'progress': progress
        })

    context = {
        'completed_enrollments': completed_enrollments,
        'available_courses': available_courses,
        'active_menu': 'profile'
    }
    return render(request, 'lms/profile.html', context)

@login_required
def certificate_view(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, user=request.user, is_completed=True)
    context = {
        'enrollment': enrollment,
        'date': enrollment.enrolled_at, # Alternatively, could be a completion date if model had it. Using enrolled_at or today is fine. 
        # Using timezone.now() for the seal
    }
    return render(request, 'lms/certificate.html', context)

@admin_required
def collaborator_create_view(request):
    if request.method == 'POST':
        form = CollaboratorCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('groups')
    else:
        form = CollaboratorCreationForm()
        
    return render(request, 'lms/collaborator_form.html', {'form': form})

@login_required
@require_POST
def toggle_pin_view(request, course_id):
    enrollment, created = Enrollment.objects.get_or_create(user=request.user, course_id=course_id)
    enrollment.is_pinned = not enrollment.is_pinned
    enrollment.save()
    return JsonResponse({'is_pinned': enrollment.is_pinned})
