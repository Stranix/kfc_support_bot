import logging

from asgiref.sync import sync_to_async

from django.contrib.auth.models import Permission

from src.models import CustomUser

logger = logging.getLogger('support_bot')


class User:

    def __init__(self, user: CustomUser):
        self.user = user

    @sync_to_async
    def has_perm(self, perm_codename: str) -> bool:
        if self._has_perm_in_group(perm_codename):
            return True
        logger.debug('Ищем права у пользователя')
        employee_permissions = Permission.objects.filter(user=self.user)
        if employee_permissions.filter(codename=perm_codename).exists():
            logger.debug('У пользователя есть право на синхронизацию')
            return True
        return False

    def _has_perm_in_group(self, perm_codename: str) -> bool:
        for group in self.user.groups.all():
            perm_exists = group.permissions.filter(
                codename=perm_codename).exists()
            if perm_exists:
                logger.debug('Нашел право %s в группе %s', perm_codename,
                             group)
                return True
        logger.debug('Нет права %s в группах пользователя', perm_codename)
        return False
