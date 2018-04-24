# -*- coding: UTF-8 -*-
"""
公共处理方法
"""
from random import Random
from urllib.parse import quote_plus

from rest_framework.permissions import IsAuthenticated
from .exceptions import NotLoginException
from .code import API_403_ACCESS_DENY
import random  


class LoginRequired(IsAuthenticated):
    """
    接口访问要求登录公共处理
    """
    def has_permission(self, request, view):
        has_permission = super().has_permission(request, view)
        if has_permission is not True:
            raise NotLoginException(API_403_ACCESS_DENY)

        return has_permission


def random_string(length=16):
    """
    生成指定长度随机字符串
    :param length:
    :return:
    """
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    char_length = len(chars) - 1
    random = Random()

    random_str = ''
    for i in range(length):
        random_str += chars[random.randint(0, char_length)]
    return random_str


def sort_object(dict_list):
    """
    字典根据key排序
    :param dict_list:
    :return:
    """
    item_keys = sorted(dict_list.keys())
    new_dict = {}
    for key in item_keys:
        new_dict[key] = dict_list[key]

    return new_dict


def urlencode(string):
    """
    just like php urlencode
    :param string:
    :return:
    """
    string = string.replace(' ', '_is_space_')
    string = quote_plus(string)
    string = string.replace('_is_space_', '%20')

    return string


def randomnickname():
    xing = '赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐'
    ming = '一二三四五六七八九十'
    X = random.choice(xing)
    M = "".join(random.choice(ming) for i in range(2))
    return X+M
