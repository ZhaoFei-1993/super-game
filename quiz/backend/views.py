# -*- coding: UTF-8 -*-
from base.backend import FormatListAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView, ListCreateAPIView, ListAPIView
from .serializers import CategorySerializer, UserQuizSerializer, UserQuizListSerializer, QuizBackendListAllSerializer
from ..models import Category, Quiz, Option, QuizCoin, Coin, Record, Rule
from chat.models import Club
from django.db import connection
from api.settings import REST_FRAMEWORK
from django.db import transaction
from django.db.models import Count, Sum
from datetime import datetime

from url_filter.integrations.drf import DjangoFilterBackend
from mptt.utils import get_cached_trees
from rest_framework import status
from utils.functions import convert_localtime, normalize_fraction
from rest_framework.reverse import reverse
from django.http import HttpResponse
import json
from utils.functions import reversion_Decorator
from django.http import JsonResponse
from decimal import Decimal


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

    @reversion_Decorator
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

    @reversion_Decorator
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

    #
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
            result['end_date'] = convert_localtime(row[3])  #
            result['updated_at'] = convert_localtime(row[4])  # 更新时间
            result['is_recommend'] = str(row[5])
            result['admin'] = row[6]  # 管理员
            result['key'] = row[7]
            result['category'] = row[8]  # 分类
            result['url'] = "/" + reverse('quiz-detail', kwargs={'pk': row[7]}).split('/api/')[1]  # url
            result['status'] = row[9]
            result['start_date'] = convert_localtime(row[10]) if row[10] is not None else ''
            jsonData.append(result)

        data = {'count': len(dt_all), 'results': jsonData}
        return HttpResponse(json.dumps(data), content_type='text/json')

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        category = Category.objects.get(name=request.data['category'], is_delete=False)
        # print("request_data==================", request.data)
        #
        # # 插入竞猜主表

        quiz = Quiz()
        quiz.category = category
        quiz.host_team = request.data['host_team']
        quiz.host_team_avatar = request.data['host_team_avatar']
        quiz.guest_team = request.data['guest_team']
        quiz.guest_team_avatar = request.data['guest_team_avatar']
        quiz.begin_at = request.data['begin_at']
        quiz.admin = request.user
        quiz.status = Quiz.PUBLISHING
        quiz.save()

        # 赛果
        result = request.data['result']
        rule_result = Rule()
        rule_result.type = 0
        rule_result.tips = '赛果'
        quiz_t = Quiz.objects.filter(category=category, host_team=quiz.host_team, guest_team=quiz.guest_team,
                                     begin_at=quiz.begin_at, admin=request.user).order_by('-created_at')
        if len(quiz_t) == 0:
            return JsonResponse({'Error': '比赛不存在'}, status=status.HTTP_400_BAD_REQUEST)
        rule_result.quiz = quiz_t[0]
        result_win = result['result_win']
        result_flat = result['result_flat']
        result_transport = result['result_transport']
        rule_result.max_odd = max([result_win, result_flat, result_transport])
        rule_result.min_odd = min([result_win, result_flat, result_transport])
        rule_result.save()
        # 主胜
        rule_t = Rule.objects.get(quiz=quiz_t[0], type=0)
        option_result_win = Option()
        option_result_win.option = '主胜'
        option_result_win.order = 1
        option_result_win.odds = result_win
        option_result_win.flag = 'h'
        option_result_win.rule = rule_t
        option_result_win.save()
        # 平局
        option_result_flat = Option()
        option_result_flat.option = '平局'
        option_result_flat.order = 2
        option_result_flat.odds = result_flat
        option_result_flat.flag = 'd'
        option_result_flat.rule = rule_t
        option_result_flat.save()
        # 主负
        option_result_transport = Option()
        option_result_transport.option = '主负'
        option_result_transport.order = 1
        option_result_transport.odds = result_transport
        option_result_transport.flag = 'a'
        option_result_transport.rule = rule_t
        option_result_transport.save()

        # 让分赛果:

        print("request===============", request.data)
        result = request.data['result']
        singleordouble = request.data['singleordouble']
        totalscore = request.data['totalscore']
        score_win = request.data['score_win']
        score_flat = request.data['score_flat']
        score_convey = request.data['score_convey']
        print("cointyp==================", result)
        print("singleordouble==================", singleordouble)
        print("totalscore==================", totalscore)
        print("score_win==================", score_win)
        print("score_flat==================", score_flat)
        print("score_convey==================", score_convey)
        # for i in cointype:
        #     coin = Coin.objects.filter(name=i)
        #     quizcoin = QuizCoin()
        #     quizcoin.quiz = quiz
        #     quizcoin.coin = coin[0]
        #     quizcoin.save()

        # 插入竞猜答案表
        # option_data = []
        # idx = 1
        # for i in request.data['keys']:
        #     option_data.append({
        #         'quiz': quiz,
        #         'title': request.data['answer-' + str(i)],
        #         'odds': request.data['answer-rate-' + str(i)],
        #         'order': idx,
        #     })
        #     idx += 1
        # options = [Option(**item) for item in option_data]
        # Option.objects.bulk_create(options)

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


class UserQuizView(ListCreateAPIView):
    """
    用户竞猜列表
    """
    queryset = Record.objects.filter(source__in=[Record.NORMAL, Record.GIVE])
    serializer_class = UserQuizSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['user', 'bet', 'earn_coin', 'option']


