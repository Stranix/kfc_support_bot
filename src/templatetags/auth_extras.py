import logging

from django import template
from django.contrib.auth.models import Permission

from src.models import CustomGroup

logger = logging.getLogger('src')
register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    group = CustomGroup.objects.get(name=group_name)
    return True if group in user.groups.all() else False


@register.filter(name='has_right')
def has_right(user, right_name):
    try:
        user.user_permissions.get(codename=right_name)
        return True
    except Permission.DoesNotExist:
        return False
    except TypeError as e:
        logger.exception(e)
        return False
