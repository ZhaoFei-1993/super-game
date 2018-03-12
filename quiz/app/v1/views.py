# -*- coding: UTF-8 -*-
from base.app import FormatListAPIView, FormatRetrieveAPIView, CreateAPIView
from base.function import LoginRequired
from base.app import ListAPIView, DestroyAPIView, ListCreateAPIView, RetrieveUpdateAPIView
from ...models import Category, Quiz, Record, Rule
from django.db.models import Q, Sum
from base.exceptions import ParamErrorException
from base import code as error_code
from datetime import datetime, timedelta
from .serializers import QuizSerialize, RecordSerialize, QuizDetailSerializer
import re
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




class RecordsListView(ListCreateAPIView):
    """
    竞猜记录
    """
    permission_classes = (LoginRequired,)
    serializer_class = RecordSerialize

    def get_queryset(self):
        if 'user_id' not in self.request.GET:
            user_id = self.request.user.id
        else:
            self.request.GET.get('user_id')
        return Record.objects.filter(user_id=user_id).order_by('created_at')


    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        Progress = results.data.get('results')
        data = []
        # quiz_id = ''
        tmp = ''
        time = ''
        host = ''
        guest = ''
        for fav in Progress:
            # record = fav.get('pk')
            # quiz = fav.get('quiz_id')
            pecific_date = fav.get('created_at')[0].get('year')
            pecific_time = fav.get('created_at')[0].get('time')
            host_team = fav.get('host_team')
            guest_team = fav.get('guest_team')
            if tmp == pecific_date and time == pecific_time and host == host_team and guest == guest_team:
                host_team = ""
                guest_team = ""
            else:
                host = host_team
                guest = guest_team

            if tmp == pecific_date and time == pecific_time:
                pecific_time = ""
            else:
                time = pecific_time

            if tmp == pecific_date:
                pecific_date = ""
            else:
                tmp = pecific_date

            # records = Record.objects.get(pk=record)
            # earn_coin = records.earn_coin
            # print("earn_coin=================", earn_coin)
            # if quiz_id==quiz:
            #     pass
            # else:
            #     quiz_id=quiz
            data.append({
                "quiz_id":fav.get('quiz_id'),
                'host_team': host_team,
                'guest_team': guest_team,
                'pecific_date': pecific_date,
                'pecific_time': pecific_time,
                'my_option': fav.get('my_option')[0].get('my_option'),
                'is_right': fav.get('my_option')[0].get('is_right'),
            })

        return self.response({'code': 0, 'data':data})


class QuizDetailView(ListAPIView):
    """
    竞猜详情
    """
    permission_classes = (LoginRequired,)
    serializer_class = QuizDetailSerializer

    def get_queryset(self):
        quiz_id = self.request.parser_context['kwargs']['quiz_id']
        quiz = Quiz.objects.filter(pk=quiz_id)
        return quiz

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        return self.response({'code': 0, 'items': items})


class QuizOptionView(ListAPIView):
    """
    竞猜选项列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = Q