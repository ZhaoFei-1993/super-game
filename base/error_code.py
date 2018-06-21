# -*- coding: UTF-8 -*-
"""
错误码
"""
from base import code
from base import code_en


def get_code(request):
    """
    获取错误码
    :return:
    """
    language = request.GET.get('language')

    error_code = code
    if language == 'en':
        error_code = code_en

    return error_code
