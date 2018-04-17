# -*- coding: UTF-8 -*-
from base.backend import FormatListAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView, ListCreateAPIView
from .serializers import CategorySerializer
from ..models import Category, Quiz, Option
from django.db import connection
from api.settings import REST_FRAMEWORK
from django.db import transaction

from mptt.utils import get_cached_trees
from rest_framework import status
from utils.functions import convert_localtime
from rest_framework.reverse import reverse
from django.http import HttpResponse
import json


class RecurseTreeNode(object):
    """
    递归获取分类树
    返回格式如：
    [
        {label: "时事", value: "时事", key: 3, children: [{label: "俄罗斯", value: "俄罗斯", key: 4}]}
    ]
    """

    def _node(self, node):
        bits = []
        context = {}
        for child in node.get_children():
            bits.append(self._node(child))
        context['label'] = node.name
        context['value'] = node.name
        context['key'] = node.id
        context['icon'] = node.icon
        if len(bits) > 0:
            context['children'] = bits
        return context

    def tree(self, parent_id=None):
        print("parent_id=================================", parent_id)
        if parent_id == '' or parent_id == None:
            print("none======================")
            roots = get_cached_trees(Category.objects.filter(is_delete=False))
            bits = [self._node(node) for node in roots]
            return bits
        elif int(parent_id) == 2:
            print("籃球================================")
            roots = get_cached_trees(Category.objects.filter(is_delete=False, parent_id=2))
            bits = [self._node(node) for node in roots]
            return bits
        elif int(parent_id) == 1:
            print("足球==========================")
            roots = get_cached_trees(Category.objects.filter(is_delete=False, parent_id=1))
            bits = [self._node(node) for node in roots]
            return bits


class CategoryListView(FormatListAPIView, CreateAPIView):
    """
    竞猜分类列表
    """
    serializer_class = CategorySerializer

    def list(self, request, *args, **kwargs):
        if 'parent_id' not in self.request.GET:
            category_tree = RecurseTreeNode()
            return self.response(category_tree.tree())
        else:
            category_tree = RecurseTreeNode()
            parent_id = request.GET.get('parent_id')
            return self.response(category_tree.tree(parent_id=parent_id))

    def post(self, request, *args, **kwargs):
        parent = None
        if 'parent' in request.data and request.data['parent'] != '':
            parent = Category.objects.get(name=request.data['parent'])

        category = Category()
        category.name = request.data['name']
        category.parent = parent
        category.admin = request.user
        category.icon = request.data['icon']
        category.save()

        content = {'status': status.HTTP_201_CREATED}
        return self.response(content)


class CategoryDetailView(RetrieveUpdateDestroyAPIView):
    """
    竞猜详情数据
    """
    serializer_class = CategorySerializer
    queryset = Category.objects.all()

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        # 获取上级分类
        if instance.parent_id is not None:
            parent = Category.objects.get(id=instance.parent_id)
            instance.parent_id = parent.name

        content = {
            'status': status.HTTP_200_OK,
            'data': {
                'name': instance.name,
                'parent_id': instance.parent_id,
                'is_delete': instance.is_delete,
                'icon': instance.icon,
            },
        }
        return self.response(content)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if 'is_delete' in request.data:
            instance.is_delete = 1
        if 'name' in request.data:
            instance.name = request.data['name']
        if 'icon' in request.data:
            instance.icon = request.data['icon']
        instance.save()
        content = {'status': status.HTTP_202_ACCEPTED}
        return self.response(content)


