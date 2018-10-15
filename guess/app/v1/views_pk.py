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
from utils.functions import get_club_info, normalize_fraction, value_judge, handle_zero
from users.models import UserCoin, CoinDetail, User
from spider.management.commands.stock_index import market_rest_cn_list


class StockPkDetail(ListAPIView):
    """
    股指pk详情
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        # 正常status
        status = 0
        switch_time = ''
        time_now = datetime.datetime.now()
        # stock_pk_id_list = StockPk.objects.all().values_list('id', flat=True)
        issue_last = Issues.objects.filter(open__gt=time_now).order_by('open').first()
        if issue_last.issue == 1:
            issue_pre = Issues.objects.filter(open__lt=time_now).order_by('-open').first()
            if (issue_pre.open + datetime.timedelta(hours=1)) > time_now:
                qs = issue_pre
                #  一小时切换status, 4: 中to美, 5: 美to中
                switch_time = qs.open + datetime.timedelta(hours=1)
                switch_time = time.mktime(switch_time.timetuple())
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
        else:
            qs = issue_last
            # 中场休息status
            if qs.open.strftime('%H:%M:%S') == '13:05:00':
                if time_now < qs.open - datetime.timedelta(minutes=5):
                    status = 1
                else:
                    status = 0
        return qs, {'status': status, 'switch_time': switch_time}

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
        open_timestamp = time.mktime(issues.open.timetuple())
        if status_dic['status'] == 1:
            open_timestamp = time.mktime((issues.open - datetime.timedelta(minutes=5)).timetuple())

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
        record_dic = {}
        for record in RecordStockPk.objects.filter(issue_id=issues.id, club_id=club_id, play_id__in=plays_dic.keys()):
            record_dic.update({
                record.id: {
                    'user_id': record.user_id, 'option_id': record.option_id
                }
            })

        # 获取选项
        options_dic = {}
        for key, value in plays_dic.items():
            options_dic.update({key: []})

        for option in OptionStockPk.objects.filter(stock_pk_id=stock_pk_id).order_by('order'):
            records_num = len(record_dic.keys())
            options_records_num = 0
            is_choice = 0
            for key, value in record_dic.items():
                if value['option_id'] == option.id and value['user_id'] == user.id:
                    is_choice = 1
                if value['option_id'] == option.id:
                    options_records_num += 1
            if records_num == 0:
                support_rate = 0
            else:
                support_rate = round((int(options_records_num) / int(records_num)) * 100, 2)  # 支持率
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
            if item['size_pk_result'] != '':
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
        club_id = int(self.request.GET.get('club_id'))  # 俱乐部表ID

        if 'user_id' not in self.request.GET:
            user_id = self.request.user.id
        else:
            user_id = self.request.GET.get('user_id')

        is_end = int(self.request.GET.get('is_end'))
        if is_end == RecordStockPk.AWAIT:
            qs = RecordStockPk.objects.filter(user_id=user_id, club_id=club_id, status=str(RecordStockPk.AWAIT))
        elif is_end == RecordStockPk.OPEN:
            qs = RecordStockPk.objects.filter(user_id=user_id, club_id=club_id, status=str(RecordStockPk.OPEN))
        else:
            qs = RecordStockPk.objects.filter(user_id=user_id, club_id=club_id)
        return qs

    def list(self, request, *args, **kwargs):
        club_id = int(self.request.GET.get('club_id'))  # 俱乐部表ID

        cache_club_value = get_club_info()
        coin_accuracy = cache_club_value[club_id]['coin_accuracy']
        coin_icon = cache_club_value[club_id]['coin_icon']
        coin_name = cache_club_value[club_id]['coin_name']

        records_obj_dic = {}
        options_id_list = []
        issues_id_list = []
        for record in self.get_queryset():
            if record.option_id not in options_id_list:
                options_id_list.append(record.option_id)
            if record.issue_id not in issues_id_list:
                issues_id_list.append(record.issue_id)
            records_obj_dic.update({
                record.id: {
                    'issues_id': record.issue_id, 'options_id': record.option_id, 'bets': record.bets,
                    'earn_coin': record.earn_coin, 'created_at': record.created_at, 'status': record.status
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
        for item_key, item_value in records_obj_dic.items():
            # 时间
            created_at = item_value['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            year = created_at.split(' ')[0].split('-')[0]
            date = created_at.split(' ')[0].split('-')[1] + '/' + created_at.split(' ')[0].split('-')[2]
            time = created_at.split(' ')[1].split(':')[0] + ':' + created_at.split(' ')[1].split(':')[1]

            # earn_coin, is_right
            is_right = 0
            earn_coin = normalize_fraction(item_value['earn_coin'], int(coin_accuracy))
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

            data.append({
                'id': item_key,
                'year': year,
                'date': date,
                'time': time,
                'title': title,
                'type': record_type,
                'my_option': my_option,
                'is_right': is_right,
                'earn_coin': earn_coin_result,
                'coin_name': coin_name,
                'coin_icon': coin_icon,
                'issue': issue,
                'result_answer': result_answer,
                'bet': item_value['bets'],
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
        bet = float(self.request.data.get('bet'))
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
        if 0 >= float(bet):
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

        if bet > float(bet_limit_dic['bets_max']) or bet < float(bet_limit_dic['bets_min']):
            raise ParamErrorException(error_code.API_50102_WAGER_INVALID)

        user_coin = UserCoin.objects.get(user_id=user.id, coin_id=coin_id)
        # 判断用户金币是否足够
        if bet > float(user_coin.balance):
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
        qs = RecordStockPk.objects.filter(issue_id=issues_id)
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