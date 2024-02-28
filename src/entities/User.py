import logging

from src.models import CustomUser

logger = logging.getLogger('support_bot')


class User:

    def __init__(self, user: CustomUser):
        self.user = user
