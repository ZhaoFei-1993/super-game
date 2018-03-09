# -*- coding: UTF-8 -*-
from base.app import FormatListAPIView, FormatRetrieveAPIView, CreateAPIView
from base.function import LoginRequired
from base.app import ListAPIView, DestroyAPIView
from ...models import Category
from django.db.models import Q
from .serializers import ListSerialize
from base.exceptions import ResultNotFoundException
from users.models import User

from rest_framework_jwt.settings import api_settings


class CategoryView(ListAPIView):
    """
    竞猜分类
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        categorys = Category.objects.filter(parent_id=None)
        data = []
        for category in categorys:
            children = []
            categoryslist = Category.objects.filter(parent_id=category.id,is_delete=0).order_by("order")
            for categorylist in categoryslist:
                children.append({
                    "category_id": categorylist.id,
                    "category_name": categorylist.name,
                })
            data.append({
                "category_id": category.id,
                "category_name": category.name,
                "children": children
            })
        return self.response({'code': 0, 'data': data})