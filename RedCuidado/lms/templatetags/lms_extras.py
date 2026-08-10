from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    try:
        group = Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        return False
    return group in user.groups.all()

@register.filter
def is_in(value, arg):
    """Checks if value is in a list/queryset"""
    if not arg: return False
    return value in arg

@register.filter
def completed_in_module(module, completed_ids):
    """Returns count of completed contents in a module"""
    if not completed_ids: return 0
    return module.contents.filter(id__in=completed_ids).count()
