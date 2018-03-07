# -*- coding: UTF-8 -*-
from rest_framework.exceptions import APIException
from rest_framework import status
import re

from . import code as error_code


class ValidateException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST


class PhoneValidator(object):
    """
    自定义数据验证类 - 手机号码验证
    """
    message = '手机号码格式错误'
    expression = r'^(13[0-9]|14[5|7]|15[0|1|2|3|5|6|7|8|9]|18[0|1|2|3|5|6|7|8|9])\d{8}$'

    def __init__(self, field, message=None):
        self.field = field
        self.message = message or self.message

    def __call__(self, value):
        is_valid = re.match(self.expression, value.get('telephone'))
        if is_valid is None:
            raise ValidateException({
                'code': error_code.API_20101_TELEPHONE_ERROR
            })
