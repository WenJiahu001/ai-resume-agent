"""Service 基类"""

from config import get_settings


class BaseService:
    def __init__(self):
        self.settings = get_settings()

    def _get_connection(self):
        return self.settings.db.get_connection(use_dict_cursor=True)
