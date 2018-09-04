# -*- coding: UTF-8 -*-
"""
缓存统一处理类
"""
from django.core.cache import caches


def get_cache_type(cache_type='redis'):
    return caches[cache_type]


def set_cache(key, value, ttl=-1, cache_type='redis'):
    """
    设置缓存
    :param key:         键
    :param value:       值
    :param ttl:         过期时间，默认为-1，不过期
    :param cache_type:  缓存类型
    :return:
    """
    cache = get_cache_type(cache_type)

    if ttl == -1:
        cache.set(key, value)
        if cache_type == 'redis':
            cache.persist(key)
    else:
        cache.set(key, value, timeout=ttl)


def get_cache(key, cache_type='redis'):
    """
    通过键获取数值
    :param key:
    :param cache_type:  缓存类型
    :return:
    """
    cache = get_cache_type(cache_type)

    return cache.get(key)


def decr_cache(key, cache_type='redis'):
    """
    通过键获取数值-1
    :param key:
    :param cache_type:  缓存类型
    :return:
    """
    cache = get_cache_type(cache_type)

    return cache.decr(key)


def incr_cache(key, cache_type='redis'):
    """
    通过键获取数值 +1
    :param key:
    :param cache_type:  缓存类型
    :return:
    """
    cache = get_cache_type(cache_type)

    return cache.incr(key)


def delete_cache(key, cache_type='redis'):
    """
    删除数值
    :param key:
    :param cache_type:  缓存类型
    :return:
    """
    cache = get_cache_type(cache_type)

    cache.delete(key)

    return True


def check_key(key):
    """
    检查key值
    :param key:
    :return:
    """
    name = get_cache(key)
    if name is None or name == "":
        item = 0
    else:
        item = name
    return item


def get_keys(key, cache_type='redis'):
    cache = get_cache_type(cache_type)
    return cache.keys('*' + key + '*')
