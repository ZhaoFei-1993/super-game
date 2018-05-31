# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from users.models import User, UserCoin, Coin, CoinValue
from utils.functions import random_string
from django.conf import settings
from django.db import transaction
import time
import random
from django.contrib.auth.hashers import make_password
from utils.functions import random_invitation_code
import linecache
from utils.cache import get_cache, set_cache


class Command(BaseCommand):
    """
    随机注册系统用户
    每天随机时间点注册1~10个用户（数量用户可配）
    当前时间大于或等于随机时间最小值时，则注册一个新用户
    """
    help = "随机注册用户"

    # 本日生成的系统用户总量
    key_today_random = 'robot_generate_total'

    # 本日生成的系统用户随机时间
    key_today_random_datetime = 'robot_generate_datetime'

    # 本日已生成的系统用户时间
    key_today_generated = 'robot_generate_user_datetime'

    @transaction.atomic()
    def handle(self, *args, **options):
        # 获取当天随机注册用户量
        random_total = get_cache(self.get_key(self.key_today_random))                    # 拿数据
        random_datetime = get_cache(self.get_key(self.key_today_random_datetime))
        if random_total is None or random_datetime is None:
            self.set_today_random()
            self.stdout.write(self.style.SUCCESS('已生成随机注册时间'))
            raise CommandError('...')

        random_datetime.sort()
        user_generated_datetime = get_cache(self.get_key(self.key_today_generated))
        if user_generated_datetime is None:
            user_generated_datetime = []

        # 算出随机注册时间与已注册时间差集
        diff_random_datetime = list(set(random_datetime) - set(user_generated_datetime))
        self.stdout.write(self.style.SUCCESS('仍有' + str(len(diff_random_datetime)) + '个时间点生成'))

        current_generate_time = ''
        for dt in diff_random_datetime:
            if self.get_current_timestamp() >= dt:
                current_generate_time = dt
                break

        if current_generate_time == '':
            raise CommandError('非生成系统用户时间')

        nickname, avatar = self.get_name_avatar()

        # 登录账号
        username = random_string(32)
        # 登录密码
        password = random_string(12)
        hash_password = make_password(password)

        user = User()
        user.username = username
        user.password = hash_password
        user.register_type = User.REGISTER_CONSOLE
        user.source = User.ROBOT
        user.telephone = ''
        user.avatar = avatar
        user.nickname = nickname
        user.invitation_code = random_invitation_code()
        user.is_robot = True
        user.save()

        # 插入用户余额表
        coins = Coin.objects.all()
        for coin in coins:
            # 获取该币可下注的最大值，确保每个机器人至少可以下注1000次
            max_coin_bet = CoinValue.objects.filter(coin_id=coin.id).order_by('-value').first()
            if max_coin_bet is None:
                continue

            max_coin = int(max_coin_bet.value)
            balance = float(random.randint(max_coin * 1000, max_coin * 10000))

            user_coin = UserCoin()
            user_coin.user = user
            user_coin.coin = coin
            user_coin.balance = balance
            user_coin.save()

        user_generated_datetime.append(current_generate_time)
        set_cache(self.get_key(self.key_today_generated), user_generated_datetime)

        self.stdout.write(self.style.SUCCESS('生成系统用户成功'))
        self.stdout.write(self.style.SUCCESS('账号为：' + username))
        self.stdout.write(self.style.SUCCESS('密码为：' + password))

    @staticmethod
    def get_name_avatar():
        """
        获取已经下载的用户昵称和头像
        :return:
        """
        key_name_avatar = 'key_name_avatar'

        line_number = get_cache(key_name_avatar)
        if line_number is None:
            line_number = 1

        file_avatar_nickname = settings.CACHE_DIR + '/new_avatar.lst'
        file_nickname = settings.CACHE_DIR + '/new_name.lst'
        nickname = linecache.getline(file_nickname, line_number)
        avatar_nickname = linecache.getline(file_avatar_nickname, line_number)
        a = avatar_nickname.split('_')
        if len(a) > 2:
            folder = str(a[0])
            suffix = str(a[1]) + "_" + str(a[2])
        else:
            folder, suffix = avatar_nickname.split('_')

        avatar_url = settings.MEDIA_DOMAIN_HOST + "/avatar/" + folder + '/' + avatar_nickname

        line_number += 1
        set_cache(key_name_avatar, line_number)
        return nickname, avatar_url

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
        获取当天0点至24点的时间戳
        :return:
        """
        today = time.strftime("%Y-%m-%d")
        start_date = today + " 00:00:00"
        end_date = today + " 23:59:59"

        ts_start = time.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        ts_end = time.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        return int(time.mktime(ts_start)), int(time.mktime(ts_end))

    def set_today_random(self):
        """
        设置今日随机值，写入到缓存中，缓存24小时后自己销毁
        :return:
        """
        user_total = random.randint(500, 1000)
        start_date, end_date = self.get_date()

        random_datetime = []
        for i in range(0, user_total):
            random_datetime.append(random.randint(start_date, end_date))

        set_cache(self.get_key(self.key_today_random), user_total, 24 * 3600)
        set_cache(self.get_key(self.key_today_random_datetime), random_datetime, 24 * 3600)
