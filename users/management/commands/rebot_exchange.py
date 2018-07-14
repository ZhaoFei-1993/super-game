# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
import time
from datetime import datetime, timedelta
from utils.cache import get_cache, set_cache
import random
from django.db import transaction
from django.db.models import Q

from quiz.models import ChangeRecord, Record
from users.models import User, UserCoin, CoinValue, Coin
from decimal import Decimal
from utils.weight_choice import WeightChoice
from utils.functions import value_judge, get_sql


class Command(BaseCommand):
    """
    机器人下注频率影响因素：
    1.　题目下注数范围
    2.　题目创建时间长短
    3.　题目周期
    4.　赔率调整需要
    目前暂先实现随机时间对进行中的竞猜下注，下注金额随机
    """
    help = "系统用户自动兑换"

    # 本日生成的系统用户总量
    key_today_random = 'robot_change_total'

    # 本日生成的系统用户随机时间
    key_today_random_datetime = 'robot_change_datetime'

    # 本日已使用的系统用户时间
    key_today_generated = 'robot_in_change_datetime'

    @transaction.atomic()
    def handle(self, *args, **options):

        # 获取当天随机注册用户量
        random_total = get_cache(self.get_key(self.key_today_random))
        random_datetime = get_cache(self.get_key(self.key_today_random_datetime))
        if random_total is None or random_datetime is None:
            self.set_today_random()
            raise CommandError('已生成随机兑换时间')

        random_datetime.sort()
        user_generated_datetime = get_cache(self.get_key(self.key_today_generated))
        if user_generated_datetime is None:
            user_generated_datetime = []

        # 算出随机注册时间与已注册时间差集
        diff_random_datetime = list(set(random_datetime) - set(user_generated_datetime))

        current_generate_time = ''
        for dt in diff_random_datetime:
            if self.get_current_timestamp() >= dt:
                current_generate_time = dt
                break

        if current_generate_time == '':
            raise CommandError('非自动兑换时间')

        change_eth_value = self.get_change_eth_value()  # 随机兑换ETH
        convert_ratio = self.get_eth_exchange_gsg_number()
        change_gsg_value = change_eth_value/convert_ratio  # 随机兑换GSG
        user = self.get_bet_user()  # 随机下注用户

        changerecord = ChangeRecord()
        changerecord.user = user
        changerecord.change_eth_value = change_eth_value
        changerecord.change_gsg_value = change_gsg_value
        changerecord.is_robot = True
        changerecord.save()

        # 用户增加对应币持有数
        user_coin = UserCoin.objects.get(user=user, coin_id=6)
        user_coin.balance += change_gsg_value
        user_coin.save()

        self.stdout.write(self.style.SUCCESS(
            "机器人：" + str(user.username) + "在" + str(changerecord.created_at) + "时候兑换了" + str(
                changerecord.change_gsg_value) + "个GSG！"))

        self.stdout.write(self.style.SUCCESS('兑换成功'))

    @staticmethod
    def gsg_time(self):
        today = time.strftime("%Y-%m-%d")
        go_time = today + " 19:00:00"
        user_number = self.get_bet_user_number()
        user_numer_early = int(user_number * 0.9)
        if self.get_current_timestamp() <= go_time:
            start_time = today + " 00:00:00"
            end_time = today + " 18:59:59"
            gsg_value = 1500000
        else:
            start_time = today + " 19:00:00"
            end_time = today + " 21:00:00"
            gsg_value = 1500000
            user_numer_early = user_number - int(user_number * 0.9)
        list = [start_time, end_time, gsg_value, user_numer_early]
        return list

    @staticmethod
    def get_user_number(self):
        """
        当前时间段剩余待兑换人数
        :param self:
        :return:
        """
        list = self.gsg_time()
        sql = "select count(a.user_id) from quiz_changerecord a"
        sql += " where created_at>= '" + list[0] + "'"
        sql += " and a.created_at<= '" + list[1] + "'"
        numbers = get_sql(sql)[0][0]  # 兑换总人数
        number = int(list[3]) - numbers
        return number

    @staticmethod
    def get_gsg_balance(self):
        """
        当前时间段剩余待兑换GSG
        :param self:
        :return:
        """
        list = self.gsg_time()
        sql = "select sum(a.change_gsg_value) from quiz_changerecord a"
        sql += " where created_at>= '" + list[0] + "'"
        sql += " and a.created_at<= '" + list[1] + "'"
        is_use = get_sql(sql)[0][0]
        gsg_balance = list[2] - is_use
        return gsg_balance

    @staticmethod
    def get_change_eth_value(self):
        gsg_balance = self.get_gsg_balance()
        user_number = self.get_user_number()
        convert_ratio = self.get_eth_exchange_gsg_number()
        change_eth_value = gsg_balance/user_number*convert_ratio
        return change_eth_value


    @staticmethod
    def get_eth_exchange_gsg_number():
        """
        当前时间点1ETH兑换多少gsg
        :return:
        """
        sql = "select a.price from users_coinprice a"
        sql += " where coin_name='ETH'"
        sql += " and a.platform_name!=''"
        eth_vlue = get_sql(sql)[0][0]  # ETH 价格
        gsg_value = Decimal(0.3)
        convert_ratio = int(eth_vlue / gsg_value)  # 1 ETH 换多少 GSG
        return convert_ratio

    @staticmethod
    def get_key(prefix):
        """
        组装缓存key值
        :param prefix:
        :return:
        """
        return prefix + time.strftime("%Y-%m-%d")

    @staticmethod
    def get_current_timestamp():
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        ts = time.strptime(current_time, "%Y-%m-%d %H:%M:%S")
        return int(time.mktime(ts))

    @staticmethod
    def get_date_early():
        """
        获取当天9点至20点的时间戳
        :return:
        """
        today = time.strftime("%Y-%m-%d")
        start_date = today + " 09:00:00"
        end_date = today + " 18:59:59"

        ts_start = time.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        ts_end = time.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        return int(time.mktime(ts_start)), int(time.mktime(ts_end))

    @staticmethod
    def get_date_late():
        """
        获取当天20点至21点的时间戳
        :return:
        """
        today = time.strftime("%Y-%m-%d")
        start_date = today + " 19:00:00"
        end_date = today + " 21:59:59"

        ts_start = time.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        ts_end = time.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        return int(time.mktime(ts_start)), int(time.mktime(ts_end))

    def set_today_random(self):
        """
        设置今日随机值，写入到缓存中，缓存24小时后自己销毁
        :return:
        """
        user_number = self.get_bet_user_number()
        user_numer_early = int(user_number * 0.9)
        user_total_early = random.randint(user_numer_early, user_numer_early)
        start_date_early, end_date_early = self.get_date_early()

        random_datetime_early = []
        for i in range(0, user_total_early):
            random_datetime_early.append(random.randint(start_date_early, end_date_early))

        user_numer_late = user_number - int(user_number * 0.9)
        user_total_late = random.randint(user_numer_late, user_numer_late)
        start_date_late, end_date_late = self.get_date_late()

        random_datetime_late = []
        for i in range(0, user_total_late):
            random_datetime_late.append(random.randint(start_date_late, end_date_late))

        random_datetime = random_datetime_early + random_datetime_late

        set_cache(self.get_key(self.key_today_random), user_number, 24 * 3600)
        set_cache(self.get_key(self.key_today_random_datetime), random_datetime, 24 * 3600)

    @staticmethod
    def get_bet_user():
        """
        随机获取有兑换资格的机器用户
        :return:
        """
        # users = User.objects.filter(is_robot=True)
        date_now = datetime.now().strftime('%Y-%m-%d')
        EXCHANGE_QUALIFICATION_INFO = "all_exchange_qualification__info_" + str(date_now)  # key
        users = get_cache(EXCHANGE_QUALIFICATION_INFO)
        print("user_info_list================================", users)
        secure_random = random.SystemRandom()
        user_id = secure_random.choice(users)
        user_info = User.objects.get(pk=user_id)
        return user_info

    @staticmethod
    def get_bet_user_number():
        """
        获取有兑换资格的机器人数量
        :return:
        """
        date_now = datetime.now().strftime('%Y-%m-%d')
        EXCHANGE_QUALIFICATION_USER_ID_NUMBER = "all_exchange_qualification__info_number" + str(date_now)  # key
        user_info_list_number = get_cache(EXCHANGE_QUALIFICATION_USER_ID_NUMBER)
        return user_info_list_number
