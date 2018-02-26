# -*- coding: UTF-8 -*-
from base.app import FormatListAPIView, FormatRetrieveAPIView, CreateAPIView
from base.function import LoginRequired
from .serializers import ListSerialize, InfoSerialize
from base.exceptions import ResultNotFoundException
from ...models import User

from rest_framework_jwt.settings import api_settings


class ListView(FormatListAPIView):
    """
    返回用户列表
    """
    serializer_class = ListSerialize
    queryset = User.objects.all()


class InfoView(FormatRetrieveAPIView):
    """
    返回用户信息
    """
    permission_classes = (LoginRequired, )
    serializer_class = InfoSerialize

    def get_queryset(self):
        try:
            user = User.objects.get(pk=self.request.parser_context['kwargs']['pk'])
        except User.DoesNotExist:
            raise ResultNotFoundException(404)

        return User.objects.all()


class LoginView(CreateAPIView):
    """
    用户登录
    """
    def post(self, request, *args, **kwargs):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        user = User.objects.get(pk=1)
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        return self.response({
            'code': 0,
            'data': {
                'access_token': token,
            }
        })
