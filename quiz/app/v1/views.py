# -*- coding: UTF-8 -*-
from base.app import FormatListAPIView, FormatRetrieveAPIView, CreateAPIView
from base.function import LoginRequired
from base.app import ListAPIView, DestroyAPIView, ListCreateAPIView
from ...models import Category, Quiz
from django.db.models import Q
from .serializers import QuizSerialize
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



class HotestView(ListAPIView):
    """
    热门比赛
    """
    permission_classes = (LoginRequired,)
    serializer_class = QuizSerialize

    def get_queryset(self):
        return Quiz.objects.filter(status=5, is_delete=False).order_by('-total_people')[:10]

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        return self.response({'code': 0, 'items': items})


class QuizListView(ListCreateAPIView):
    """
    获取竞猜列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = QuizSerialize

    def get_queryset(self):
        if 'category' not in self.request.GET:
            if 'is_end' not in self.request.GET:
                return Quiz.objects.filter(is_delete=False)
            else:
                return Quiz.objects.filter(is_delete=self.request.GET.get('is_end'))
        category_id = str(self.request.GET.get('category'))
        category_arr = category_id.split(',')
        if 'is_end' not in self.request.GET:
            return Quiz.objects.filter(is_delete=False, category=category_arr)
        else:
            return Quiz.objects.filter(is_delete=self.request.GET.get('is_end'),
                                           category__in=category_arr)







