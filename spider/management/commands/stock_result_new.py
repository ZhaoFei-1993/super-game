# -*- coding: utf-8 -*-
from guess.models import Options, Periods, Index_day, Issues, Stock, StockPk, Index, RecordStockPk
from guess.models import Record as Guess_Record
from datetime import timedelta
from users.models import CoinDetail
from utils.functions import *
from time import time
from django.db.models import Q
from guess.consumers import guess_pk_result_list, guess_pk_index


class GuessRecording(object):
    def __init__(self):
        self.coin_detail_list = []
        self.user_message_list = []
        self.user_coin_dic = {}
        self.record_right_list = []
        self.record_false_list = []

    def base_functions(self, user_id, coin_id, coin_name, earn_coin):
        if Decimal(earn_coin) > 0:
            # user_coin
            if user_id not in self.user_coin_dic.keys():
                user_coin = UserCoin.objects.get(user_id=user_id, coin_id=coin_id)
                self.user_coin_dic.update({
                    user_id: {
                        coin_id: {'balance': float(user_coin.balance)}
                    }
                })
            if coin_id not in self.user_coin_dic[user_id].keys():
                user_coin = UserCoin.objects.get(user_id=user_id, coin_id=coin_id)
                self.user_coin_dic[user_id].update({
                    coin_id: {'balance': float(user_coin.balance)}
                })

            # 用户资金明细表
            self.user_coin_dic[user_id][coin_id]['balance'] = self.user_coin_dic[user_id][coin_id][
                                                                  'balance'] + earn_coin
            now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.coin_detail_list.append({
                'user_id': str(user_id),
                'coin_name': coin_name, 'amount': str(float(earn_coin)),
                'rest': str(self.user_coin_dic[user_id][coin_id]['balance']),
                'sources': str(CoinDetail.OPEB_PRIZE), 'is_delete': '0',
                'created_at': now_time,
            })

    def edit_user_message(self, record, club_name, club_name_en, coin_name):
        # 编辑开奖公告
        title = club_name + '开奖公告'
        title_en = 'Lottery announcement from' + club_name_en
        earn_coin = float(record.earn_coin)
        if earn_coin < 0:
            content = club_name + '已开奖，' + Stock.STOCK[int(record.periods.stock.name)][1] + '的正确答案是：收盘 ' \
                      + record.periods.size + '， ' + record.periods.points + '， 您选的答案是: ' + record.options.title + \
                      '，您答错了。'

            content_en = club_name + '已开奖，' + Stock.STOCK[int(record.periods.stock.name)][1] + '的正确答案是：收盘 ' + \
                         record.periods.size + '， ' + record.periods.points + '， 您选的答案是: ' + record.options.title + \
                         '您答错了。'
        else:
            content = club_name + '已开奖，' + Stock.STOCK[int(record.periods.stock.name)][1] + '的正确答案是：收盘 ' + \
                      record.periods.size + '， ' + record.periods.points + '， 您选的答案是: ' + \
                      record.options.title + '，您的奖金是：' + str(round(earn_coin, 5)) + coin_name

            content_en = club_name + '已开奖，' + Stock.STOCK[int(record.periods.stock.name)][1] + '的正确答案是：收盘 ' + \
                         record.periods.size + '， ' + record.periods.points + '， 您选的答案是: ' + record.options.title + \
                         '，您的奖金是：' + str(round(earn_coin, 5)) + coin_name

        now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.user_message_list.append(
            {
                'user_id': str(record.user_id), 'status': '0',
                'message_id': '6', 'title': title, 'title_en': title_en,
                'content': content, 'content_en': content_en,
                'created_at': now_time,
            }
        )

    def size_result(self, record, cache_club_value):
        """
        玩法：大小
        """
        # 获取币信息
        coin_id = cache_club_value[record.club.id]['coin_id']
        coin_name = cache_club_value[record.club.id]['coin_name']
        coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

        if record.periods.size == record.options.title:
            earn_coin = record.bets * record.odds
            earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
            earn_coin = float(earn_coin)
            # record.earn_coin = earn_coin
            # record.save()
            # 记录record
            self.record_right_list.append({'id': str(record.id), 'earn_coin': str(earn_coin)})
        else:
            earn_coin = '-' + str(record.bets)
            earn_coin = float(earn_coin)
            # record.earn_coin = earn_coin
            # record.save()
            # 记录record
            self.record_false_list.append({'id': str(record.id), 'earn_coin': str(earn_coin)})

        self.base_functions(record.user_id, coin_id, coin_name, earn_coin)

    def points_result(self, record, cache_club_value):
        """
        玩法：点数
        """
        coin_id = cache_club_value[record.club.id]['coin_id']
        coin_name = cache_club_value[record.club.id]['coin_name']
        coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

        num_list = record.periods.points
        if str(record.options.title) in num_list:
            earn_coin = record.bets * record.odds
            earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
            earn_coin = float(earn_coin)
            # record.earn_coin = earn_coin
            # record.save()
            # 记录record
            self.record_right_list.append({'id': str(record.id), 'earn_coin': str(earn_coin)})
        else:
            earn_coin = '-' + str(record.bets)
            earn_coin = float(earn_coin)
            # record.earn_coin = earn_coin
            # record.save()
            # 记录record
            self.record_false_list.append({'id': str(record.id), 'earn_coin': str(earn_coin)})

        self.base_functions(record.user_id, coin_id, coin_name, earn_coin)

    def pair_result(self, record, cache_club_value):
        """
        玩法：对⼦
        """
        coin_id = cache_club_value[record.club.id]['coin_id']
        coin_name = cache_club_value[record.club.id]['coin_name']
        coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

        if record.periods.pair == record.options.title:
            earn_coin = record.bets * record.odds
            earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
            earn_coin = float(earn_coin)
            # record.earn_coin = earn_coin
            # record.save()
            # 记录record
            self.record_right_list.append({'id': str(record.id), 'earn_coin': str(earn_coin)})
        else:
            earn_coin = '-' + str(record.bets)
            earn_coin = float(earn_coin)
            # record.earn_coin = earn_coin
            # record.save()
            # 记录record
            self.record_false_list.append({'id': str(record.id), 'earn_coin': str(earn_coin)})

        self.base_functions(record.user_id, coin_id, coin_name, earn_coin)

    def status_result(self, record, win_sum_dic, lose_sum_dic, cache_club_value):
        """
        玩法：涨跌
        """
        coin_id = cache_club_value[record.club.id]['coin_id']
        coin_name = cache_club_value[record.club.id]['coin_name']
        coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']
        club_name = cache_club_value[record.club.id]['club_name']

        lose_sum = lose_sum_dic[club_name]
        win_sum = win_sum_dic[club_name]

        if record.periods.up_and_down == record.options.title:
            earn_coin = lose_sum * (float(record.bets) / win_sum)
            earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
            earn_coin = float(earn_coin)
            # record.earn_coin = earn_coin
            # record.save()
            # 记录record
            self.record_right_list.append({'id': str(record.id), 'earn_coin': str(earn_coin)})
        else:
            earn_coin = '-' + str(record.bets)
            earn_coin = float(earn_coin)
            # record.earn_coin = earn_coin
            # record.save()
            # 记录record
            self.record_false_list.append({'id': str(record.id), 'earn_coin': str(earn_coin)})

        self.base_functions(record.user_id, coin_id, coin_name, earn_coin)

    def take_result(self, period, dt, date):
        print(dt)
        print('----------------')
        if dt['auto'] is True:
            """
            填入正确选项
            """
            num = float(dt['num'])
            period.lottery_value = num
            # 涨跌玩法
            if dt['status'] == 'up':
                period.up_and_down = '涨'
                period.up_and_down_en = 'up'
            elif dt['status'] == 'down':
                period.up_and_down = '跌'
                period.up_and_down_en = 'down'
            else:
                period.up_and_down = '和'
                period.up_and_down_en = 'draw'

            # lose_sum_dic = {}
            # win_sum_dic = {}
            # if period.up_and_down == '涨':
            #     lose_option = '跌'
            # else:
            #     lose_option = '涨'
            # for club in Club.objects.all():
            #     win_sum = Record.objects.filter(club=club, periods=period, play__play_name=str(0),
            #                                     options__title=period.up_and_down).aggregate(Sum('bets'))
            #     lose_sum = Record.objects.filter(club=club, periods=period, play__play_name=str(0),
            #                                      options__title=lose_option).aggregate(Sum('bets'))
            #     win_bet_sum = float(win_sum['bets__sum'])
            #     lose_bet_sum = float(lose_sum['bets__sum'])
            #
            #     club_name = club.room_title
            #     lose_sum_dic.update({club_name: lose_bet_sum})
            #     win_sum_dic.update({club_name: win_bet_sum})

            # win_sum_dic = {}
            # lose_sum_dic = {}
            # club_list = []
            # if period.up_and_down == '涨':
            #     lose_option = '跌'
            # else:
            #     lose_option = '涨'
            # for club in Club.objects.all():
            #     club_list.append(club.id)
            #     club_name = club.room_title
            #     win_sum_dic.update({club_name: 0})
            #     lose_sum_dic.update({club_name: 0})
            #
            # win_sum_objects = Record.objects.filter(club__in=club_list, periods=period, play__play_name=str(0),
            #                                         options__title=period.up_and_down)
            # lose_sum_objects = Record.objects.filter(club__in=club_list, periods=period, play__play_name=str(0),
            #                                          options__title=lose_option)
            # for data in win_sum_objects:
            #     win_sum_dic[data.club.room_title] = float(win_sum_dic[data.club.room_title]) + float(data.bets)
            #
            # for data in lose_sum_objects:
            #     lose_sum_dic[data.club.room_title] = float(lose_sum_dic[data.club.room_title]) + float(data.bets)
            #
            # period.save()

            # 大小玩法
            num_spilt = str(dt['num']).split('.')[1]
            num_sum = int(num_spilt[1])
            if num_sum >= 5:
                period.size = '大'
                period.size_en = 'big'
            elif num_sum < 5:
                period.size = '小'
                period.size_en = 'small'
            period.save()

            # 点数玩法
            period.points = num_spilt[0] + num_spilt[1]
            period.save()

            # 对子玩法
            if num_spilt[0] == num_spilt[1]:
                period.pair = num_spilt[0] + num_spilt[1]
                period.save()

            # 开始遍历record表
            self.ergodic_record(period)

    def ergodic_record(self, period, win_sum_dic={}, lose_sum_dic={}):
        cache_club_value = Club.objects.get_club_info()
        start_time = time()
        # 开始遍历record表
        i = 0
        rule_dic = {
            '1': self.size_result, '2': self.points_result,
            '3': self.pair_result, '0': self.status_result,
        }
        records = Guess_Record.objects.filter(periods=period, status='0')
        if len(records) > 0:
            for record in records:
                # i += 1
                # print('正在处理record_id为: ', record.id, ', 共 ', len(records), '条, 当前第 ', i, ' 条')
                if record.play.play_name == str(0):
                    rule_dic[record.play.play_name](record, win_sum_dic, lose_sum_dic, cache_club_value)
                else:
                    rule_dic[record.play.play_name](record, cache_club_value)

        # 开始执行sql语句
        # 更新record状态
        now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        update_record_right = 'earn_coin=VALUES(earn_coin),' \
                              'status=\'1\', is_distribution=\'1\', ' \
                              'open_prize_time=\'{open_prize_time}\''.format(open_prize_time=now_time)
        update_record_false = 'earn_coin=VALUES(earn_coin),' \
                              'status=\'1\', is_distribution=\'1\', ' \
                              'open_prize_time=\'{open_prize_time}\''.format(open_prize_time=now_time)
        sql_right = make_batch_update_sql('guess_record', self.record_right_list, update_record_right)
        sql_false = make_batch_update_sql('guess_record', self.record_false_list, update_record_false)
        # print(sql_right)
        # print(sql_false)
        with connection.cursor() as cursor:
            if sql_right is not False:
                cursor.execute(sql_right)
            if sql_false is not False:
                cursor.execute(sql_false)

        for record in Guess_Record.objects.filter(Q(periods=period) & ~Q(status='0')):
            club_name = cache_club_value[record.club.id]['club_name']
            club_name_en = cache_club_value[record.club.id]['club_name_en']
            coin_name = cache_club_value[record.club.id]['coin_name']
            self.edit_user_message(record, club_name, club_name_en, coin_name)

        self.insert_info()

        # index_day = Index_day.objects.filter(stock_id=period.stock.id, created_at=date).first()
        # index_day.index_value = float(dt['num'])
        # index_day.index_time = period.lottery_time
        # index_day.save()

        period.is_result = True
        period.save()

        end_time = time()
        cost_time = str(round(end_time - start_time)) + '秒'
        print('执行完成。耗时：' + cost_time)
        print('----------------------------------------------')

    def insert_info(self):
        # 插入coin_detail表
        sql = make_insert_sql('users_coindetail', self.coin_detail_list)
        # print(sql)
        with connection.cursor() as cursor:
            if sql is not False:
                cursor.execute(sql)

        # 更新user_coin表
        update_user_coin_duplicate_key = 'balance=VALUES(balance)'
        user_coin_list = []
        for key, value in self.user_coin_dic.items():
            for key_ch, value_ch in value.items():
                user_coin_list.append({
                    'user_id': str(key), 'coin_id': str(key_ch), 'balance': str(value_ch['balance']),
                })
        sql = make_batch_update_sql('users_usercoin', user_coin_list, update_user_coin_duplicate_key)
        # print(sql)
        with connection.cursor() as cursor:
            if sql is not False:
                cursor.execute(sql)

        # 插入user_message表
        sql = make_insert_sql('users_usermessage', self.user_message_list)
        # print(sql)
        with connection.cursor() as cursor:
            if sql is not False:
                cursor.execute(sql)

    @staticmethod
    def newobject(periods, stock_id, next_start, next_end):
        rotary_header_time = next_end - timedelta(minutes=30)
        new_object = Periods(periods=periods, stock_id=stock_id)
        new_object.save()
        new_object.lottery_time = next_end
        new_object.rotary_header_time = rotary_header_time
        new_object.save()

        return new_object


