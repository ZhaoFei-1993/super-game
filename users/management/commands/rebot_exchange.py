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
from chat.models import Club
from utils.weight_choice import WeightChoice


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
        change_gsg_value = self.get_change_gsg_value()  # 随机兑换GSG
        user = self.get_bet_user() # 随机下注用户

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

        self.stdout.write(self.style.SUCCESS("机器人："+str(user.username)+"在"+str(changerecord.created_at)+"时候兑换了"+str(changerecord.change_gsg_value)+"个GSG！"))

        self.stdout.write(self.style.SUCCESS('兑换成功'))

    @staticmethod
    def get_change_eth_value():

        change_eth_value = 1
        return change_eth_value

    @staticmethod
    def get_change_gsg_value():

        change_gsg_value = 1
        return change_gsg_value

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
    def get_date():
        """
        获取当天9点至21点的时间戳
        :return:
        """
        today = time.strftime("%Y-%m-%d")
        start_date = today + " 09:00:00"
        end_date = today + " 21:59:59"

        ts_start = time.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        ts_end = time.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        return int(time.mktime(ts_start)), int(time.mktime(ts_end))

    def set_today_random(self):
        """
        设置今日随机值，写入到缓存中，缓存24小时后自己销毁
        :return:
        """
        user_total = random.randint(1, 200)
        start_date, end_date = self.get_date()

        random_datetime = []
        for i in range(0, user_total):
            random_datetime.append(random.randint(start_date, end_date))

        set_cache(self.get_key(self.key_today_random), user_total, 24 * 3600)
        set_cache(self.get_key(self.key_today_random_datetime), random_datetime, 24 * 3600)

    @staticmethod
    def get_bet_user():
        """
        随机获取用户
        :return:
        """
        users = User.objects.filter(is_robot=True)
        secure_random = random.SystemRandom()
        return secure_random.choice(users)

