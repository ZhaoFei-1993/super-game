from django.db import models
from utils.cache import get_cache, set_cache


class BaseManager(models.Manager):
    """
    基数数据操作类
    """
    key = None
    order_by = None
    cache_type = 'redis'

    def get_all(self):
        """
        获取所有记录
        :return:
        """
        items = get_cache(self.key, cache_type=self.cache_type)
        if items is None:
            items = self.all()
            if self.order_by is not None:
                items.order_by(self.order_by)
            set_cache(self.key, items, ttl=-1, cache_type=self.cache_type)

        return items

    def get_one(self, *args, **kwargs):
        """
        获取一条记录
        :param args:
        :param kwargs
        :return:
        """
        items = self.get_all()

        if len(items) == 0:
            return None

        pk = kwargs['pk']
        result = None
        for item in items:
            if item.id != pk:
                continue
            result = item

        return result
