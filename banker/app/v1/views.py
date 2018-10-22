# -*- coding: UTF-8 -*-
from base.app import ListAPIView
from base.function import LoginRequired
from base import code as error_code
from base.exceptions import ParamErrorException
from django.db.models import Q
from chat.models import ClubRule, Club
from quiz.models import Category


class BankerRuleView(ListAPIView):
    """
       联合坐庄：   玩法
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        quiz_info = Category.objects.filter(Q(id=2) | Q(id=1))
        rule_info = ClubRule.objects.filter(Q(id=2) | Q(id=3)).order_by('id')

        data = []
        for i in quiz_info:
            data.append({
                "icon": i.icon,
                "name": i.name
            })

        for s in rule_info:
            data.append({
                "icon": s.icon,
                "name": s.title
            })

        return self.response({"code": 0, "data": data})


class BankerClubView(ListAPIView):
    """
        联合坐庄：   俱乐部
    """

    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        club_info = Club.objects.filter(~Q(is_recommend=0)).order_by("room_title")

        data = []
        for i in club_info:
            coin_name = i.coin.name
            data.append({
                "icon": i.icon,
                "title": i.coin.name,
                "club_id": i.id,
            })

        return self.response({"code": 0, "data": data})


# class BankerDetailView(ListAPIView):
#     """
#         联合坐庄：   坐庄
#     """
#     permission_classes = (LoginRequired,)
#
#     serializer_class = QuizSerialize
#
#     def get_queryset(self):
#         # 竞猜赛事分类
#         category_id = None
#         if 'category' in self.request.GET and self.request.GET.get('category') != '':
#             category_id = self.request.GET.get('category')
#
#         # 赛事类型：1＝未结束，2＝已结束
#         quiz_type = 1
#         if 'type' in self.request.GET and self.request.GET['type'] != '':
#             quiz_type = int(self.request.GET.get('type'))
#
#         if 'is_user' not in self.request.GET:
#             if category_id is None:
#                 if quiz_type == 1:  # 未结束
#                     return Quiz.objects.filter(Q(status=0) | Q(status=1) | Q(status=2), is_delete=False).order_by(
#                         'begin_at')
#                 elif quiz_type == 2:  # 已结束
#                     return Quiz.objects.filter(Q(status=3) | Q(status=4) | Q(status=5), is_delete=False).order_by(
#                         '-begin_at')
#             else:
#                 category_id = str(category_id)
#                 category_arr = category_id.split(',')
#                 if quiz_type == 1:  # 未开始
#                     return Quiz.objects.filter(Q(status=0) | Q(status=1) | Q(status=2),
#                                                is_delete=False, category__in=category_arr).order_by('begin_at')
#                 elif quiz_type == 2:  # 已结束
#                     return Quiz.objects.filter(Q(status=3) | Q(status=4) | Q(status=5),
#                                                is_delete=False, category__in=category_arr).order_by('-begin_at')
#         else:
#             user_id = self.request.user.id
#             roomquiz_id = self.request.parser_context['kwargs']['roomquiz_id']
#             quiz_id = list(
#                 set(Record.objects.filter(user_id=user_id, roomquiz_id=roomquiz_id).values_list('quiz_id', flat=True)))
#             my_quiz = Quiz.objects.filter(id__in=quiz_id).order_by('-begin_at')
#             return my_quiz
#
#     def list(self, request, *args, **kwargs):
#         results = super().list(request, *args, **kwargs)
#         value = results.data.get('results')
#         data = []
#         quiz_id_list = ''
#         for fav in value:
#             if quiz_id_list == '':
#                 quiz_id_list = str(fav.get('id'))
#             else:
#                 quiz_id_list = str(quiz_id_list) + ',' + str(fav.get('id'))
#             data.append({
#                 "id": fav.get('id'),
#                 "match_name": fav.get('match_name'),
#                 "host_team": fav.get('host_team'),
#                 'host_team_avatar': fav.get('host_team_avatar'),
#                 'host_team_score': fav.get('host_team_score'),
#                 'guest_team': fav.get('guest_team'),
#                 'guest_team_avatar': fav.get('guest_team_avatar'),
#                 'guest_team_score': fav.get('guest_team_score'),
#                 'begin_at': fav.get('begin_at'),
#                 'total_people': fav.get('total_people'),
#                 'total_coin': '0',
#                 'is_bet': fav.get('is_bet'),
#                 'category': fav.get('category'),
#                 'is_end': fav.get('is_end'),
#                 'win_rate': fav.get('win_rate'),
#                 'planish_rate': fav.get('planish_rate'),
#                 'lose_rate': fav.get('lose_rate'),
#                 'total_coin_avatar': fav.get('total_coin_avatar'),
#                 'status': fav.get('status'),
#             })
#
#         quiz_id_list = '(' + quiz_id_list + ')'
#         roomquiz_id = self.request.parser_context['kwargs']['roomquiz_id']
#         if len(quiz_id_list) > 2:
#             sql = "select  a.quiz_id, sum(a.bet) from quiz_record a"
#             sql += " where a.quiz_id in " + str(quiz_id_list)
#             sql += " and a.roomquiz_id = '" + str(roomquiz_id) + "'"
#             sql += " group by a.quiz_id"
#             total_coin = get_sql(sql)  # 投注金额
#             club = Club.objects.get(pk=roomquiz_id)
#             for s in total_coin:
#                 for a in data:
#                     if a['id'] == s[0]:
#                         a['total_coin'] = normalize_fraction(s[1], int(club.coin.coin_accuracy))
#
#         return self.response({"code": 0, "data": data})