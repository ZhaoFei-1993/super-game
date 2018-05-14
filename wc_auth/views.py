# -*- coding: UTF-8 -*-
import rest_framework_filters as filters
from base.backend import CreateAPIView, FormatListAPIView, FormatRetrieveAPIView, ListAPIView

from .serializers import InfoSerialize, RoleListSerialize, QuizSerialize, AdminOperationSerialize
from .models import Role, Admin
from config.models import Admin_Operation
from quiz.models import Quiz
from url_filter.integrations.drf import DjangoFilterBackend
from utils.functions import reversion_Decorator


class LoginView(CreateAPIView):
    """
    管理员登录
    """
    serializer_class = InfoSerialize

    def post(self, request, *args, **kwargs):
        return self.response({
            'code': 0
        })


class RoleFilter(filters.FilterSet):
    """
    角色列表筛选
    """

    class Meta:
        model = Role
        fields = {
            "name": ['contains']
        }


class RoleListView(FormatListAPIView):
    """
    管理员角色列表
    """
    serializer_class = RoleListSerialize
    filter_class = RoleFilter

    def get_queryset(self):
        id = self.request.GET.get('id')
        if id is not None:
            return Role.objects.filter(pk=id)

        return Role.objects.all()


class InfoView(FormatRetrieveAPIView):
    """
    管理员信息
    """
    serializer_class = InfoSerialize
    queryset = Admin.objects.all()

    def get(self, request, *args, **kwargs):
        return self.response({
            "username": "admin",
            "truename": "Serati Ma",
            "email": "rexlin0624@gmail.com",
            "role": "超级管理员",
            "role_id": "1",
        })


class QuizFilter(filters.FilterSet):
    """
    竞猜列表筛选
    """

    class Meta:
        model = Quiz
        fields = {
            "host_team": ['contains'],
            "guest_team": ['contains'],
            "status": ['contains'],
            "match_name": ['contains']
        }


class QuizView(FormatListAPIView):
    """
    竞猜表
    """
    serializer_class = QuizSerialize
    filter_class = QuizFilter
    queryset = Quiz.objects.all()


class AdminOperationView(ListAPIView):
    """
    管理员操作记录
    """
    serializer_class = AdminOperationSerialize
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['admin', 'pre_version', 'mod_version', 'revision']

    def get_queryset(self):
        admin_id = self.request.user.id
        query_s = Admin_Operation.objects.filter(admin_id=admin_id).order_by('revision')
        return query_s
