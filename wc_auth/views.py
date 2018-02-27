# -*- coding: UTF-8 -*-
from base.backend import CreateAPIView

from .serializers import InfoSerialize


class LoginView(CreateAPIView):
    serializer_class = InfoSerialize

    def post(self, request, *args, **kwargs):
        """
        管理员登录
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        return self.response({
            'code': 0
        })