class QuizListView(ListCreateAPIView):
    """
    get:
    获取所有竞猜数据

    post:
    添加一条竞猜数据
    """

    # serializer_class = serializers.QuizSerializer
    # filter_class = QuizFilter

    def get(self, request, *args, **kwargs):
        """
        竞猜列表只显示自己创建的竞猜数据
        :return:
        """

        admin = self.request.user

        current_page = int(request.GET.get('page'))
        search_content = request.GET.get('title__contains')
        category = request.GET.get('category')
        status = request.GET.get('status')
        is_recommend = request.GET.get('is_recommend')
        is_daily = request.GET.get('daily')
        quiz_type = request.GET.get('quiz_type')

        sql = ""

        if is_daily == "1":
            sql = "select a.title,a.sub_title,a.thumb,a.end_date,a.updated_at,a.is_recommend,b.username,a.id as `key`,c.name,a.status,start_date from "
            sql += "quiz_quiz a inner join wcc_admin_wccadmin b on a.admin_id=b.id "
            sql += "inner join quiz_category c on a.category_id=c.id "
            sql += "inner join quiz_daily d on a.id=d.quiz_id "
        else:
            sql = "select a.title,a.sub_title,a.thumb,a.end_date,a.updated_at,a.is_recommend,b.username,a.id as `key`,c.name,a.status,start_date from "
            sql += "quiz_quiz a inner join wcc_admin_wccadmin b on a.admin_id=b.id "
            sql += "inner join quiz_category c on a.category_id=c.id "
            sql += "left join quiz_daily d on a.id=d.quiz_id "
        sql_where = "where a.title like '%" + search_content + "%' and a.is_delete=0 "

        if not category == "":
            sql_where += " and a.category_id=" + category
        if not is_recommend == "":
            sql_where += " and a.is_recommend=" + is_recommend
        if not status == "":
            sql_where += " and a.status=" + status
        # if is_daily == "1":
        #     sql_where += " and substring(start_date,1,10)='" + datetime.now().strftime('%Y-%m-%d') + "'"
        if quiz_type != "" and quiz_type is not None:
            sql_where += " and a.type=" + quiz_type

        sql += sql_where  # 判断条件

        cursor = connection.cursor()
        cursor.execute(sql, None)
        dt_all = cursor.fetchall()

        page_size = int(REST_FRAMEWORK['PAGE_SIZE'])
        offset = ' LIMIT ' + str((current_page - 1) * page_size) + ',' + str(page_size)
        sql += offset  # 分页设置

        cursor.execute(sql, None)
        query_set = cursor.fetchall()

        jsonData = []
        for row in query_set:
            result = {}
            result['title'] = row[0]
            result['sub_title'] = row[1]
            result['thumb'] = row[2]
            result['end_date'] = convert_localtime( row[3])                 #
            result['updated_at'] =  convert_localtime( row[4])              # 更新时间
            result['is_recommend'] = str(row[5])
            result['admin'] = row[6]                               # 管理员
            result['key'] = row[7]
            result['category'] = row[8]                              # 分类
            result['url'] = "/" + reverse('quiz-detail', kwargs={'pk': row[7]}).split('/api/')[1]                # url
            result['status'] = row[9]
            result['start_date'] = convert_localtime(row[10]) if row[10] is not None else ''
            jsonData.append(result)

        data = {'count': len(dt_all), 'results': jsonData}
        return HttpResponse(json.dumps(data), content_type='text/json')

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        category = Category.objects.get(name=request.data['category'], is_delete=False)

        # 插入竞猜主表
        quiz = Quiz()
        quiz.category = category
        quiz.title = request.data['title']
        quiz.sub_title = request.data['sub_title']
        quiz.thumb = request.data['thumb']
        quiz.begin_at = request.data['end_date']
        quiz.admin = request.user
        quiz.status = Quiz.PUBLISHING
        quiz.save()

        # 插入竞猜答案表
        option_data = []
        idx = 1
        for i in request.data['keys']:
            option_data.append({
                'quiz': quiz,
                'title': request.data['answer-' + str(i)],
                'odds': request.data['answer-rate-' + str(i)],
                'order': idx,
            })
            idx += 1
        options = [Option(**item) for item in option_data]
        Option.objects.bulk_create(options)

        # 插入竞猜审核表
        # Audit.objects.create_audit(quiz)

        # publish_date = self.request.data.get('publish_date')
        #
        # if not publish_date==None:
        #     if not Daily.objects.filter(start_date__startswith=publish_date[0:10]):
        #         daily=Daily()
        #         daily.quiz=quiz
        #         daily.admin=request.user
        #         daily.start_date=publish_date
        #         daily.save()

        content = {'status': status.HTTP_201_CREATED}
        return HttpResponse(json.dumps(content), content_type='text/json')
