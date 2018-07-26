# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
import time
from datetime import datetime
from utils.cache import get_cache, set_cache
import random
from django.db import transaction

from quiz.models import ChangeRecord
from users.models import User, UserCoin, CoinDetail
from decimal import Decimal

from utils.functions import get_sql
from .rand_avg import get_robot_exchange


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
    key_today_random_datetime = 'robot_change_datetime_list'

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
        gsg_balance = self.get_gsg_balance()  # 剩余gsg

        if current_generate_time == '' or gsg_balance <= 0:
            raise CommandError('非自动兑换时间')

        # change_eth_value = self.get_change_eth_value()  # 随机兑换ETH
        # gsg_balance = self.get_gsg_balance()  # 剩余gsg
        # gsg_balance = 10000  # 剩余gsg
        user_number = self.get_user_number()  # 剩余人数
        # user_number = 1  # 剩余人数
        convert_ratio = self.get_eth_exchange_gsg_number()
        if user_number == 1:
            change_eth_value = gsg_balance * convert_ratio
            change_gsg_value = gsg_balance
        else:
            change_eth_value = get_robot_exchange(gsg_balance, user_number, convert_ratio)  # 随机兑换ETH
            change_gsg_value = change_eth_value * float(convert_ratio)  # 随机兑换GSG
        user = self.get_bet_user()  # 随机下注用户

        changerecord = ChangeRecord()
        changerecord.user = user
        changerecord.change_eth_value = change_eth_value
        changerecord.change_gsg_value = change_gsg_value
        changerecord.is_robot = True
        changerecord.save()

        # 用户增加对应币持有数
        user_coin = UserCoin.objects.get(user=user, coin_id=6)
        user_coin.balance += Decimal(change_gsg_value)
        user_coin.save()
        coin_detail = CoinDetail()
        coin_detail.user = user
        coin_detail.coin_name = user_coin.coin.name
        coin_detail.amount = '+' + str(change_gsg_value)
        coin_detail.rest = Decimal(user_coin.balance)
        coin_detail.sources = 13
        coin_detail.save()

        self.stdout.write(self.style.SUCCESS(
            "机器人：" + str(user.username) + "在" + str(changerecord.created_at) + "时候兑换了" + str(
                changerecord.change_gsg_value) + "个GSG！"))

        user_generated_datetime.append(current_generate_time)
        set_cache(self.get_key(self.key_today_generated), user_generated_datetime, 24 * 3600)

        self.stdout.write(self.style.SUCCESS('兑换成功'))

    def gsg_time(self):
        today = time.strftime("%Y-%m-%d")
        user_number = self.get_bet_user_number()
        start_time = today + " 00:00:00"
        end_time = today + " 20:59:59"
        gsg_value = 2000000
        list = [start_time, end_time, gsg_value, user_number]
        return list

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
        if numbers == None or numbers == 0:
            numbers = 0
        number = int(list[3]) - numbers
        return number

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
        if is_use == None or is_use == 0:
            is_use = 0
        gsg_balance = list[2] - is_use
        return gsg_balance

    def get_change_eth_value(self):
        gsg_balance = self.get_gsg_balance()  # 剩余gsg
        user_number = self.get_user_number()  # 剩余人数
        convert_ratio = self.get_eth_exchange_gsg_number()  #
        change_eth_value = gsg_balance / user_number * convert_ratio
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
        convert_ratio = round(eth_vlue / gsg_value, 2)  # 1 ETH 换多少 GSG
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
        """

        :return:
        """
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        ts = time.strptime(current_time, "%Y-%m-%d %H:%M:%S")
        return int(time.mktime(ts))

    @staticmethod
    def get_date_early():
        """
        获取当天9点至20点的时间戳
        :return:
        """
        list = []

        today = time.strftime("%Y-%m-%d")
        start_date_one = today + " 10:00:00"
        end_date_one = today + " 13:59:59"
        start_date_two = today + " 14:00:00"
        end_date_two = today + " 17:59:59"
        start_date_three = today + " 18:00:00"
        end_date_three = today + " 20:59:59"

        ts_start_one = time.strptime(start_date_one, "%Y-%m-%d %H:%M:%S")
        ts_start_two = time.strptime(end_date_one, "%Y-%m-%d %H:%M:%S")
        ts_start_three = time.strptime(start_date_two, "%Y-%m-%d %H:%M:%S")
        ts_end_one = time.strptime(end_date_two, "%Y-%m-%d %H:%M:%S")
        ts_end_two = time.strptime(start_date_three, "%Y-%m-%d %H:%M:%S")
        ts_end_three = time.strptime(end_date_three, "%Y-%m-%d %H:%M:%S")
        list = [int(time.mktime(ts_start_one)), int(time.mktime(ts_end_one)), int(time.mktime(ts_start_two)),
                int(time.mktime(ts_end_two)), int(time.mktime(ts_start_three)), int(time.mktime(ts_end_three))]
        return list

    def set_today_random(self):
        """
        设置今日随机值，写入到缓存中，缓存24小时后自己销毁
        :return:
        """
        user_number = self.get_bet_user_number()
        user_number_list = self.constrained_sum_sample_pos(3, user_number)
        # user_numer_early = int(user_number * 0.3)
        user_numer_early = user_number_list[0]
        user_total_early = random.randint(user_numer_early, user_numer_early)

        # user_numer_late = user_number - (int(user_number * 0.3)*2)
        user_numer_late = user_number_list[1]
        user_total_late = random.randint(user_numer_late, user_numer_late)

        user_numer_late_a = user_number_list[2]
        user_total_late_a = random.randint(user_numer_late_a, user_numer_late_a)

        list = self.get_date_early()
        start_date_early_one = list[0]
        end_date_early_one = list[1]

        random_datetime_one = []
        for i in range(0, user_total_early):
            random_datetime_one.append(random.randint(start_date_early_one, end_date_early_one))

        start_date_early_two = list[2]
        end_date_early_two = list[3]

        random_datetime_two = []
        for i in range(0, user_total_late):
            random_datetime_two.append(random.randint(start_date_early_two, end_date_early_two))

        start_date_early_three = list[4]
        end_date_early_three = list[5]

        random_datetime_three = []
        for i in range(0, user_total_late_a):
            random_datetime_three.append(random.randint(start_date_early_three, end_date_early_three))

        random_datetime = random_datetime_one + random_datetime_two + random_datetime_three

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
        EXCHANGE_QUALIFICATION_INFO = "all_exchange_qualification__info" + str(date_now)  # key
        users = get_cache(EXCHANGE_QUALIFICATION_INFO)
        EXCHANGE_QUALIFICATION_USER_ID_NUMBER = "all_exchange_qualification__info_number" + str(date_now)  # key
        user_info_list_number = get_cache(EXCHANGE_QUALIFICATION_USER_ID_NUMBER)
        if user_info_list_number < 500:
            users = User.objects.filter(is_robot=True)[:800]
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
        if user_info_list_number < 500:
            user_info_list_number = 800
        return user_info_list_number

    @staticmethod
    def constrained_sum_sample_pos(n, total):
        """Return a randomly chosen list of n positive integers summing to total.
         Each such list is equally likely to occur."""

        dividers = sorted(random.sample(range(1, total), n - 1))
        return [a - b for a, b in zip(dividers + [total], [0] + dividers)]