# ===================== 股指pk =====================

class GuessPKRecording(GuessRecording):
    @staticmethod
    def new_issues(left_periods, right_periods, start_time, stock_pk):
        end_with = left_periods.lottery_time
        if stock_pk == 2:
            start_with_str = (end_with - datetime.timedelta(days=1)).strftime('%Y-%m-%d') + ' ' + start_time
        else:
            start_with_str = end_with.strftime('%Y-%m-%d') + ' ' + start_time
        start_with = datetime.datetime.strptime(start_with_str, '%Y-%m-%d %H:%M:%S')
        stock_pk = StockPk.objects.get(left_stock_id=left_periods.stock_id,
                                       right_stock_id=right_periods.stock_id)

        rest_start_with = None
        rest_end_with = None
        if stock_pk.left_stock_name == '深证成指':
            rest_start_with = datetime.datetime.strptime(end_with.strftime('%Y-%m-%d') + ' ' + '11:30:00',
                                                         '%Y-%m-%d %H:%M:%S')
            rest_end_with = datetime.datetime.strptime(end_with.strftime('%Y-%m-%d') + ' ' + '13:01:00',
                                                       '%Y-%m-%d %H:%M:%S')

        issue = 0
        open_time = start_with + datetime.timedelta(minutes=5)
        print()
        while open_time <= end_with:
            if rest_start_with is not None:
                if rest_end_with > open_time > rest_start_with:
                    open_time = open_time + datetime.timedelta(minutes=5)
                    continue
            issue += 1
            closing = open_time - datetime.timedelta(seconds=45)
            new_issues_obj = Issues()
            new_issues_obj.stock_pk_id = stock_pk.id
            new_issues_obj.left_periods_id = left_periods.id
            new_issues_obj.right_periods_id = right_periods.id
            new_issues_obj.issue = issue
            new_issues_obj.closing = closing
            new_issues_obj.open = open_time
            new_issues_obj.save()

            open_time = open_time + datetime.timedelta(minutes=5)
        print('完成股指pk出题')

    def take_pk_result(self, left_periods, right_periods, start_time, stock_pk):
        time_now = datetime.datetime.now()
        issue_last = Issues.objects.filter(open__gt=time_now).order_by('open').first()
        if issue_last is not None:
            left_periods_id = issue_last.left_periods_id
            right_periods_id = issue_last.right_periods_id
            left_index_last = Index.objects.filter(periods_id=left_periods_id).order_by('-index_time').first()
            right_index_last = Index.objects.filter(periods_id=right_periods_id).order_by('-index_time').first()
            if left_index_last is not None and right_index_last is not None:
                if issue_last.left_stock_index != left_index_last.index_value or \
                        issue_last.right_stock_index != right_index_last.index_value:
                    issue_last.left_stock_index = left_index_last.index_value
                    issue_last.right_stock_index = right_index_last.index_value
                    issue_last.save()

                    guess_pk_index(issue_last, left_index_last.index_value, right_index_last.index_value)
                    print('推送index')

        # 股指pk出题找答案
        issues_result_flag = False
        issues_id = ''
        for issues in Issues.objects.filter(open__lt=time_now, result_confirm__lt=3).order_by('open'):
            issues_id = issues.id
            left_periods_id = issues.left_periods_id
            right_periods_id = issues.right_periods_id
            open_time = issues.open
            index_qs = Index.objects.filter(periods_id__in=[left_periods_id, right_periods_id],
                                            index_time=open_time)
            if len(index_qs) == 2:
                index_dic = {}
                for index in index_qs:
                    index_dic.update({
                        index.periods_id: index.index_value
                    })
                if issues.left_stock_index != index_dic[left_periods_id] or \
                        issues.right_stock_index != index_dic[right_periods_id]:
                    issues.left_stock_index = index_dic[left_periods_id]
                    issues.right_stock_index = index_dic[right_periods_id]

                    left_last_num = int(str(index_dic[left_periods_id])[-1])
                    right_last_num = int(str(index_dic[right_periods_id])[-1])

                    if left_last_num > right_last_num:
                        size_pk_result = issues.stock_pk.left_stock_name[:-2] + '大'
                    elif left_last_num < right_last_num:
                        size_pk_result = issues.stock_pk.right_stock_name[:-2] + '大'
                    else:
                        size_pk_result = '和'
                    issues.size_pk_result = size_pk_result

                    # 确认数清零
                    issues.result_confirm = 0
                else:
                    issues.result_confirm += 1

                issues.save()
                issues_result_flag = True
        if issues_result_flag is True:
            if issue_last is not None:
                guess_pk_result_list(issue_last.id)
            else:
                if issues_id != '':
                    guess_pk_result_list(issues_id)

        # 股指pk出题
        if left_periods is not None and right_periods is not None:
            if left_periods.lottery_time == right_periods.lottery_time:
                if Issues.objects.filter(left_periods_id=left_periods.id).exists() is not True:
                    self.new_issues(left_periods, right_periods, start_time, stock_pk)

    def pk_size(self, record, option_obj_dic, issues_obj):
        cache_club_value = Club.objects.get_club_info()
        coin_id = cache_club_value[record.club.id]['coin_id']
        coin_name = cache_club_value[record.club.id]['coin_name']
        coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

        option_id = record.option_id
        if option_obj_dic[option_id]['title'] == issues_obj.size_pk_result:
            earn_coin = record.bets * record.odds
            earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
            earn_coin = float(earn_coin)
            record.earn_coin = earn_coin
            record.status = 1
            record.save()
        else:
            earn_coin = '-' + str(record.bets)
            earn_coin = float(earn_coin)
            record.earn_coin = earn_coin
            record.status = 1
            record.save()
        self.base_functions(record.user_id, coin_id, coin_name, earn_coin)

# def ergodic_pk_record(issue_obj_dic):
#     records = RecordStockPk.objects.filter(issues_id=issues.id, status=str(RecordStockPk.AWAIT))
#     for record in records:
#         pass
