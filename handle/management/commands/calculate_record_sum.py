# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from quiz.models import Record, EveryDayInjectionValue
from users.models import CoinPrice, User, UserCoin, CoinDetail, UserMessage
from chat.models import Club
from utils.functions import normalize_fraction
from django.db.models import Q
import datetime
from utils.cache import set_cache, get_cache, decr_cache, incr_cache, delete_cache


class Command(BaseCommand):
    help = "计算现在用户单日投注总量,和返现"

    def handle(self, *args, **options):
        # 分配比例
        rate = 0.001
        gsg_to_rmb = CoinPrice.objects.get(coin_name='GSG').price

        # 划分出时间区间
        date_now = datetime.datetime.now().strftime('%Y-%m-%d')
        print("date_now================", date_now)
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
            record_sum_usd = 0
            record_dic = {}
            for record_personal in records.filter(user_id=user_id):
                club_id = record_personal.roomquiz_id
                club_nickname = 'club_nickname'+str(club_id)
                coin_name = get_cache(club_nickname)
                if coin_name is None:
                    club_name = Club.objects.get(pk=club_id).room_title
                    coin_name = club_name.replace('俱乐部', '')
                    set_cache(club_nickname, coin_name, 24 * 3600)

                if coin_name in record_dic.keys():
                    record_dic[coin_name] = record_dic[coin_name] + float(record_personal.bet)
                else:
                    record_dic[coin_name] = normalize_fraction(record_personal.bet,
                                                               int(record_personal.club.coin.coin_accuracy))

                rmb_price = 'currency_corresponds_to_rmb_price_'+str(coin_name)
                usd_price = 'currency_corresponds_to_usd_price_' + str(coin_name)
                price = get_cache(rmb_price)
                price_usd = get_cache(usd_price)
                if price is None:
                    coin_price = CoinPrice.objects.get(coin_name=coin_name)
                    price = coin_price.price
                    set_cache(rmb_price, coin_price.price, 24 * 3600)
                if price_usd is None:
                    coin_price = CoinPrice.objects.get(coin_name=coin_name)
                    price_usd = coin_price.price_usd
                    set_cache(usd_price, price_usd, 24 * 3600)
                record_sum = record_sum + record_personal.bet * price
                record_sum_usd = record_sum + record_personal.bet * price_usd

            # 返现值
            if float(gsg_to_rmb) < float(0.65):
                gsg_to_rmb = 0.65
            cash_back_gsg = (float(record_sum) * rate) / float(gsg_to_rmb)
            cash_back_gsg = normalize_fraction(cash_back_gsg, 2)

            user_coin_gsg = UserCoin.objects.filter(user_id=user_id, coin_id=6).first()
            user_coin_gsg.balance = float(user_coin_gsg.balance) + float(cash_back_gsg)
            user_coin_gsg.save()

            # 用户资金明细表
            coin_detail = CoinDetail()
            coin_detail.user_id = user_id
            coin_detail.coin_name = "GSG"
            coin_detail.amount = float(cash_back_gsg)
            coin_detail.rest = user_coin_gsg.balance
            coin_detail.sources = CoinDetail.CASHBACK
            coin_detail.save()

            # 发送信息
            u_mes = UserMessage()
            u_mes.status = 0
            u_mes.user_id = user_id
            u_mes.message_id = 6  # 私人信息
            u_mes.title = '返现公告'
            u_mes.title_en = 'Cash-back announcement'
            content = ''
            for key, value in record_dic.items():
                content = content + str(value) + '个' + key + '，'
            u_mes.content = '您在' + date_last + '投注了' + content + '投注总价值约为' + str(
                normalize_fraction(record_sum_usd, 2)) + 'USD ,' + '本次GSG激励数量为' + str(cash_back_gsg) + '个，已发放！'
            u_mes.content_en = ''
            u_mes.save()

            # print('use_id=====> ', user_id, ' ,record_sum====> ', record_sum)
            print('use_id=====> ', user_id, ' ,record_sum====> ', record_sum, ' ,cash_back====> ', cash_back_gsg)

            obj = EveryDayInjectionValue()
            obj.user_id = user_id
            obj.injection_value = normalize_fraction(record_sum, 8)
            obj.cash_back_gsg = cash_back_gsg
            obj.is_robot = User.objects.get(pk=user_id).is_robot
            obj.injection_time = date_last
            obj.save()

        i = 1
        user_info_list = []
        for obj in EveryDayInjectionValue.objects.filter(injection_time=date_last).order_by('-injection_value'):
            EXCHANGE_QUALIFICATION = "exchange_qualification_" + str(obj.user_id) + '_' + str(date_now)  # key
            set_cache(EXCHANGE_QUALIFICATION, i, 86400)  # 存储
            obj.order = i
            obj.save()
            if i <= 1000:
                if obj.user.is_robot == True:
                    user_info_list.append(obj.user.id)
                print("i==========================", i)
                # 发送信息
                u_mes = UserMessage()
                u_mes.status = 0
                u_mes.user_id = obj.user_id
                u_mes.message_id = 6  # 私人信息
                u_mes.title_en = str(date_now) + 'GSG exchange qualification.'
                u_mes.title = str(date_now) + 'GSG兑换资格。'
                u_mes.content = '恭喜您获得了GSG的兑换资格。'
                u_mes.content_en = 'Congratulations on your eligibility for GSG.'
                u_mes.save()
            i += 1
        EXCHANGE_QUALIFICATION_INFO = "all_exchange_qualification__info" + str(date_now)  # key
        print("user_info_list================================", user_info_list)
        set_cache(EXCHANGE_QUALIFICATION_INFO, user_info_list, 86400)  # 存储

        EXCHANGE_QUALIFICATION_USER_ID_NUMBER = "all_exchange_qualification__info_number" + str(date_now)  # key
        set_cache(EXCHANGE_QUALIFICATION_USER_ID_NUMBER, len(user_info_list), 86400)  # 存储
