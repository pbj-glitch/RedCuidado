from django import forms
from django.contrib.auth.models import User, Group
from .models import Course, Module, Content, UserProfile, WorkArea

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'code', 'description', 'image', 'image_url', 'assigned_work_areas', 'duration_days']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none transition-all'}),
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none transition-all'}),
            'code': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none transition-all'}),
            'image_url': forms.URLInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none transition-all'}),
            'assigned_work_areas': forms.CheckboxSelectMultiple(attrs={'class': 'space-y-2 mt-2'}),
            'duration_days': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none transition-all', 'min': '1', 'placeholder': 'Ej. 30'}),
        }

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none transition-all'}),
            'order': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none transition-all'}),
        }

class ContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['title', 'content_type', 'file', 'text_content', 'duration', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none transition-all'}),
            'content_type': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none transition-all'}),
            'text_content': forms.Textarea(attrs={'rows': 6, 'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none transition-all'}),
            'duration': forms.TextInput(attrs={'placeholder': "Ej: '5 min'", 'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none transition-all'}),
            'order': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none transition-all'}),
        }

class CollaboratorCreationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True, label="Nombre", widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none'}))
    last_name = forms.CharField(max_length=150, required=True, label="Apellido", widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none'}))
    password = forms.CharField(widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none', 'id': 'password-field'}), required=True, label="Contraseña")
    role = forms.ChoiceField(
        choices=[('Trabajador', 'Colaborador'), ('Profesor', 'Profesor'), ('Administrador', 'Administrador')],
        initial='Trabajador',
        label="Rol en la plataforma",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none'})
    )
    employee_id = forms.CharField(max_length=50, required=False, label="ID de Colaborador", widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none'}))
    work_area = forms.ModelChoiceField(queryset=WorkArea.objects.all(), required=False, label="Área de Trabajo", widget=forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none'}))
    headquarters = forms.ChoiceField(choices=UserProfile.HEADQUARTER_CHOICES, required=False, label="Sede", widget=forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-blue-500 outline-none'}),
        }
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            group_name = self.cleaned_data.get('role')
            if group_name:
                group, created = Group.objects.get_or_create(name=group_name)
                user.groups.add(group)
            
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.employee_id = self.cleaned_data.get('employee_id')
            profile.work_area = self.cleaned_data.get('work_area')
            profile.headquarters = self.cleaned_data.get('headquarters')
            profile.save()
            
        return user
