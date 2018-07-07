# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from quiz.models import Record, EveryDayInjectionValue
from users.models import CoinPrice, User, UserCoin, CoinDetail, UserMessage
from chat.models import Club
from utils.functions import normalize_fraction, gsg_coin_initialization
from django.db.models import Q
import datetime
from utils.cache import set_cache, get_cache, decr_cache, incr_cache, delete_cache


class Command(BaseCommand):
    help = "计算现在用户单日投注总量,和返现"

    def handle(self, *args, **options):
        # 分配比例
        rate = 0.001

        # 划分出时间区间
        date_now = datetime.datetime.now().strftime('%Y-%m-%d')
        date_last = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

        start_with = datetime.datetime(int(date_last.split('-')[0]), int(date_last.split('-')[1]),
                                       int(date_last.split('-')[2]), 0, 0, 0)
        end_with = datetime.datetime(int(date_last.split('-')[0]), int(date_last.split('-')[1]),
                                     int(date_last.split('-')[2]), 23, 59, 59)
        print(date_last, start_with, end_with, sep='\n')

        user_list = []
        records = Record.objects.filter(~Q(roomquiz_id=Club.objects.get(room_title='HAND俱乐部').id), is_distribution=True,
                                        open_prize_time__range=(start_with, end_with))
        for record in records:
            if record.user_id not in user_list:
                user_list.append(record.user_id)

        # print(user_list)

        for user_id in user_list:
            record_sum = 0
            # record_dic = {}
            for record_personal in records.filter(user_id=user_id):
                club_name = Club.objects.get(pk=record_personal.roomquiz_id).room_title
                coin_name = club_name.replace('俱乐部', '')
                # if coin_name in record_dic.keys():
                #     record_dic[coin_name] = record_dic[coin_name] + float(record_personal.bet)
                # else:
                #     record_dic[coin_name] = float(record_personal.bet)
                coin_price = CoinPrice.objects.get(coin_name=coin_name)
                record_sum = record_sum + record_personal.bet * coin_price.price

            # # 返现值
            # cash_back_gsg = (float(record_sum) * rate) / 0.5
            # cash_back_gsg = normalize_fraction(cash_back_gsg, 4)
            #
            # # 给用户user_coin加上gsg
            # gsg_count = UserCoin.objects.filter(user_id=user_id, coin_id=6).count()
            # if gsg_count == 0:
            #     user_coin_gsg = gsg_coin_initialization(user_id, 6)
            # else:
            #     user_coin_gsg = UserCoin.objects.filter(user_id=user_id, coin_id=6).first()
            # user_coin_gsg.balance = float(user_coin_gsg.balance) + float(cash_back_gsg)
            # user_coin_gsg.save()
            #
            # # 用户资金明细表
            # coin_detail = CoinDetail()
            # coin_detail.user_id = user_id
            # coin_detail.coin_name = "GSG"
            # coin_detail.amount = float(cash_back_gsg)
            # coin_detail.rest = user_coin_gsg.balance
            # coin_detail.sources = CoinDetail.CASHBACK
            # coin_detail.save()
            #
            # # 发送信息
            # u_mes = UserMessage()
            # u_mes.status = 0
            # u_mes.user_id = user_id
            # u_mes.message_id = 6  # 私人信息
            # u_mes.title = '返现公告'
            # u_mes.title_en = 'Cash-back announcement'
            # content = ''
            # for key, value in record_dic.items():
            #     content = content + str(value) + '个' + key + '，'
            # u_mes.content = '您在' + date_last + '投注了' + content + '根据coinmarketcap上的实时价格，您的投注总价值约为' + str(
            #     normalize_fraction(record_sum, 2)) + '，' + '本次GSG激励数量为' + str(cash_back_gsg) + '个，已发放！'
            # u_mes.content_en = ''
            # u_mes.save()

            print('use_id=====> ', user_id, ' ,record_sum====> ', record_sum)
            # print('use_id=====> ', user_id, ' ,record_sum====> ', record_sum, ' ,cash_back====> ', cash_back_gsg)

            obj = EveryDayInjectionValue()
            obj.user_id = user_id
            obj.injection_value = normalize_fraction(record_sum, 8)
            # obj.cash_back_gsg = cash_back_gsg
            obj.is_robot = User.objects.get(pk=user_id).is_robot
            obj.injection_time = date_last
            obj.save()

        i = 1
        for obj in EveryDayInjectionValue.objects.filter(injection_time=date_last).order_by('-injection_value'):
            EXCHANGE_QUALIFICATION = "exchange_qualification_" + str(obj.user_id) + '_' + str(date_now)  # key
            set_cache(EXCHANGE_QUALIFICATION, i, 86400)   # 存储
            obj.order = i
            obj.save()
            i += 1
