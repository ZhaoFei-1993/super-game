"""
公共处理方法
"""
from rest_framework.permissions import IsAuthenticated
from .exceptions import NotLoginException
from .code import API_403_ACCESS_DENY


class LoginRequired(IsAuthenticated):
    """
    接口访问要求登录公共处理
    """
    def has_permission(self, request, view):
        has_permission = super().has_permission(request, view)
        if has_permission is not True:
            raise NotLoginException(API_403_ACCESS_DENY)

        return has_permission