class QuizListBackEndView(FormatListAPIView):
    """
    后台竞猜列表
    """

    def ts_null_2_zero(self, item):
        if item == None:
            return 0
        else:
            return float(normalize_fraction(item, 4))

    def list(self, request, *args, **kwargs):
        category = kwargs['category']
        records = Record.objects.filter(source__in=[Record.NORMAL, Record.GIVE], quiz__category__parent__id=category)
        values = records.values("quiz", "roomquiz_id").annotate(total_bet=Count('id'),
                                                                sum_bet=Sum('bet')).order_by('-quiz__begin_at')
        data = []
        for x in values:
            q_id = int(x['quiz'])
            r_id = int(x['roomquiz_id'])
            sum_out = self.ts_null_2_zero(
                records.filter(quiz_id=q_id, roomquiz_id=r_id, earn_coin__gt=0).aggregate(Sum('earn_coin'))[
                    'earn_coin__sum'])

            try:
                quiz = Quiz.objects.get(id=q_id)
                room = Club.objects.get(id=r_id)
            except Exception:
                return JsonResponse({'ERROR': '比赛不存在或币种不存在'}, status=status.HTTP_400_BAD_REQUEST)
            state = ''
            for i in quiz.STATUS_CHOICE:
                if int(quiz.status) == i[0]:
                    state = i[1]
            match_time = quiz.begin_at.strftime('%Y-%m-%d %H:%M')
            temp_dict = {
                'quiz_id': quiz.id,
                'match_name': quiz.match_name,
                'host_team': quiz.host_team,
                'guest_team': quiz.guest_team,
                'match_time': match_time,
                'score': str(quiz.host_team_score) + ":" + str(quiz.guest_team_score),
                'room': room.room_title,
                'room_id': room.id,
                'total_bet': x['total_bet'],
                'sum_bet': x['sum_bet'],
                'sum_out': sum_out,
                'status': state,
            }
            if int(quiz.status) != Quiz.BONUS_DISTRIBUTION:
                temp_dict['sum_earn_coin']=0
            else:
                temp_dict['sum_earn_coin']=normalize_fraction(float(temp_dict['sum_bet'])-temp_dict['sum_out'],8)
            data.append(temp_dict)
        return JsonResponse({'results': data}, status=status.HTTP_200_OK)


class QuizListBackEndDetailView(ListAPIView):
    """
    比赛赛果
    """

    def list(self, request, *args, **kwargs):
        type = int(self.kwargs['type'])
        for i in ['room', 'quiz_id']:
            if i not in request.query_params:
                return JsonResponse({'Error:参数%s缺失' % i}, status=status.HTTP_400_BAD_REQUEST)
        quiz_id = request.query_params.get('quiz_id')
        room = request.query_params.get('room')
        if quiz_id == '':
            return JsonResponse({'Error:参数quiz_id不能为空,需为整数'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            quiz_id = int(quiz_id)
        if room == '':
            return JsonResponse({'Error:参数room不能为空,需为整数'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            room = int(room)
        records = Record.objects.filter(source__in=[Record.NORMAL, Record.GIVE], quiz_id=quiz_id, roomquiz_id=room,
                                        rule__type=type)
        if len(records) > 0:
            rule_id = records[0].rule_id
            options = Option.objects.filter(rule_id=rule_id).order_by('id')
        else:
            return JsonResponse({'提示': '无投注数据'}, status=status.HTTP_200_OK)
        data = []
        if len(options) > 0:
            for x in options:
                count_t = records.filter(option__option=x.id).count()
                sum_t = records.filter(option__option=x.id).aggregate(Sum('bet'))
                temp_dict = {
                    'item': x.option,
                    'option_id': x.id,
                    'odds': x.odds,
                    'count': count_t,
                    'sum_bet': 0 if sum_t['bet__sum'] == None else sum_t['bet__sum']
                }
                if type in [0, 1, 4, 5]:
                    temp_dict['rate'] = round((100 * count_t) / records.count(), 0)
                    if type in [1, 5]:
                        temp_dict['home_let_score'] = x.rule.home_let_score
                        temp_dict['guest_let_score'] = x.rule.guest_let_score
                if type in [2, 7]:
                    temp_dict['option_type'] = x.option_type
                data.append(temp_dict)
        else:
            return JsonResponse({'Error': '无对应选项'}, status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'results': data}, status=status.HTTP_200_OK)


class UserQuizListView(ListAPIView):
    """
    用户竞猜列表详情
    """

    serializer_class = UserQuizListSerializer

    def get_queryset(self):
        pk = self.kwargs['user_id']
        room_id = self.kwargs['room_id']
        rec_s = Record.objects.filter(user_id=pk, source__in=[Record.NORMAL, Record.GIVE], roomquiz_id=room_id)
        return rec_s


class QuizCountListView(ListAPIView):
    """
    下注人数
    """
    serializer_class = UserQuizSerializer

    def get_queryset(self):
        option_id = int(self.kwargs['pk'])
        room = int(self.kwargs['room'])
        records = Record.objects.filter(source__in=[Record.NORMAL, Record.GIVE], roomquiz_id=room,
                                        option__option_id=option_id)
        return records


class QuizListAllView(ListAPIView):
    """
    竞猜比赛所有列表
    """
    serializer_class = QuizBackendListAllSerializer

    def get_queryset(self):
        category = self.kwargs['category']  # 1为篮球, 2为足球
        quiz_s = Quiz.objects.filter(category__parent_id=category)
        return quiz_s
