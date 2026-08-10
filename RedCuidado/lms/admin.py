from django.contrib import admin
from .models import UserProfile, Course, Module, Content, Test, Question, Answer, Enrollment, ContentProgress, TestResult, WorkArea

@admin.register(WorkArea)
class WorkAreaAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'work_area')

class ContentInline(admin.TabularInline):
    model = Content
    extra = 1

class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'created_at')
    inlines = [ModuleInline]

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    inlines = [ContentInline]

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 3

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'test')
    inlines = [AnswerInline]

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'passing_score')
    inlines = [QuestionInline]

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'enrolled_at', 'is_completed')

@admin.register(ContentProgress)
class ContentProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'is_completed', 'completed_at')

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'score', 'passed', 'attempted_at')
