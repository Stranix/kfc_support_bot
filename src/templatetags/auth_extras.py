from django import template
from django.contrib.auth.models import Permission

from src.models import CustomGroup

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    group = CustomGroup.objects.get(name=group_name)
    return True if group in user.groups.all() else False


@register.filter(name='has_right')
def has_right(user, right_name):
    employee_permissions = Permission.objects.filter(user=user)
    if employee_permissions.filter(codename=right_name).exists():
        return True
    return False
