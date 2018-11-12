# -*- coding: UTF-8 -*-
from django.db import transaction
from base.app import ListAPIView, ListCreateAPIView
from base.function import LoginRequired
from base.exceptions import ParamErrorException
from base import code as error_code
from .serializers_pk import *
from guess.models import (StockPk, Issues, PlayStockPk, OptionStockPk,
                          RecordStockPk, BetLimit, Index, Periods)
import datetime
import time
from utils.functions import get_club_info, normalize_fraction, value_judge, handle_zero, to_decimal
from utils.cache import get_cache, set_cache
from users.models import UserCoin, CoinDetail, User, RecordMark
from spider.management.commands.stock_index import market_rest_cn_list
from promotion.models import PromotionRecord
from chat.models import Club
from decimal import Decimal
from django.db.models import Sum
from users.models import Coin


class StockPkDetail(ListAPIView):
    """
    股指pk详情
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        # 正常status
        status = 0
        switch_time = ''
        open_market_time = ''
        time_now = datetime.datetime.now()
        # stock_pk_id_list = StockPk.objects.all().values_list('id', flat=True)
        issue_last = Issues.objects.filter(open__gt=time_now).order_by('open').first()
        if issue_last.issue == 1:
            issue_pre = Issues.objects.filter(open__lt=time_now).order_by('-open').first()
            if (issue_pre.open + datetime.timedelta(hours=1)) > time_now:
                qs = issue_pre
                #  一小时切换status, 4: 中to美, 5: 美to中
                switch_time = qs.open + datetime.timedelta(hours=1)
                switch_time = time.mktime(switch_time.timetuple()) - time.time()
                switch_time = int(switch_time)
                if issue_pre.stock_pk_id == 1:
                    status = 4
                else:
                    status = 5
            else:
                qs = issue_last
                # 休市
                if qs.stock_pk_id == 1:
                    open_time = qs.open
                else:
                    open_time = qs.open - datetime.timedelta(hours=12)
                before_open_time = open_time - datetime.timedelta(days=1)
                if before_open_time.isoweekday() > 5 or \
                        before_open_time.strftime('%Y-%m-%d') in market_rest_cn_list:
                    status = 3
                # 平日休市
                else:
                    if time_now > qs.open:
                        status = 0
                    else:
                        status = 6
                open_market_time = qs.open - datetime.timedelta(minutes=5)
                open_market_time = time.mktime(open_market_time.timetuple()) - time.time()
                open_market_time = int(open_market_time)
        else:
            qs = issue_last
            # 中场休息status
            if qs.open.strftime('%H:%M:%S') == '13:05:00':
                if time_now < qs.open - datetime.timedelta(minutes=5):
                    status = 1
                else:
                    status = 0
        return qs, {'status': status, 'switch_time': switch_time, 'open_market_time': open_market_time}

    def list(self, request, *args, **kwargs):
        club_id = int(self.request.GET.get('club_id'))  # 俱乐部表ID
        user = request.user

        issues, status_dic = self.get_queryset()
        time_now = datetime.datetime.now()
        stock_pk_id = issues.stock_pk_id

        left_periods_id = issues.left_periods_id
        right_periods_id = issues.right_periods_id

        left_index_value = issues.left_stock_index
        right_index_value = issues.right_stock_index
        if left_index_value == 0:
            left_index = Index.objects.filter(periods_id=left_periods_id).order_by(
                '-index_time').first()
            if left_index is not None:
                left_index_value = left_index.index_value

            right_index = Index.objects.filter(periods_id=right_periods_id).order_by(
                '-index_time').first()
            if right_index is not None:
                right_index_value = right_index.index_value

        if issues.issue == 1:
            issue_pre = Issues.objects.filter(stock_pk_id=stock_pk_id, open__lt=time_now).order_by('-open').first()
            left_index_value = issue_pre.left_stock_index
            right_index_value = issue_pre.right_stock_index

            left_periods_id = issue_pre.left_periods_id
            right_periods_id = issue_pre.right_periods_id

        periods_obj_dic = {}
        for periods in Periods.objects.filter(id__in=[left_periods_id, right_periods_id]):
            periods_obj_dic.update({
                periods.id: {
                    'start_value': periods.start_value,
                }
            })
        # color 1: 涨, 2: 跌, 3: 平
        left_start_value = periods_obj_dic[left_periods_id]['start_value']
        if left_index_value > left_start_value:
            left_index_color = 1
        elif left_index_value < left_start_value:
            left_index_color = 2
        else:
            left_index_color = 3

        right_start_value = periods_obj_dic[right_periods_id]['start_value']
        if right_index_value > right_start_value:
            right_index_color = 1
        elif right_index_value < right_start_value:
            right_index_color = 2
        else:
            right_index_color = 3

        issues_id = issues.id
        issue = issues.issue
        open_time = issues.open.strftime('%Y-%m-%d %H:%M:%S')
        open_timestamp = time.mktime(issues.open.timetuple()) - time.time()
        open_timestamp = int(open_timestamp)

        if status_dic['status'] == 1 or status_dic['status'] == 6:
            open_timestamp = time.mktime((issues.open - datetime.timedelta(minutes=5)).timetuple()) - time.time()
            open_timestamp = int(open_timestamp)

        # 用户余额，对应币信息
        cache_club_value = get_club_info()
        coin_id = cache_club_value[club_id]['coin_id']
        coin_accuracy = cache_club_value[club_id]['coin_accuracy']
        user_coin = UserCoin.objects.get(user_id=user.id, coin_id=coin_id)
        coin_icon = cache_club_value[club_id]['coin_icon']
        coin_name = cache_club_value[club_id]['coin_name']
        balance = normalize_fraction(user_coin.balance, int(coin_accuracy))  # 用户余额
        coin_dic = {
            'balance': balance, 'coin_name': coin_name, 'coin_icon': coin_icon,
        }

        # stock_pk
        stock_pk_dic = {}
        for stock_pk in StockPk.objects.all():
            stock_pk_dic.update({
                stock_pk.id: {
                    'left_stock_name': stock_pk.left_stock_name,
                    'right_stock_name': stock_pk.right_stock_name,
                }
            })
        left_stock_name = stock_pk_dic[stock_pk_id]['left_stock_name']
        right_stock_name = stock_pk_dic[stock_pk_id]['right_stock_name']

        # 获取 bet_limit, 共用旧股指玩法的限制指数
        bet_limit_dic = {}  # {play_id: bet_limit obj}
        for bet_limit in BetLimit.objects.filter(club_id=club_id, play_id=1):
            bet_limit_dic.update({
                'bets_one': bet_limit.bets_one,
                'bets_two': bet_limit.bets_two,
                'bets_three': bet_limit.bets_three,
                'bets_min': bet_limit.bets_min,
                'bets_max': bet_limit.bets_max,
            })

        # 获取玩法
        plays_dic = {}
        for play in PlayStockPk.objects.all():
            play_name = PlayStockPk.PLAY[int(play.play_name)][1]
            tips = play.tips
            if self.request.GET.get('language') == 'en':
                play_name = PlayStockPk.PLAY_EN[int(play.play_name_en)][1]
                tips = play.tips_en
            plays_dic.update({
                play.id: {
                    'play_name': play_name, 'tips': tips,
                }
            })

        # 投注情况
        user_options_list = RecordStockPk.objects.filter(user_id=user.pk, issue_id=issues.id, club_id=club_id,
                                                         play_id__in=plays_dic).values_list('option_id', flat=True)
        # record_dic = {}
        # for record in RecordStockPk.objects.filter(issue_id=issues.id, club_id=club_id, play_id__in=plays_dic.keys()):
        #     record_dic.update({
        #         record.id: {
        #             'user_id': record.user_id, 'option_id': record.option_id
        #         }
        #     })

        # 获取选项
        options_dic = {}
        for key, value in plays_dic.items():
            options_dic.update({key: []})

        # 从缓存拿出各个选项的投注人数，计算各个支持率
        key_pk_bet_count = 'record_pk_bet_count' + '_' + str(issues.stock_pk_id)
        pk_bet_count = get_cache(key_pk_bet_count)

        pk_bet_rate = {}
        rate = 0
        list_item = list(pk_bet_count[issues.id].items())
        bet_num_sum = sum(pk_bet_count[issues.id].values())
        for option_id, option_bet_num in list_item[:-1]:
            support_rate = 0
            if bet_num_sum != 0:
                support_rate = round(option_bet_num / bet_num_sum * 100, 2)
            pk_bet_rate.update({option_id: support_rate})
            rate += to_decimal(support_rate)
        if bet_num_sum != 0:
            pk_bet_rate.update({list_item[-1][0]: to_decimal(100) - rate})
        else:
            pk_bet_rate.update({list_item[-1][0]: 0})

        for option in OptionStockPk.objects.filter(stock_pk_id=stock_pk_id).order_by('order'):
            is_choice = 0
            if option.pk in user_options_list:
                is_choice = 1  # 是否已选

            support_rate = pk_bet_rate[option.id]  # 支持率

            title = option.title
            if self.request.GET.get('language') == 'en':
                title = option.title_en
            options_dic[option.play_id].append({
                'option_id': option.id, 'title': title, 'odds': handle_zero(option.odds),
                'is_choice': is_choice, 'support_rate': support_rate,
            })

        # 构造玩法选项
        for key, value in plays_dic.items():
            value['options'] = options_dic[key]

        data = {
            'stock_pk_id': stock_pk_id,
            'status': status_dic['status'],
            'switch_time': status_dic['switch_time'],

            'left_stock_name': left_stock_name,
            'left_periods_id': left_periods_id,
            'left_index_value': left_index_value,
            'left_index_color': left_index_color,

            'right_stock_name': right_stock_name,
            'right_periods_id': right_periods_id,
            'right_index_value': right_index_value,
            'right_index_color': right_index_color,

            'bet_limit': bet_limit_dic,
            'plays_options': plays_dic,
            'issue': issue,
            'issues_id': issues_id,
            'open_time': open_time,
            'open_timestamp': open_timestamp,
            'coin_dic': coin_dic,
        }
        return self.response({'code': 0, 'data': data})


class StockPkResultList(ListAPIView):
    """
    股指pk开奖记录
    """
    permission_classes = (LoginRequired,)
    serializer_class = StockPkResultListSerialize

    def get_queryset(self):
        time_now = datetime.datetime.now()
        # stock_pk_id_list = StockPk.objects.all().values_list('id', flat=True)
        issues = Issues.objects.filter(open__gt=time_now).order_by('open').first()
        stock_pk_id = issues.stock_pk_id

        if issues.issue != 1:
            left_periods_id = issues.left_periods_id
            right_periods_id = issues.right_periods_id
        else:
            issue_pre = Issues.objects.filter(open__lt=time_now).order_by('-open').first()
            if (issue_pre.open + datetime.timedelta(hours=1)) > time_now:
                stock_pk_id = issue_pre.stock_pk_id
                left_periods_id = issue_pre.left_periods_id
                right_periods_id = issue_pre.right_periods_id
            else:
                issues_pre_two = Issues.objects.filter(stock_pk_id=stock_pk_id,
                                                       open__lt=time_now).order_by('-open').first()
                stock_pk_id = issues_pre_two.stock_pk_id
                left_periods_id = issues_pre_two.left_periods_id
                right_periods_id = issues_pre_two.right_periods_id

        qs = Issues.objects.filter(stock_pk_id=stock_pk_id, result_confirm=3,
                                   left_periods_id=left_periods_id, right_periods_id=right_periods_id)
        return qs

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')

        stock_pk_dic = {}
        for stock_pk in StockPk.objects.all():
            stock_pk_dic.update({
                stock_pk.id: {
                    'left_stock_name': stock_pk.left_stock_name,
                    'right_stock_name': stock_pk.right_stock_name,
                }
            })

        result_flag = {
            '和': 0, '上证大': 1, '深证大': 2, '纳斯达克大': 3, '道琼斯大': 4,
        }
        data = []
        for item in items:
            left_stock_name = stock_pk_dic[item['stock_pk_id']]['left_stock_name']
            right_stock_name = stock_pk_dic[item['stock_pk_id']]['right_stock_name']

            data.append({
                'issue': item['issue'],
                'open_time': item['open_time'],

                'left_stock_name': left_stock_name,
                'left_index': item['left_stock_index'],
                'left_result_num': str(item['left_stock_index']).split('.')[1][1],

                'right_stock_name': right_stock_name,
                'right_index': item['right_stock_index'],
                'right_result_num': str(item['right_stock_index']).split('.')[1][1],

                'result_answer': item['size_pk_result'],
                'result_flag': result_flag[item['size_pk_result']]
            })
        return self.response({'code': 0, 'data': data})


class StockPkRecordsList(ListAPIView):
    """
    股指pk竞猜记录
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        if 'user_id' not in self.request.GET:
            user_id = self.request.user.id
        else:
            user_id = self.request.GET.get('user_id')

        is_end = int(self.request.GET.get('is_end'))
        if is_end == RecordStockPk.AWAIT:
            if "club_id" not in self.request.GET:
                qs = RecordStockPk.objects.filter(user_id=user_id, status=str(RecordStockPk.AWAIT))
            else:
                club_id = int(self.request.GET.get('club_id'))  # 俱乐部表ID
                qs = RecordStockPk.objects.filter(user_id=user_id, club_id=club_id, status=str(RecordStockPk.AWAIT))
        elif is_end == RecordStockPk.OPEN:
            if "club_id" not in self.request.GET:
                qs = RecordStockPk.objects.filter(user_id=user_id, status=str(RecordStockPk.OPEN))
            else:
                club_id = int(self.request.GET.get('club_id'))  # 俱乐部表ID
                qs = RecordStockPk.objects.filter(user_id=user_id, club_id=club_id, status=str(RecordStockPk.OPEN))
        else:
            if "club_id" not in self.request.GET:
                qs = RecordStockPk.objects.filter(user_id=user_id)
            else:
                club_id = int(self.request.GET.get('club_id'))  # 俱乐部表ID
                qs = RecordStockPk.objects.filter(user_id=user_id, club_id=club_id)
        return qs

    def list(self, request, *args, **kwargs):
        records_obj_dic = {}
        options_id_list = []
        issues_id_list = []

        cache_club_value = get_club_info()

        for record in self.paginate_queryset(self.get_queryset()):
            club_id = int(record.club.id)  # 俱乐部表ID

            coin_accuracy = cache_club_value[club_id]['coin_accuracy']
            coin_icon = cache_club_value[club_id]['coin_icon']
            coin_name = cache_club_value[club_id]['coin_name']

            if record.option_id not in options_id_list:
                options_id_list.append(record.option_id)
            if record.issue_id not in issues_id_list:
                issues_id_list.append(record.issue_id)
            records_obj_dic.update({
                record.id: {
                    'issues_id': record.issue_id, 'options_id': record.option_id, 'bets': record.bets,
                    'earn_coin': record.earn_coin, 'created_at': record.created_at, 'status': record.status,
                    'coin_accuracy': coin_accuracy, 'coin_icon': coin_icon, 'coin_name': coin_name
                }
            })

        # 处理期数
        issues_obj_dic = {}
        for issue in Issues.objects.filter(id__in=issues_id_list):
            issues_obj_dic.update({
                issue.id: {
                    'size_pk_result': issue.size_pk_result, 'issue': issue.issue,
                    'stock_pk_id': issue.stock_pk_id,
                }
            })

        # 处理选项
        options_obj_dic = {}
        for option in OptionStockPk.objects.filter(id__in=options_id_list):
            options_obj_dic.update({
                option.id: {
                    'play_id': option.play_id, 'title': option.title, 'title_en': option.title_en,
                }
            })

        # 处理stock_pk
        stock_pk_obj_dic = {}
        for stock_pk in StockPk.objects.all():
            stock_pk_obj_dic.update({
                stock_pk.id: {
                    'left_stock_name': stock_pk.left_stock_name,
                    'right_stock_name': stock_pk.right_stock_name,
                }
            })

        data = []
        last_date = ''
        for item_key, item_value in records_obj_dic.items():
            # 时间
            created_at = item_value['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            year = created_at.split(' ')[0].split('-')[0]
            date = created_at.split(' ')[0].split('-')[1] + '/' + created_at.split(' ')[0].split('-')[2]
            if last_date == year + ' ' + date:
                year = ''
                date = ''
            else:
                last_date = year + ' ' + date
            bet_time = created_at.split(' ')[1].split(':')[0] + ':' + created_at.split(' ')[1].split(':')[1]

            # earn_coin, is_right
            is_right = 0
            earn_coin = normalize_fraction(item_value['earn_coin'], int(item_value['coin_accuracy']))
            if int(item_value['status']) == RecordStockPk.AWAIT:
                record_type = 0
                earn_coin_result = '待开奖'
                if self.request.GET.get('language') == 'en':
                    earn_coin_result = 'Wait results'
            elif earn_coin < 0:
                record_type = 2
                is_right = 2
                earn_coin_result = '猜错'
                if self.request.GET.get('language') == 'en':
                    earn_coin_result = 'Guess wrong'
            else:
                record_type = 1
                is_right = 1
                earn_coin_result = '+' + handle_zero(earn_coin)

            # 选项
            options_id = item_value['options_id']
            my_option = options_obj_dic[options_id]['title']
            if self.request.GET.get('language') == 'en':
                my_option = options_obj_dic[options_id]['title_en']

            # 期数
            issues_id = item_value['issues_id']
            issue = issues_obj_dic[issues_id]['issue']
            result_answer = ''
            if issues_obj_dic[issues_id]['size_pk_result'] != '':
                result_answer = issues_obj_dic[issues_id]['size_pk_result']

            # title
            stock_pk_id = issues_obj_dic[issues_id]['stock_pk_id']
            left_stock_name = stock_pk_obj_dic[stock_pk_id]['left_stock_name']
            right_stock_name = stock_pk_obj_dic[stock_pk_id]['right_stock_name']
            title = left_stock_name + ' PK ' + right_stock_name

            if "user_id" not in request.GET:
                user_id = self.request.user.id
            else:
                user_id = self.request.GET.get("user_id")
            RecordMark.objects.update_record_mark(user_id, 6, 0)

            data.append({
                'id': item_key,
                'year': year,
                'date': date,
                'time': bet_time,
                'title': title,
                'type': record_type,
                'my_option': my_option,
                'is_right': is_right,
                'earn_coin': earn_coin_result,
                'coin_name': item_value['coin_name'],
                'coin_icon': item_value['coin_icon'],
                'issue': issue,
                'result_answer': result_answer,
                'bet': normalize_fraction(item_value['bets'], int(item_value['coin_accuracy'])),
            })
        return self.response({'code': 0, 'data': data})


class StockPkBet(ListCreateAPIView):
    """
    股指pk下注
    """
    permission_classes = (LoginRequired,)

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        value = value_judge(request, "issues", "stock_pk_id", "option_id", "play_id", "bet",
                            "club_id", "open_time")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        user = request.user
        issues = int(self.request.data.get('issues'))
        club_id = int(self.request.data.get('club_id'))
        play_id = int(self.request.data.get('play_id'))
        option_id = int(self.request.data.get('option_id'))
        bet = Decimal(self.request.data.get('bet'))
        stock_pk_id = int(self.request.data.get('stock_pk_id'))
        open_time = datetime.datetime.strptime(self.request.data.get('open_time'), '%Y-%m-%d %H:%M:%S')

        # 对应club币信息
        cache_club_value = get_club_info()
        coin_id = cache_club_value[club_id]['coin_id']
        coin_accuracy = cache_club_value[club_id]['coin_accuracy']

        # 判断选项ID是否有效
        try:
            option = OptionStockPk.objects.get(pk=option_id)
            if option.play_id != int(play_id):
                raise ParamErrorException(error_code.API_50101_QUIZ_OPTION_ID_INVALID)
        except Exception:
            raise ParamErrorException(error_code.API_50101_QUIZ_OPTION_ID_INVALID)

        # 判断赌注是否有效
        try:
            issues_obj = Issues.objects.filter(open=open_time, issue=issues,
                                               stock_pk_id=stock_pk_id).first()
        except Exception:
            raise ParamErrorException(error_code.API_40105_SMS_WAGER_PARAMETER)
        if 0 >= Decimal(bet):
            raise ParamErrorException(error_code.API_50102_WAGER_INVALID)

        # 是否封盘
        time_now = datetime.datetime.now()
        if time_now >= issues_obj.closing:
            raise ParamErrorException(error_code.API_80101_STOP_BETTING)

        # 获取 bet_limit, 共用旧股指玩法的限制指数
        try:
            bet_limit_dic = {}  # {play_id: bet_limit obj}
            for bet_limit in BetLimit.objects.filter(club_id=club_id, play_id=1):
                bet_limit_dic.update({
                    'bets_one': bet_limit.bets_one,
                    'bets_two': bet_limit.bets_two,
                    'bets_three': bet_limit.bets_three,
                    'bets_min': bet_limit.bets_min,
                    'bets_max': bet_limit.bets_max,
                })
        except Exception:
            raise ParamErrorException(error_code.API_40105_SMS_WAGER_PARAMETER)

        if bet > Decimal(bet_limit_dic['bets_max']) or bet < Decimal(bet_limit_dic['bets_min']):
            raise ParamErrorException(error_code.API_50102_WAGER_INVALID)

        # 单场比赛最大下注
        bet_sum = RecordStockPk.objects.filter(user_id=user.id, club_id=club_id, issue_id=issues_obj.id).aggregate(
            Sum('bets'))

        bet_sum = bet_sum['bets__sum'] if bet_sum['bets__sum'] else 0
        bet_sum = Decimal(bet_sum) + Decimal(bet)

        coin_info = Coin.objects.get_one(pk=coin_id)
        betting_toplimit = coin_info.betting_toplimit
        if Decimal(bet_sum) > betting_toplimit:
            raise ParamErrorException(error_code.API_50109_BET_LIMITED)

        user_coin = UserCoin.objects.get(user_id=user.id, coin_id=coin_id)
        # 判断用户金币是否足够
        if bet > Decimal(user_coin.balance):
            raise ParamErrorException(error_code.API_50104_USER_COIN_NOT_METH)

        bet = normalize_fraction(bet, coin_accuracy)
        record = RecordStockPk()
        record.issue_id = issues_obj.id
        record.user = user
        record.club_id = club_id
        record.play_id = play_id
        record.option_id = option_id
        record.bets = bet
        record.odds = option.odds
        source = request.META.get('HTTP_X_API_KEY')
        if source == 'ios':
            source = RecordStockPk.IOS
        elif source == 'android':
            source = RecordStockPk.ANDROID
        else:
            source = RecordStockPk.HTML5
        if user.is_robot is True:
            source = RecordStockPk.ROBOT
        record.source = source
        record.save()

        # 投注累积进缓存
        key_pk_bet_count = 'record_pk_bet_count' + '_' + str(issues_obj.stock_pk_id)
        pk_bet_count = get_cache(key_pk_bet_count)
        pk_bet_count[issues_obj.id][option_id] += 1
        set_cache(key_pk_bet_count, pk_bet_count)

        # 用户减少金币
        balance = normalize_fraction(user_coin.balance, coin_accuracy)
        user_coin.balance = balance - bet
        user_coin.save()

        coin_detail = CoinDetail()
        coin_detail.user = user
        coin_detail.coin_name = user_coin.coin.name
        coin_detail.amount = '-' + str(bet)
        coin_detail.rest = user_coin.balance
        coin_detail.sources = CoinDetail.BETS
        coin_detail.save()

        RecordMark.objects.update_record_mark(user.id, 6, 0)

        if int(club_id) == 1 or int(user.is_robot) == 1:
            pass
        else:
            clubinfo = Club.objects.get_one(pk=int(club_id))
            PromotionRecord.objects.insert_record(user, clubinfo, record.id, Decimal(bet), 5, record.created_at)

        response = {
            'code': 0,
            'data': {
                'message': '下注成功，金额总数为 ' + str(bet),
                'balance': normalize_fraction(user_coin.balance, int(coin_accuracy))
            }
        }
        return self.response(response)


class StockPKPushView(ListAPIView):
    """
    详情页面推送
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        issues_id = int(self.request.GET.get('issues_id'))
        club_id = int(self.request.GET.get('club_id'))
        qs = RecordStockPk.objects.filter(issue_id=issues_id, club_id=club_id)
        return qs

    def list(self, request, *args, **kwargs):
        cache_club_value = get_club_info()

        records_obj_dic = {}
        options_id_list = []
        user_id_list = []
        for record in self.get_queryset():
            if record.option_id not in options_id_list:
                options_id_list.append(record.option_id)
            if record.user_id not in user_id_list:
                user_id_list.append(record.user_id)
            records_obj_dic.update({
                record.id: {
                    'issues_id': record.issue_id, 'options_id': record.option_id, 'bets': record.bets,
                    'earn_coin': record.earn_coin, 'created_at': record.created_at, 'status': record.status,
                    'user_id': record.user_id, 'coin_name': cache_club_value[record.club_id]['coin_name'],
                }
            })

        # 处理user
        user_obj_dic = {}
        for user in User.objects.filter(id__in=user_id_list):
            user_obj_dic.update({
                user.id: {
                    'nickname': user.nickname,
                }
            })

        # 处理选项
        options_obj_dic = {}
        for option in OptionStockPk.objects.filter(id__in=options_id_list):
            options_obj_dic.update({
                option.id: {
                    'play_id': option.play_id, 'title': option.title, 'title_en': option.title_en,
                }
            })

        data = []
        for item_key, item_value in records_obj_dic.items():
            user_id = item_value['user_id']
            options_id = item_value['options_id']

            user_name = user_obj_dic[user_id]['nickname'][0] + '**'
            my_option = options_obj_dic[options_id]['title']
            if self.request.GET.get('language') == 'en':
                my_option = options_obj_dic[options_id]['title_en']
            bet = round(float(item_value['bets']), 3)
            coin_name = item_value['coin_name']

            data.append({
                "record_id": item_key,
                "username": user_name,
                "my_option": my_option,
                "bet": bet,
                "coin_name": coin_name,
            })
        return self.response({"code": 0, "data": data})
