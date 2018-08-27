# -*- coding: UTF-8 -*-
from django.db import transaction
from django.db.models import Q, Sum
from base.function import LoginRequired, time_data
from base.app import ListAPIView, ListCreateAPIView
from ...models import Category, Quiz, Record, Rule, Option, OptionOdds, ClubProfitAbroad, ChangeRecord, \
    EveryDayInjectionValue
from users.models import CoinDetail
from chat.models import Club
from users.models import UserCoin, CoinValue, Coin, CoinGiveRecords
from base.exceptions import ParamErrorException
from base import code as error_code
from decimal import Decimal
from .serializers import QuizSerialize, RecordSerialize, QuizDetailSerializer, QuizPushSerializer, \
    ClubProfitAbroadSerialize
from utils.functions import value_judge, get_sql
from datetime import datetime, timedelta
from django.conf import settings
from utils.functions import normalize_fraction
from utils.cache import get_cache, set_cache


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
            category_name = category.name
            if self.request.GET.get('language') == 'en':
                category_name = category.name_en
            categoryslist = Category.objects.filter(parent_id=category.id, is_delete=0).order_by('order')
            for categorylist in categoryslist:
                categorylist_name = categorylist.name
                if self.request.GET.get('language') == 'en':
                    categorylist_name = categorylist.name_en
                    if categorylist_name == "" or categorylist_name == None:
                        categorylist_name = categorylist.name
                number = Quiz.objects.filter(category_id=categorylist.id).count()
                if number <= 0:
                    continue
                children.append({
                    "category_id": categorylist.id,
                    "category_name": categorylist_name,
                })
            data.append({
                "category_id": category.id,
                "category_name": category_name,
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
        return Quiz.objects.filter(status=0, is_delete=False).order_by('-total_people')[:10]

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        quiz_id_list = ''
        for fav in items:
            if quiz_id_list == '':
                quiz_id_list = fav.get('id')
            else:
                quiz_id_list = str(quiz_id_list) + ',' + str(fav.get('id'))
            data.append({
                "id": fav.get('id'),
                "match_name": fav.get('match_name'),
                "host_team": fav.get('host_team'),
                'host_team_avatar': fav.get('host_team_avatar'),
                'guest_team': fav.get('guest_team'),
                'guest_team_avatar': fav.get('guest_team_avatar'),
                'guest_team_score': fav.get('guest_team_score'),
                'host_team_score': fav.get('host_team_score'),
                'begin_at': fav.get('begin_at'),
                'total_people': fav.get('total_people'),
                'total_coin': '',
                'is_bet': fav.get('is_bet'),
                'category': fav.get('category'),
                'is_end': fav.get('is_end'),
                'win_rate': fav.get('win_rate'),
                'planish_rate': fav.get('planish_rate'),
                'lose_rate': fav.get('lose_rate'),
                'total_coin_avatar': fav.get('total_coin_avatar'),
                'status': fav.get('status'),
            })

        quiz_id_list = '(' + quiz_id_list + ')'
        roomquiz_id = self.request.parser_context['kwargs']['roomquiz_id']
        sql = "select  a.quiz_id, sum(a.bet) from quiz_record a"
        sql += " where a.quiz_id in " + str(quiz_id_list)
        sql += " and a.roomquiz_id = '" + str(roomquiz_id) + "'"
        sql += " group by a.quiz_id"
        total_coin = get_sql(sql)  # 投注金额
        club = Club.objects.get(pk=roomquiz_id)
        for s in total_coin:
            for a in data:
                if a['id'] == s[0]:
                    a['total_coin'] = int(s[1])
                    a['total_coin'] = normalize_fraction(str(s[1]), int(club.coin.coin_accuracy))

        return self.response({'code': 0, 'data': data})


class QuizListView(ListCreateAPIView):
    """
    获取竞猜列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = QuizSerialize

    def get_queryset(self):
        # 竞猜赛事分类
        category_id = None
        if 'category' not in self.request.GET or self.request.GET.get('category') == '':
            category_id = self.request.GET.get('category')

        # 赛事类型：1＝未结束，2＝已结束
        quiz_type = 1
        if 'type' not in self.request.GET or self.request.GET['type'] == '':
            quiz_type = int(self.request.GET.get('type'))

        if 'is_user' not in self.request.GET:
            if category_id is None:
                if quiz_type == 1:  # 未结束
                    return Quiz.objects.filter(Q(status=0) | Q(status=1) | Q(status=2), is_delete=False).order_by('begin_at')
                elif quiz_type == 2:  # 已结束
                    return Quiz.objects.filter(Q(status=3) | Q(status=4) | Q(status=5), is_delete=False).order_by('-begin_at')
            else:
                category_id = str(category_id)
                category_arr = category_id.split(',')
                if quiz_type == 1:  # 未开始
                    return Quiz.objects.filter(Q(status=0) | Q(status=1) | Q(status=2),
                                               is_delete=False, category__in=category_arr).order_by('begin_at')
                elif quiz_type == 2:  # 已结束
                    return Quiz.objects.filter(Q(status=3) | Q(status=4) | Q(status=5),
                                               is_delete=False, category__in=category_arr).order_by('-begin_at')
        else:
            user_id = self.request.user.id
            roomquiz_id = self.request.parser_context['kwargs']['roomquiz_id']
            quiz_id = list(
                set(Record.objects.filter(user_id=user_id, roomquiz_id=roomquiz_id).values_list('quiz_id', flat=True)))
            my_quiz = Quiz.objects.filter(id__in=quiz_id).order_by('-begin_at')
            return my_quiz

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        value = results.data.get('results')
        data = []
        quiz_id_list = ''
        for fav in value:
            if quiz_id_list == '':
                quiz_id_list = fav.get('id')
            else:
                quiz_id_list = str(quiz_id_list) + ',' + str(fav.get('id'))
            data.append({
                "id": fav.get('id'),
                "match_name": fav.get('match_name'),
                "host_team": fav.get('host_team'),
                'host_team_avatar': fav.get('host_team_avatar'),
                'host_team_score': fav.get('host_team_score'),
                'guest_team': fav.get('guest_team'),
                'guest_team_avatar': fav.get('guest_team_avatar'),
                'guest_team_score': fav.get('guest_team_score'),
                'begin_at': fav.get('begin_at'),
                'total_people': fav.get('total_people'),
                'total_coin': '',
                'is_bet': fav.get('is_bet'),
                'category': fav.get('category'),
                'is_end': fav.get('is_end'),
                'win_rate': fav.get('win_rate'),
                'planish_rate': fav.get('planish_rate'),
                'lose_rate': fav.get('lose_rate'),
                'total_coin_avatar': fav.get('total_coin_avatar'),
                'status': fav.get('status'),
            })

        quiz_id_list = '(' + quiz_id_list + ')'
        roomquiz_id = self.request.parser_context['kwargs']['roomquiz_id']
        if len(quiz_id_list) > 2:
            sql = "select  a.quiz_id, sum(a.bet) from quiz_record a"
            sql += " where a.quiz_id in " + str(quiz_id_list)
            sql += " and a.roomquiz_id = '" + str(roomquiz_id) + "'"
            sql += " group by a.quiz_id"
            total_coin = get_sql(sql)  # 投注金额
            club = Club.objects.get(pk=roomquiz_id)
            for s in total_coin:
                for a in data:
                    if a['id'] == s[0]:
                        a['total_coin'] = int(s[1])
                        a['total_coin'] = normalize_fraction(str(s[1]), int(club.coin.coin_accuracy))

        return self.response({"code": 0, "data": data})


class RecordsListView(ListCreateAPIView):
    """
    竞猜记录
    """
    permission_classes = (LoginRequired,)
    serializer_class = RecordSerialize

    def get_queryset(self):
        if 'user_id' not in self.request.GET:
            user_id = self.request.user.id
            roomquiz_id = self.request.parser_context['kwargs']['roomquiz_id']
            if 'is_end' not in self.request.GET:
                record = Record.objects.filter(user_id=user_id, roomquiz_id=roomquiz_id).order_by('-created_at')
                return record
            else:
                is_end = self.request.GET.get('is_end')
                if int(is_end) == 1:
                    return Record.objects.filter(
                        Q(quiz__status=0) | Q(quiz__status=1) | Q(quiz__status=2) | Q(quiz__status=3),
                        user_id=user_id,
                        roomquiz_id=roomquiz_id).order_by('-created_at')
                else:
                    return Record.objects.filter(Q(quiz__status=4) | Q(quiz__status=5) | Q(quiz__status=6),
                                                 user_id=user_id,
                                                 roomquiz_id=roomquiz_id).order_by('-created_at')
        else:
            user_id = self.request.GET.get('user_id')
            roomquiz_id = self.request.parser_context['kwargs']['roomquiz_id']
            return Record.objects.filter(user_id=user_id, roomquiz_id=roomquiz_id).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        progress = results.data.get('results')
        data = []
        tmp = ''

        language = request.GET.get('language')

        club_ids = []
        quiz_ids = []
        option_odds_ids = []
        for fav in progress:
            club_ids.append(int(fav.get('roomquiz_id')))
            quiz_ids.append(int(fav.get('quiz_id')))
            option_odds_ids.append(int(fav.get('option_id')))

        # 俱乐部对应货币精度
        clubs = Club.objects.get_all()
        coins = Coin.objects.get_all()
        map_coin_accuracy = {}
        map_coin_icon = {}
        map_coin_name = {}
        for coin in coins:
            for club in clubs:
                if club.coin_id != coin.id:
                    continue
                map_coin_accuracy[club.id] = coin.coin_accuracy
                map_coin_icon[club.id] = coin.icon
                map_coin_name[club.id] = coin.name

        # 竞猜比赛数据
        quizs = Quiz.objects.filter(id__in=quiz_ids)
        map_team_info = {}
        map_quiz_category_name = {}
        for quiz in quizs:
            map_team_info[quiz.id] = quiz

            quiz_category = Category.objects.get_one(pk=quiz.category_id)
            category = Category.objects.get_one(pk=quiz_category.parent_id)
            map_quiz_category_name[quiz.id] = category.name

        # 获取我的选项及我的选项是否正确，通过option_odds获取option_id，然后通过option_id获取rule_id
        option_odds = OptionOdds.objects.filter(id__in=option_odds_ids)
        option_ids = []
        for option_odd in option_odds:
            option_ids.append(option_odd.option_id)
        options = Option.objects.filter(id__in=option_ids)
        rule_ids = []
        map_option_odds_option = {}
        for item in options:
            rule_ids.append(item.rule_id)
            for option_odd in option_odds:
                if option_odd.option_id != item.id:
                    continue
                map_option_odds_option[option_odd.id] = item
        rules = Rule.objects.filter(id__in=rule_ids)
        map_option_rule = {}
        for rule in rules:
            for option in options:
                if option.rule_id != rule.id:
                    continue
                map_option_rule[option.id] = rule
        map_option_odds_rule = {}
        for option_odd in option_odds:
            map_option_odds_rule[option_odd.id] = map_option_rule[option_odd.option_id]

        for fav in progress:
            club_id = int(fav.get('roomquiz_id'))
            quiz_id = int(fav.get('quiz_id'))
            option_odd_id = int(fav.get('option_id'))

            pecific_dates = fav.get('created_at')[0].get('years')
            pecific_date = fav.get('created_at')[0].get('year')

            # 队名
            quiz = map_team_info[quiz_id]
            if language == 'en':
                host_team = quiz.host_team_en
                guest_team = quiz.guest_team_en

                if host_team == '' or host_team is None:
                    host_team = quiz.host_team

                if guest_team == '' or guest_team is None:
                    guest_team = quiz.guest_team
            else:
                host_team = quiz.host_team
                guest_team = quiz.guest_team

            status = int(quiz.status)
            earn_coin = Decimal(float(fav.get('earn_coin')))

            # 获取盈亏数据
            earn_coin_str = '待开奖'
            if language == 'en':
                earn_coin_str = 'Wait results'
            if status in [Quiz.PUBLISHING_ANSWER, Quiz.BONUS_DISTRIBUTION]:
                if earn_coin <= 0:
                    earn_coin_str = "猜错"
                    if language == 'en':
                        earn_coin_str = "Guess wrong"
                else:
                    earn_coin_str = "+" + str(normalize_fraction(earn_coin, map_coin_accuracy[club_id]))

            if tmp == pecific_date:
                pecific_date = ""
                pecific_dates = ""
            else:
                tmp = pecific_date

            # 获取用户选项数据
            rule = map_option_odds_rule[option_odd_id]
            option = map_option_odds_option[option_odd_id]
            if language == 'en':
                tips = rule.tips_en
                if tips == '' or tips is None:
                    tips = rule.tips
            else:
                tips = rule.tips
            if language == 'en':
                option_str = option.option_en
                if option_str is None or option_str == '':
                    option_str = option.option
            else:
                option_str = option.option
            my_option = tips + ':' + option_str + '/' + str(normalize_fraction(fav.get('odds'), 2))

            data.append({
                "id": fav.get('id'),
                "quiz_id": fav.get('quiz_id'),
                "type": fav.get('type'),
                'host_team': host_team,
                'guest_team': guest_team,
                'earn_coin': earn_coin_str,
                'pecific_dates': pecific_dates,
                'pecific_date': pecific_date,
                'pecific_time': fav.get('created_at')[0].get('time'),
                'my_option': my_option,
                'is_right': option.is_right,
                'coin_avatar': map_coin_icon[club_id],
                'category_name': map_quiz_category_name[quiz.id],
                'coin_name': map_coin_name[club_id],
                'bet': normalize_fraction(fav.get('bet'), map_coin_accuracy[club_id])
            })
        return self.response({'code': 0, 'data': data})


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
        item = items[0]
        return self.response({"code": 0, "data": {
            "id": item['id'],
            "host_team": item['host_team'],
            "host_team_score": item['host_team_score'],
            "guest_team": item['guest_team'],
            "guest_team_score": item['guest_team_score'],
            "begin_at": item['start'],
            "year": item['year'],
            "time": item['time'],
            "status": item['status']
        }})


class QuizPushView(ListAPIView):
    """
    下注页面推送
    """
    permission_classes = (LoginRequired,)
    serializer_class = QuizPushSerializer

    def get_queryset(self):
        roomquiz_id = self.request.GET.get('roomquiz_id')
        quiz_id = self.request.parser_context['kwargs']['quiz_id']
        record = Record.objects.filter(quiz_id=quiz_id, roomquiz_id=roomquiz_id)
        return record

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for item in items:
            data.append(
                {
                    "quiz_id": item['id'],
                    "username": item['username'],
                    "my_rule": item['my_rule'],
                    "my_option": item['my_option'],
                    "bet": item['bet']
                }
            )
        return self.response({"code": 0, "data": data})


class RuleView(ListAPIView):
    """
    竞猜选项
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        user = request.user.id
        roomquiz_id = self.request.GET.get('roomquiz_id')
        quiz_id = kwargs['quiz_id']
        rule = Rule.objects.filter(quiz_id=quiz_id).order_by('type')
        clubinfo = Club.objects.get(pk=int(roomquiz_id))
        coin_id = clubinfo.coin.pk
        coin_betting_control = clubinfo.coin.betting_control
        coin_betting_control = normalize_fraction(coin_betting_control, int(clubinfo.coin.coin_accuracy))
        coin_betting_toplimit = clubinfo.coin.betting_toplimit
        coin_betting_toplimit = normalize_fraction(coin_betting_toplimit, int(clubinfo.coin.coin_accuracy))
        usercoin = UserCoin.objects.get(user_id=user, coin_id=coin_id)
        is_bet = usercoin.id
        balance = normalize_fraction(usercoin.balance, int(clubinfo.coin.coin_accuracy))
        coin_name = usercoin.coin.name
        coin_icon = usercoin.coin.icon

        coinvalue = CoinValue.objects.filter(coin_id=coin_id).order_by('value')
        value1 = coinvalue[0].value
        value1 = normalize_fraction(value1, coinvalue[0].coin.coin_accuracy)
        value2 = coinvalue[1].value
        value2 = normalize_fraction(value2, coinvalue[0].coin.coin_accuracy)
        value3 = coinvalue[2].value
        value3 = normalize_fraction(value3, coinvalue[0].coin.coin_accuracy)
        data = []
        for i in rule:
            # option = Option.objects.filter(rule_id=i.pk).order_by('order')
            option = OptionOdds.objects.filter(option__rule_id=i.pk, club_id=roomquiz_id).order_by('option__order')
            option_id = OptionOdds.objects.filter(option__rule_id=i.pk, club_id=roomquiz_id).order_by(
                'option__order').values('pk')
            list = []
            total = Record.objects.filter(option_id__in=option_id, rule_id=i.pk, roomquiz_id=roomquiz_id).count()
            for s in option:
                is_record = Record.objects.filter(user_id=user, roomquiz_id=roomquiz_id, option_id=s.pk).count()
                is_choice = 0
                if int(is_record) > 0:
                    is_choice = 1
                odds = normalize_fraction(s.odds, 2)
                number = Record.objects.filter(roomquiz_id=roomquiz_id, rule_id=i.pk, option_id=s.pk).count()
                if number == 0 or total == 0:
                    accuracy = "0"
                else:
                    accuracy = number / total
                    accuracy = Decimal(accuracy).quantize(Decimal('0.00'))
                option = s.option.option
                if self.request.GET.get('language') == 'en':
                    option = s.option.option_en
                    if option == '' or option == None:
                        option = s.option.option
                list.append({
                    "option_id": s.pk,
                    "option": option,
                    "odds": odds,
                    "option_type": s.option.option_type,
                    "is_right": s.option.is_right,
                    "number": number,
                    "accuracy": accuracy,
                    "is_choice": is_choice,
                    "order": s.option.order
                })
            # 比分
            win = []
            flat = []
            loss = []
            if int(i.type) == 2:
                for l in list:
                    if str(l['option_type']) == "胜":
                        win.append(l)
                    elif str(l['option_type']) == "平":
                        flat.append(l)
                    else:
                        loss.append(l)
                tips = i.tips
                if self.request.GET.get('language') == 'en':
                    tips = i.tips_en
                    if tips == '' or tips == None:
                        tips = i.tips
                data.append({
                    "quiz_id": i.quiz_id,
                    "type": i.TYPE_CHOICE[int(i.type)][1],
                    "tips": tips,
                    "home_let_score": normalize_fraction(i.home_let_score, int(coinvalue[0].coin.coin_accuracy)),
                    "guest_let_score": normalize_fraction(i.guest_let_score, int(coinvalue[0].coin.coin_accuracy)),
                    "estimate_score": normalize_fraction(i.estimate_score, int(coinvalue[0].coin.coin_accuracy)),
                    "list_win": win,
                    "list_flat": flat,
                    "list_loss": loss
                })
            elif int(i.type) == 7:
                for l in list:
                    if str(l['option_type']) == "主胜":
                        win.append(l)
                    else:
                        loss.append(l)
                    win.sort(key=lambda x: x["order"])
                    flat.sort(key=lambda x: x["order"])
                    loss.sort(key=lambda x: x["order"])
                tips = i.tips
                if self.request.GET.get('language') == 'en':
                    tips = i.tips_en
                    if tips == '' or tips == None:
                        tips = i.tips
                data.append({
                    "quiz_id": i.quiz_id,
                    "type": i.TYPE_CHOICE[int(i.type)][1],
                    "tips": tips,
                    "home_let_score": normalize_fraction(i.home_let_score, int(coinvalue[0].coin.coin_accuracy)),
                    "guest_let_score": normalize_fraction(i.guest_let_score, int(coinvalue[0].coin.coin_accuracy)),
                    "estimate_score": normalize_fraction(i.estimate_score, int(coinvalue[0].coin.coin_accuracy)),
                    "list_win": win,
                    "list_loss": loss,
                })

            # 亚盘
            elif int(i.type) == Rule.AISA_RESULTS:
                if settings.ASIA_GAME_OPEN:
                    tips = i.tips
                    if self.request.GET.get('language') == 'en':
                        tips = i.tips_en
                        if tips == '' or tips == None:
                            tips = i.tips
                    data.append({
                        "quiz_id": i.quiz_id,
                        "type": i.TYPE_CHOICE[int(i.type)][1],
                        "tips": tips,
                        "home_let_score": normalize_fraction(i.home_let_score, int(coinvalue[0].coin.coin_accuracy)),
                        "guest_let_score": normalize_fraction(i.guest_let_score, int(coinvalue[0].coin.coin_accuracy)),
                        "estimate_score": normalize_fraction(i.estimate_score, int(coinvalue[0].coin.coin_accuracy)),
                        "handicap": i.handicap,
                        "list": list
                    })

            else:
                tips = i.tips
                if self.request.GET.get('language') == 'en':
                    tips = i.tips_en
                    if tips == '' or tips == None:
                        tips = i.tips
                data.append({
                    "quiz_id": i.quiz_id,
                    "type": i.TYPE_CHOICE[int(i.type)][1],
                    "tips": tips,
                    "home_let_score": normalize_fraction(i.home_let_score, int(coinvalue[0].coin.coin_accuracy)),
                    "guest_let_score": normalize_fraction(i.guest_let_score, int(coinvalue[0].coin.coin_accuracy)),
                    "estimate_score": normalize_fraction(i.estimate_score, int(coinvalue[0].coin.coin_accuracy)),
                    "list": list
                })
        return self.response({'code': 0, 'data': data,
                              'list': {'is_bet': is_bet, 'balance': balance, 'coin_name': coin_name,
                                       'coin_icon': coin_icon, 'coin_betting_control': coin_betting_control,
                                       'coin_betting_toplimit': coin_betting_toplimit, 'value1': value1,
                                       'value2': value2, 'value3': value3}})


class BetView(ListCreateAPIView):
    """
    竞猜下注
    """

    # max_wager = 10000
    def get_queryset(self):
        pass

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        value = value_judge(request, "quiz_id", "option", "wager", "roomquiz_id")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        user = request.user
        quiz_id = self.request.data['quiz_id']  # 获取竞猜ID
        roomquiz_id = self.request.data['roomquiz_id']  # 获取俱乐部ID
        # 单个下注
        option = self.request.data['option']  # 获取选项ID
        coins = self.request.data['wager']  # 获取投注金额
        coins = float(coins)

        clubinfo = Club.objects.get(pk=roomquiz_id)
        coin_id = clubinfo.coin.pk  # 破产赠送hand功能
        coin_accuracy = clubinfo.coin.coin_accuracy  # 破产赠送hand功能
        # usercoin = UserCoin.objects.get(user_id=user.id, coin_id=coin_id)
        # if int(usercoin.balance) < 1000 and int(roomquiz_id) == 1:
        #     today = date.today()
        #     is_give = BankruptcyRecords.objects.filter(user_id=user.id, coin_name="HAND", money=10000,
        #                                                created_at__gte=today).count()
        #     if is_give <= 0:
        #         usercoin.balance += Decimal(10000)
        #         usercoin.save()
        #         coin_bankruptcy = CoinDetail()
        #         coin_bankruptcy.user = user
        #         coin_bankruptcy.coin_name = 'HAND'
        #         coin_bankruptcy.amount = '+' + str(10000)
        #         coin_bankruptcy.rest = Decimal(usercoin.balance)
        #         coin_bankruptcy.sources = 4
        #         coin_bankruptcy.save()
        #         bankruptcy_info = BankruptcyRecords()
        #         bankruptcy_info.user = user
        #         bankruptcy_info.coin_name = 'HAND'
        #         bankruptcy_info.money = Decimal(10000)
        #         bankruptcy_info.save()
        #         user_message = UserMessage()
        #         user_message.status = 0
        #         user_message.user = user
        #         user_message.message_id = 10
        #         user_message.save()

        try:  # 判断选项ID是否有效
            option_odds = OptionOdds.objects.get(pk=option)
        except Exception:
            raise ParamErrorException(error_code.API_50101_QUIZ_OPTION_ID_INVALID)
        if int(option_odds.quiz.id) != int(quiz_id):
            raise ParamErrorException(error_code.API_50101_QUIZ_OPTION_ID_INVALID)
        i = 0
        Decimal(i)
        # 判断赌注是否有效
        if i >= Decimal(coins):
            raise ParamErrorException(error_code.API_50102_WAGER_INVALID)
        quiz = Quiz.objects.get(pk=quiz_id)  # 判断比赛
        nowtime = datetime.now()
        if nowtime > quiz.begin_at:
            raise ParamErrorException(error_code.API_50108_THE_GAME_HAS_STARTED)
        if int(quiz.status) != 0 or quiz.is_delete is True:
            raise ParamErrorException(error_code.API_50107_USER_BET_TYPE_ID_INVALID)
        coin_betting_control = float(clubinfo.coin.betting_control)
        coin_betting_toplimit = float(clubinfo.coin.betting_toplimit)
        if coin_betting_control > coins or coin_betting_toplimit < coins:
            raise ParamErrorException(error_code.API_50102_WAGER_INVALID)

        # HAND币单场比赛最大下注
        bet_sum = Record.objects.filter(user_id=user.id, roomquiz_id=roomquiz_id, quiz_id=quiz_id).aggregate(
            Sum('bet'))
        if coin_id == Coin.HAND:
            if bet_sum['bet__sum'] is not None and bet_sum['bet__sum'] >= 5000000:
                raise ParamErrorException(error_code.API_50109_BET_LIMITED)
        elif coin_id == Coin.INT:
            if bet_sum['bet__sum'] is not None and bet_sum['bet__sum'] >= 20000:
                raise ParamErrorException(error_code.API_50109_BET_LIMITED)
        elif coin_id == Coin.ETH:
            if bet_sum['bet__sum'] is not None and bet_sum['bet__sum'] >= 6:
                raise ParamErrorException(error_code.API_50109_BET_LIMITED)
        elif coin_id == Coin.BTC:
            if bet_sum['bet__sum'] is not None and bet_sum['bet__sum'] >= 0.5:
                raise ParamErrorException(error_code.API_50109_BET_LIMITED)
        elif coin_id == Coin.USDT:
            if bet_sum['bet__sum'] is not None and bet_sum['bet__sum'] >= 3100:
                raise ParamErrorException(error_code.API_50109_BET_LIMITED)

        usercoin = UserCoin.objects.get(user_id=user.id, coin_id=coin_id)
        # 判断用户金币是否足够
        if float(usercoin.balance) < coins:
            raise ParamErrorException(error_code.API_50104_USER_COIN_NOT_METH)
        rule_id = option_odds.option.rule_id

        # 调整赔率
        Option.objects.change_odds(rule_id, coin_id, roomquiz_id)

        if clubinfo.coin.name == "USDT":  # USDT下注
            give_coin = CoinGiveRecords.objects.get(user_id=user.id)
            coins = normalize_fraction(coins, coin_accuracy)  # 总下注额
            balance = normalize_fraction(usercoin.balance, coin_accuracy)  # 总下注额
            usercoin.balance = balance - coins  # 用户余额表减下注额
            usercoin.save()
            lock_coin = normalize_fraction(give_coin.lock_coin, coin_accuracy)
            if lock_coin != float(0) and coins > lock_coin:
                coins_give = coins - lock_coin  # 正常币下注额

                record = Record()  # 正常币记录
                record.user = user
                record.quiz = quiz
                record.roomquiz_id = roomquiz_id
                record.rule_id = rule_id
                record.option = option_odds
                record.bet = coins_give
                record.odds = option_odds.odds
                record.save()
                earn_coins = coins_give * option_odds.odds
                earn_coins_one = normalize_fraction(earn_coins, coin_accuracy)

                record = Record()  # 赠送币记录
                record.user = user
                record.quiz = quiz
                record.roomquiz_id = roomquiz_id
                record.rule_id = rule_id
                record.option = option_odds
                record.source = 2
                record.bet = lock_coin
                record.odds = option_odds.odds
                record.save()
                earn_coins = lock_coin * option_odds.odds
                earn_coins_two = normalize_fraction(earn_coins, coin_accuracy)

                give_coin.lock_coin -= lock_coin
                give_coin.save()

                earn_coins = earn_coins_one + earn_coins_two
            elif coins < lock_coin or coins == lock_coin:
                record = Record()  # 赠送币记录
                record.user = user
                record.quiz = quiz
                record.roomquiz_id = roomquiz_id
                record.rule_id = rule_id
                record.option = option_odds
                record.source = 2
                record.bet = coins
                record.odds = option_odds.odds
                record.save()
                earn_coins = coins * option_odds.odds
                earn_coins = normalize_fraction(earn_coins, coin_accuracy)

                give_coin.lock_coin -= coins
                give_coin.save()
            else:
                record = Record()  # 充值币记录
                record.user = user
                record.quiz = quiz
                record.roomquiz_id = roomquiz_id
                record.rule_id = rule_id
                record.option = option_odds
                record.bet = coins
                record.odds = option_odds.odds
                record.save()
                earn_coins = coins * option_odds.odds
                earn_coins = normalize_fraction(earn_coins, coin_accuracy)
        else:
            coins = normalize_fraction(coins, coin_accuracy)  # 总下注额
            record = Record()
            record.user = user
            record.quiz = quiz
            record.roomquiz_id = roomquiz_id
            record.rule_id = rule_id
            record.option = option_odds
            record.bet = coins
            record.odds = option_odds.odds
            if int(option_odds.option.rule.type) == Rule.AISA_RESULTS:
                record.handicap = option_odds.option.rule.handicap
            record.save()
            earn_coins = coins * option_odds.odds
            earn_coins = normalize_fraction(earn_coins, coin_accuracy)
            # 用户减少金币
            balance = normalize_fraction(usercoin.balance, coin_accuracy)
            usercoin.balance = balance - coins
            usercoin.save()
            quiz.total_people += 1
            quiz.save()

        coin_detail = CoinDetail()
        coin_detail.user = user
        coin_detail.coin_name = usercoin.coin.name
        coin_detail.amount = '-' + str(coins)
        coin_detail.rest = usercoin.balance
        coin_detail.sources = 3
        coin_detail.save()

        # 更新俱乐部对应竞猜投注的数据
        Record.objects.update_club_quiz_bet_data(quiz_id=quiz.id, club_id=roomquiz_id, user_id=user.id)

        response = {
            'code': 0,
            'data': {
                'message': '下注成功，金额总数为 ' + str(
                    normalize_fraction(coins, int(usercoin.coin.coin_accuracy))) + '，预计可得猜币 ' + str(
                    normalize_fraction(earn_coins, int(usercoin.coin.coin_accuracy))),
                'balance': normalize_fraction(usercoin.balance, int(usercoin.coin.coin_accuracy))
            }
        }
        return self.response(response)


class RecommendView(ListAPIView):
    """
    竞猜推荐
    """
    permission_classes = (LoginRequired,)
    serializer_class = QuizSerialize

    def get_queryset(self):
        return Quiz.objects.filter(status__lt=2, is_delete=False).order_by('-total_people')[:20]

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for item in items:
            data.append(
                {
                    "quiz_id": item['id'],
                    "match": item['host_team'] + " VS " + item['guest_team'],
                    "match_time": datetime.strftime(datetime.fromtimestamp(item['begin_at']), '%H:%M')
                }
            )
        return self.response({"code": 0, "data": data})


class WorldCup(ListAPIView):
    """
    世界杯列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = QuizSerialize

    def get_queryset(self):
        if int(self.request.GET.get('type')) == 1:  # 未开始
            list = Quiz.objects.filter(Q(status=0) | Q(status=1) | Q(status=2), category_id=873,
                                       is_delete=False).order_by('begin_at')
            return list
        elif int(self.request.GET.get('type')) == 2:  # 已结束
            list = Quiz.objects.filter(Q(status=3) | Q(status=4) | Q(status=5), category_id=873,
                                       is_delete=False).order_by('-begin_at')
            return list

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        value = results.data.get('results')
        time = 0
        return self.response({"code": 0, "data": value, 'time': time})


class ProfitView(ListAPIView):
    """
    俱乐部收益
    """
    serializer_class = ClubProfitAbroadSerialize

    def get_queryset(self):
        days = self.request.GET.get('days')
        type = self.request.GET.get('type')
        date_last = (datetime.now() - timedelta(days=int(days))).strftime('%Y-%m-%d')
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start_time = str(date_last) + ' 00:00:00'  # 开始时间
        if 'start_time' in self.request.GET:
            start_time = self.request.GET.get('start_time')
        if 'end_time' in self.request.GET:
            if 'start_time' not in self.request.GET:
                start_time = '2018-06-01 00:30:00'
            end_time = self.request.GET.get('end_time')
            end_time = str(end_time) + ' 23:59:59'
        end_time_all = str(
            (datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')).strftime('%Y-%m-%d')) + ' 00:30:00'  # 开始时间
        CLUB_PROFIT_DATA = "club_profit_" + str(start_time) + '_' + str(end_time_all) + "_data_" + str(type)  # key
        CLUB_PROFIT_NAME = "club_profit_" + str(start_time) + '_' + str(end_time_all) + "_name_" + str(type)  # key
        data = get_cache(CLUB_PROFIT_DATA)
        name = get_cache(CLUB_PROFIT_NAME)
        if data is None or name is None:
            lists = ClubProfitAbroad.objects.filter(Q(created_at__gte=start_time, created_at__lte=end_time)).order_by(
                'created_at', '-virtual_profit')
        else:
            lists = []
        return lists

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        days = self.request.GET.get('days')
        date_last = (datetime.now() - timedelta(days=int(days))).strftime('%Y-%m-%d')
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start_time = str(date_last) + ' 00:00:00'  # 开始时间
        type = self.request.GET.get('type')
        if 'start_time' in self.request.GET:
            start_time = self.request.GET.get('start_time')
        if 'end_time' in self.request.GET:
            if 'start_time' not in self.request.GET:
                start_time = '2018-06-01 00:30:00'
            end_time = self.request.GET.get('end_time')
            end_time = str(end_time) + ' 23:59:59'
        end_time_all = str(
            (datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')).strftime('%Y-%m-%d')) + ' 00:30:00'  # 开始时间
        CLUB_PROFIT_DATA = "club_profit_" + str(start_time) + '_' + str(end_time_all) + "_data_" + str(type)  # key
        CLUB_PROFIT_NAME = "club_profit_" + str(start_time) + '_' + str(end_time_all) + "_name_" + str(type)  # key
        data = get_cache(CLUB_PROFIT_DATA)
        name = get_cache(CLUB_PROFIT_NAME)
        if data is None or name is None:
            print("我的天，竟然没有放进缓存")
            name = []
            sums = []
            sql = "SELECT uc.`name`, sum( cpb.virtual_profit ) AS sum_total FROM quiz_clubprofitabroad cpb "
            sql += "LEFT JOIN chat_club c on cpb.roomquiz_id = c.id LEFT JOIN users_coin uc on uc.id = c.coin_id "
            sql += "WHERE cpb.created_at>='" + start_time + "' AND cpb.created_at<='" + end_time + "' and c.is_recommend!=0 "
            sql += "GROUP BY uc.`name` ORDER BY sum_total desc limit 0" + "," + str(type) + ";"
            coins = get_sql(sql)
            for club_coin in coins:
                name.append(club_coin[0])
                sums.append(club_coin[1])
            data = {}
            for item in items:
                if item['coin_name'] in name:
                    date_key = item['coin_name']
                    if date_key not in data:
                        data[date_key] = {}
                        data[date_key]["icon"] = ''
                        data[date_key]["type"] = []
                        data[date_key]["sum"] = 0
                        data[date_key]["total"] = []
                        data[date_key]['created_at'] = []
                if item['coin_name'] in name:
                    profit_total = float(item["virtual_profit"])
                    if profit_total < 0:
                        type = 1
                    else:
                        type = 0
                    data[item['coin_name']]["icon"] = item["coin_icon"]
                    data[item['coin_name']]["type"].append(type)
                    data[item['coin_name']]["sum"] += normalize_fraction(1, 2)
                    data[item['coin_name']]["total"].append(normalize_fraction(item["virtual_profit"], 7))
                    data[item['coin_name']]['created_at'].append(item["created_at"])
            for club_info in coins:
                data[str(club_info[0])]["sum"] = club_info[1]
            CLUB_PROFIT_DATA = "club_profit_" + str(start_time) + '_' + str(end_time_all) + "_data"  # key
            CLUB_PROFIT_NAME = "club_profit_" + str(start_time) + '_' + str(end_time_all) + "_name"  # key
            set_cache(CLUB_PROFIT_DATA, data)
            set_cache(CLUB_PROFIT_NAME, name)
        return self.response({'code': 0, 'data': data, 'name': name})


class ChangeDate(ListAPIView):
    """
    兑换页面时间轴
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        days = int(settings.GSG_EXCHANGE_DATE)
        gsg_exchange_date = settings.GSG_EXCHANGE_START_DATE
        start_date = datetime.strptime(gsg_exchange_date, "%Y-%m-%d %H:%M:%S")
        day = 0
        data = []
        if day != days:
            data = time_data(start_date, day, data, days)
        return self.response({'code': 0, 'data': data})


class Change(ListAPIView):
    """
    兑换主页面
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        sql = "select a.name, a.icon from users_coin a"
        sql += " where id=2 or id=6"
        coin = get_sql(sql)  # gsg
        gsg = coin[1]
        eth = coin[0]

        sql = "SELECT v.value FROM quiz_gsgvalue v"
        sql += " where v.house = 'debi'"
        sql += " and v.coin_id = 6"
        sql += "  ORDER BY v.created_at DESC limit 1"
        # gsg_list = get_sql(sql)    # gsg价格列表
        # print("gsg_list====================================", gsg_list)
        gsg_values = get_sql(sql)[0][0]    # gsg价格

        sql = "select a.price from users_coinprice a"
        sql += " where coin_name='ETH'"
        sql += " and a.platform_name!=''"
        eth_vlue = get_sql(sql)[0][0]  # ETH 价格
        # gsg_value = Decimal(0.3)
        gsg_value = gsg_values*eth_vlue
        convert_ratio = int(eth_vlue / gsg_value)  # 1 ETH 换多少 GSG
        toplimit = Decimal(100000000 / 50)  # 一天容许兑换的总数

        day = datetime.now().strftime('%Y-%m-%d')
        if 'days' in self.request.GET:
            day = self.request.GET.get('days')
        start_time = str(day) + ' 00:00:00'  # 开始时间
        end_time = str(day) + ' 23:59:59'  # 结束时间

        gsg_exchange_date = settings.GSG_EXCHANGE_START_DATE
        gsg_exchange_date_all = datetime.strptime(gsg_exchange_date, "%Y-%m-%d %H:%M:%S")
        date_last_all = (gsg_exchange_date_all + timedelta(days=50)).strftime('%Y-%m-%d')
        end_time_all = str(date_last_all) + ' 23:59:59'  # 结束时间
        if day > end_time_all:
            start_time = str(date_last_all) + ' 00:00:00'  # 开始时间
            end_time = str(date_last_all) + ' 23:59:59'  # 结束时间
        if day < gsg_exchange_date:
            start_time = gsg_exchange_date  # 开始时间
            end_time_a = datetime.strptime(gsg_exchange_date, "%Y-%m-%d %H:%M:%S")
            end_time = str(end_time_a) + ' 23:59:59'  # 开始时间

        sql = "select sum(a.change_gsg_value) from quiz_changerecord a"
        sql += " where created_at>= '" + start_time + "'"
        sql += " and a.created_at<= '" + end_time + "'"
        is_use = get_sql(sql)[0][0]  # 已经兑换了多少GSG
        if is_use == None or is_use == 0:
            ratio = 0
        else:
            ratio = is_use / toplimit  # 兑换了的GSG占天当总数的百分比

        sql = "select count(distinct a.user_id) from quiz_changerecord a"
        sql += " where created_at>= '" + start_time + "'"
        sql += " and a.created_at<= '" + end_time + "'"
        numbers = get_sql(sql)[0][0]  # 兑换总人数
        return self.response({'code': 0, "data": {
            "convert_ratio": convert_ratio,
            "toplimit": toplimit,
            "ratio": ratio,
            "numbers": numbers,
            "coin_one": str(1) + " " + eth[0],
            "coin_icon_one": eth[1],
            "coin_two": str(convert_ratio) + " " + gsg[0],
            "coin_icon_two": gsg[1]
        }})


class ChangeGsg(ListAPIView):
    """
    点击兑换
    """
    permission_classes = (LoginRequired,)

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        user_id = str(request.user.id)
        value = value_judge(request, "wager", "convert_ratio")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)

        day = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        EXCHANGE_QUALIFICATION = "exchange_qualification_" + user_id + '_' + str(day)  # key
        number = get_cache(EXCHANGE_QUALIFICATION)
        if number == None or number == '':
            everydayinjection = EveryDayInjectionValue.objects.filter(user_id=int(user_id), injection_time=yesterday)
            if len(everydayinjection) <= 0:
                raise ParamErrorException(error_code.API_70208_NO_REDEMPTION)  # 有没有兑换资格
            else:
                number = everydayinjection[0].order
        if int(number) < 1000:
            raise ParamErrorException(error_code.API_70208_NO_REDEMPTION)  # 有没有兑换资格

        gsg_exchange_date = settings.GSG_EXCHANGE_START_DATE
        gsg_exchange_date_all = datetime.strptime(gsg_exchange_date, "%Y-%m-%d %H:%M:%S")
        date_last_all = (gsg_exchange_date_all + timedelta(days=50)).strftime('%Y-%m-%d')
        end_time_all = str(date_last_all) + ' 23:59:59'  # 结束时间
        if day > end_time_all:
            raise ParamErrorException(error_code.API_408_ACTIVITY_ENDS)  # 活动已结束
        if day < gsg_exchange_date:
            raise ParamErrorException(error_code.API_407_ACTIVITY_HAS_NOT_STARTED)  # 活动未开始

        coins = float(self.request.data['wager'])  # 获取兑换ETH
        coin_astrict = float(0.01)
        if coins < coin_astrict:
            raise ParamErrorException(error_code.API_70204_ETH_UNQUALIFIED_CONVERTIBILITY)  # 判断兑换值是否大于0.01

        toplimit = Decimal(100000000 / 50)  # 一天容许兑换的总数
        day = datetime.now().strftime('%Y-%m-%d')
        start_time = str(day) + ' 00:00:00'  # 开始时间
        end_time = str(day) + ' 23:59:59'  # 开始时间
        sql = "select sum(a.change_gsg_value) from quiz_changerecord a"
        sql += " where a.created_at>= '" + start_time + "'"
        sql += " and a.created_at<= '" + end_time + "'" + " for update"
        is_use = get_sql(sql)[0][0]  # 已经兑换了多少GSG
        if is_use == None or is_use == '':
            is_use = 0
        left_gsg = toplimit - is_use

        sql = "select sum(a.change_eth_value) from quiz_changerecord a"
        sql += " where a.created_at>= '" + start_time + "'"
        sql += " and a.created_at<= '" + end_time + "'"
        sql += " and a.user_id=" + user_id
        has_user_change = get_sql(sql)[0][0]  # 用户当天已经兑换了多少GSG
        if has_user_change == None or has_user_change == '':
            has_user_change = 0
        user_change = Decimal(coins) + has_user_change
        if user_change > 5:
            raise ParamErrorException(error_code.API_70207_REACH_THE_UPPER_LIMIT)  # 判断用户兑换是否超过5个ETH

        convert_ratio = float(self.request.data['convert_ratio'])  # 获取兑换比例

        sql = "select a.balance from users_usercoin a"
        sql += " where a.coin_id=2"
        sql += " and a.user_id=" + user_id
        eth_balance = get_sql(sql)[0][0]  # 用户拥有的ETH
        if eth_balance < coins:
            raise ParamErrorException(error_code.API_70205_ETH_NOT_SUFFICIENT_FUNDS)  # 判断用户ETH余额是否足

        gsg_ratio = convert_ratio * coins
        if left_gsg < gsg_ratio:
            raise ParamErrorException(error_code.API_70206_CONVERTIBLE_GSG_INSUFFICIENT)  # 判断是否有足够GSG供用户兑换

        change_record = ChangeRecord()
        change_record.user = request.user
        change_record.change_eth_value = Decimal(coins)
        change_record.change_gsg_value = Decimal(gsg_ratio)
        change_record.is_robot = request.user.is_robot
        change_record.save()

        user_coin_gsg = UserCoin.objects.get(user_id=request.user.id, coin_id=6)
        user_coin_gsg.balance += Decimal(gsg_ratio)
        user_coin_gsg.save()
        coin_detail = CoinDetail()
        coin_detail.user = request.user
        coin_detail.coin_name = user_coin_gsg.coin.name
        coin_detail.amount = '+' + str(gsg_ratio)
        coin_detail.rest = user_coin_gsg.balance
        coin_detail.sources = 13
        coin_detail.save()

        user_coin_ETH = UserCoin.objects.get(user_id=request.user.id, coin_id=2)
        user_coin_ETH.balance -= Decimal(coins)
        user_coin_ETH.save()
        coin_detail = CoinDetail()
        coin_detail.user = request.user
        coin_detail.coin_name = user_coin_ETH.coin.name
        coin_detail.amount = '-' + str(coins)
        coin_detail.rest = user_coin_ETH.balance
        coin_detail.sources = 13
        coin_detail.save()

        content = {'code': 0, 'user_coin_ETH': normalize_fraction(user_coin_ETH.balance, 4)}
        return self.response(content)


class ChangeTable(ListAPIView):
    """
    点击兑换页面
    """

    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        user_id = str(request.user.id)
        day = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        EXCHANGE_QUALIFICATION = "exchange_qualification_" + user_id + '_' + str(day)  # key
        number = get_cache(EXCHANGE_QUALIFICATION)
        if number == None or number == '':
            everydayinjection = EveryDayInjectionValue.objects.filter(user_id=int(user_id), injection_time=yesterday)
            if len(everydayinjection) <= 0:
                number = 100000
            else:
                number = everydayinjection[0].order
        if int(number) <= 1000:
            is_right = 1
        else:
            is_right = 0
        GSG_ICON = "gsg_icon_in_cache"  # key
        gsg_icon = get_cache(GSG_ICON)
        if gsg_icon is None:
            gsg_info = Coin.objects.get(id=6)
            gsg_icon = gsg_info.icon
        sql = "select a.balance, c.icon from users_usercoin a LEFT JOIN users_coin c on c.id = a.coin_id"
        sql += " where a.coin_id=2"
        sql += " and a.user_id=" + user_id
        eth_icon = get_sql(sql)[0][1]
        eth_balance = normalize_fraction(get_sql(sql)[0][0], 3)  # 用户拥有的ETH
        eth_limit = settings.ETH_ONCE_EXCHANGE_LOWER_LIMIT
        eth_exchange_instruction_one = settings.ETH_EXCHANGE_INSTRUCTION_ONE
        eth_exchange_instruction_two = settings.ETH_EXCHANGE_INSTRUCTION_TWO
        eth_exchange_instruction_three = settings.ETH_EXCHANGE_INSTRUCTION_THREE
        eth_exchange_instruction_four = settings.ETH_EXCHANGE_INSTRUCTION_ONE_FOUR
        return self.response({'code': 0, 'is_right': is_right, "data": {
            "eth_limit": eth_limit,
            "eth_balance": eth_balance,
            "eth_icon": eth_icon,
            "gsg_icon": gsg_icon,
            "eth_exchange_instruction_one": eth_exchange_instruction_one,
            "eth_exchange_instruction_two": eth_exchange_instruction_two,
            "eth_exchange_instruction_three": eth_exchange_instruction_three,
            "eth_exchange_instruction_four": eth_exchange_instruction_four
        }})


class PlatformList(ListAPIView):
    """
    GSG交易所列表
    """

    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        sql = "select house from quiz_gsgvalue a group by house;"
        price_list = get_sql(sql)  # 交易所列表
        data = []
        for price in price_list:
            if price[0] == 'debi':
                data.append(price[0])
            else:
                pass
        return self.response({'code': 0, "data": data})


class GsgPrice(ListAPIView):
    """
    GSG价格曲线图
    """

    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        if 'house' not in self.request.GET:
            sql = "select house from quiz_gsgvalue a group by house;"
            price_list = get_sql(sql)  # 用户拥有的ETH
            if len(price_list) <= 0:
                raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)
            house = price_list[0][0]
            house = 'debi'
        else:
            house = self.request.GET.get('house')
        sql = "select date_format(a.created_at, '%m/%d') as date, date_format(a.created_at, '%Y-%m-%d') as date, avg(value)  as price from quiz_gsgvalue a"
        sql += " where a.coin_id = 6"
        sql += " and a.house= '" + house + "'" + "group by date;"
        price_list = get_sql(sql)
        data = []
        for price in price_list:
            data.append({
                "created_at": price[0],
                "created_at_new": price[1],
                "gsg_value": price[2],
                "eth_value": "暂无数据",
                "market_value": "暂无数据",
                "Volume": "暂无数据"
            })
        return self.response({'code': 0, "data": data})


class ChangeRemainder(ListAPIView):
    """
    兑换检测
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        user_id = str(request.user.id)

        day = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        EXCHANGE_QUALIFICATION = "exchange_qualification_" + user_id + '_' + str(day)  # key
        number = get_cache(EXCHANGE_QUALIFICATION)
        if number == None or number == '':
            everydayinjection = EveryDayInjectionValue.objects.filter(user_id=int(user_id), injection_time=yesterday)
            if len(everydayinjection) <= 0:
                raise ParamErrorException(error_code.API_70208_NO_REDEMPTION)  # 有没有兑换资格
            else:
                number = everydayinjection[0].order
        if int(number) < 1000:
            raise ParamErrorException(error_code.API_70208_NO_REDEMPTION)  # 有没有兑换资格

        gsg_exchange_date = settings.GSG_EXCHANGE_START_DATE
        gsg_exchange_date_all = datetime.strptime(gsg_exchange_date, "%Y-%m-%d %H:%M:%S")
        date_last_all = (gsg_exchange_date_all + timedelta(days=50)).strftime('%Y-%m-%d')
        end_time_all = str(date_last_all) + ' 23:59:59'  # 结束时间
        if day > end_time_all:
            raise ParamErrorException(error_code.API_408_ACTIVITY_ENDS)  # 活动已结束
        if day < gsg_exchange_date:
            raise ParamErrorException(error_code.API_407_ACTIVITY_HAS_NOT_STARTED)  # 活动未开始

        coins = float(self.request.GET.get('wager'))  # 获取兑换ETH
        coin_astrict = float(0.01)
        if coins < coin_astrict:
            raise ParamErrorException(error_code.API_70204_ETH_UNQUALIFIED_CONVERTIBILITY)  # 判断兑换值是否大于0.01

        toplimit = Decimal(100000000 / 50)  # 一天容许兑换的总数
        day = datetime.now().strftime('%Y-%m-%d')
        start_time = str(day) + ' 00:00:00'  # 开始时间
        end_time = str(day) + ' 23:59:59'  # 开始时间
        sql = "select sum(a.change_gsg_value) from quiz_changerecord a"
        sql += " where a.created_at>= '" + start_time + "'"
        sql += " and a.created_at<= '" + end_time + "'" + " for update"
        is_use = get_sql(sql)[0][0]  # 已经兑换了多少GSG
        if is_use == None or is_use == '':
            is_use = 0
        left_gsg = toplimit - is_use

        sql = "select sum(a.change_eth_value) from quiz_changerecord a"
        sql += " where a.created_at>= '" + start_time + "'"
        sql += " and a.created_at<= '" + end_time + "'"
        sql += " and a.user_id=" + user_id
        has_user_change = get_sql(sql)[0][0]  # 用户当天已经兑换了多少GSG
        if has_user_change == None or has_user_change == '':
            has_user_change = 0
        user_change = Decimal(coins) + has_user_change
        if user_change > 5:
            raise ParamErrorException(error_code.API_70207_REACH_THE_UPPER_LIMIT)  # 判断用户兑换是否超过5个ETH

        convert_ratio = float(self.request.GET.get('convert_ratio'))  # 获取兑换比例

        sql = "select a.balance from users_usercoin a"
        sql += " where a.coin_id=2"
        sql += " and a.user_id=" + user_id
        eth_balance = get_sql(sql)[0][0]  # 用户拥有的ETH
        if eth_balance < coins:
            raise ParamErrorException(error_code.API_70205_ETH_NOT_SUFFICIENT_FUNDS)  # 判断用户ETH余额是否足

        gsg_ratio = convert_ratio * coins

        if left_gsg < gsg_ratio:
            coin_number = left_gsg / convert_ratio
        else:
            coin_number = coins

        return self.response({'code': 0, "coin_number": coin_number})
