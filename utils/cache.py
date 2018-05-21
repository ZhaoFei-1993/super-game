# -*- coding: UTF-8 -*-
"""
缓存统一处理类
"""
from django.core.cache import caches


cache = caches['redis']


def set_cache(key, value, ttl=-1):
    """
    设置缓存
    :param key:     键
    :param value:   值
    :param ttl:     过期时间，默认为-1，不过期
    :return:
    """
    if ttl == -1:
        cache.set(key, value)
        cache.persist(key)
    else:
        cache.set(key, value, timeout=ttl)


def get_cache(key):
    """
    通过键获取数值
    :param key:
    :return:
    """
    return cache.get(key)


def delete_cache(key):
    """
    删除数值
    :param key:
    :return:
    """
    return cache.delete(key)

