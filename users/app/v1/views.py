# -*- coding: UTF-8 -*-
from base.app import FormatListAPIView, FormatRetrieveAPIView
from .serializers import ListSerialize, InfoSerialize
from base.exceptions import ResultNotFoundException
from ...models import User


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
    serializer_class = InfoSerialize

    def get_queryset(self):
        try:
            user = User.objects.get(pk=self.request.parser_context['kwargs']['pk'])
        except User.DoesNotExist:
            raise ResultNotFoundException(404)

        return User.objects.all()
