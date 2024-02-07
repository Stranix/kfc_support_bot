from django import template

from src.models import CustomGroup

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    group = CustomGroup.objects.get(name=group_name)
    return True if group in user.groups.all() else False
