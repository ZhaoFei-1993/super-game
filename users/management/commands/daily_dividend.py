# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from django.db.models import Sum
from datetime import datetime, timedelta
from users.models import Coin, UserCoin, UserCoinLock, Dividend, CoinDetail, DividendConfig, DividendConfigCoin
import dateparser
from decimal import Decimal
from utils.functions import make_insert_sql, get_cache, set_cache
from django.conf import settings


class Command(BaseCommand):
    """
    每日分红
    每日分红时间点：
    分红金额：手工录入
    分红池定义：昨日平台每个币种真实盈利数据，如今天是2018-08-08，则统计出2018-08-07当天BTC、ETH、INT、HAND、USDT等币盈利数值
    俱乐部币随机生成比例，比例总和=100
    币价抓取时间点：

    例子说明：
    分红时间：2018-08-08
    分红数据时间：2018-08-07
    分红金额：1500 USD
    昨日营收：BTC=1个，ETH=10个，USDT=10000个，INT=1000个
    币种比例：BTC=10%，ETH=20%，USDT=30%，INT=40%
    当前币价：BTC=7700 USD，ETH=425 USD，USDT=1 USD，INT=0.06 USD
    币种数量：
        BTC = 1500 * 10% / 7700 = 0.02
        ETH = 1500 * 20% / 425 = 0.7
        USDT = 1500 * 30% / 1 = 450
        INT = 1500 * 40% / 0.06 = 10000
    """
    help = "每日分红"
    key_daily_dividend_datetime = 'daily_dividend_'
    dividend_decimal = settings.DIVIDEND_DECIMAL  # 分红精度

    dividend_id = 0
    total_dividend = 0
    dividend_date = ''
    dividend_percent = {}
    coin_price = {}
    coin_titular_dividend = {}  # 每种币实际分红数量

    lock_time_delta = 12 * 3600  # 锁定12小时后方可享受分红，单位（秒）

    profit_coin_message = []  # 组成 xxxBTC、xxxINT
    user_profit_coin_message = []  # 用户分红，组成 xxxBTC、xxxINT

    def check_lock_time(self, lock_time):
        """
        判断锁定时间到00:00:00是否超过12小时
        :param lock_time:
        :return:
        """
        end_dt = datetime.now().strftime("%Y-%m-%d 23:59:59")
        return lock_time + timedelta(seconds=self.lock_time_delta) <= dateparser.parse(end_dt)

    @staticmethod
    def get_total_coin_lock():
        """
        获取平台GSG总锁定量
        :return:
        """
        lock_sum = UserCoinLock.objects.filter(is_free=False).aggregate(lock_sum=Sum('amount'))

        if lock_sum['lock_sum'] is None:
            total_coin_lock = 0
        else:
            total_coin_lock = lock_sum['lock_sum']

        return total_coin_lock

    def get_coin_dividend(self, amount):
        """
        获取每种币用户可分得数量
        公式：( 分红金额 * 币种比例 / 币种价格 ) * ( 用户锁定量 / GSG总锁定量 )
        :param amount   锁定数量
        :return:
        """
        coin_dividend = {}
        for coin_id in self.coin_titular_dividend:
            user_dividend = float(amount) * self.coin_titular_dividend[coin_id]
            user_dividend = int(user_dividend * self.dividend_decimal) / self.dividend_decimal
            user_dividend = '%.7f' % user_dividend

            coin_dividend[coin_id] = user_dividend

            self.user_profit_coin_message.append(str(user_dividend) + self.get_coin_name(coin_id))
        # percent = Decimal(amount / self.get_total_coin_lock())
        # coin_dividend = {}
        # for coin_id in self.dividend_percent:
        #     coin_percent = Decimal(self.dividend_percent[coin_id])
        #     dividend = self.total_dividend * coin_percent / Decimal(self.coin_price[coin_id]) * percent
        #     dividend = int(dividend * self.dividend_decimal) / self.dividend_decimal
        #
        #     user_dividend = '%.7f' % dividend
        #     coin_dividend[coin_id] = user_dividend
        #
        #     self.user_profit_coin_message.append(str(user_dividend) + self.get_coin_name(coin_id))

        return coin_dividend

    @staticmethod
    def get_coin_name(coin_id):
        """
        获取币名称
        :return:
        """
        coin_name = ''
        if coin_id == Coin.BTC:
            coin_name = 'BTC'
        elif coin_id == Coin.INT:
            coin_name = 'INT'
        elif coin_id == Coin.HAND:
            coin_name = 'HAND'
        elif coin_id == Coin.USDT:
            coin_name = 'USDT'
        elif coin_id == Coin.ETH:
            coin_name = 'ETH'

        return coin_name

    @staticmethod
    def get_dividended_datetime(user_coin_lock):
        """
        获取已分红日期
        :return:
        """
        ucl_ids = []
        for aucl in user_coin_lock:
            ucl_ids.append(aucl.id)

        dividend_list = Dividend.objects.filter(user_lock_id__in=ucl_ids).values('created_at')
        dividend_datetime = []
        if len(dividend_list) > 0:
            for dvl in dividend_list:
                dvd_dt = datetime.strftime(dvl['created_at'], '%Y-%m-%d')
                if dvd_dt in dividend_datetime:
                    continue

                dividend_datetime.append(dvd_dt)

        return dividend_datetime

    def get_dividend_config(self):
        """
        获取分红配置
        :return:
        """
        date_today = datetime.strftime(datetime.now(), '%Y-%m-%d')
        dividend_date = dateparser.parse(date_today)

        # 判断当天是否已经分红
        if get_cache(self.key_daily_dividend_datetime + date_today) is not None:
            raise CommandError(date_today + '已经分红')

        try:
            dividend_config = DividendConfig.objects.get(dividend_date=dividend_date)
        except DividendConfig.DoesNotExist:
            raise CommandError('Not set yet')

        dividend_config_coin = DividendConfigCoin.objects.filter(dividend_config=dividend_config)

        self.dividend_id = dividend_config.id
        self.total_dividend = dividend_config.dividend  # 分红总额
        # self.dividend_date = dividend_config.dividend_date - timedelta(1)  # 分红日期
        self.dividend_date = dividend_config.dividend_date  # 分红日期

        percent = {}
        price = {}
        for ditem in dividend_config_coin:
            percent[ditem.coin_id] = ditem.scale / 100
            price[ditem.coin_id] = ditem.price

            self.coin_titular_dividend[ditem.coin_id] = ditem.coin_titular_dividend

            # 盈利情况组成字符串
            self.profit_coin_message.append(str(ditem.revenue) + self.get_coin_name(ditem.coin_id))

        self.dividend_percent = percent
        self.coin_price = price

    @transaction.atomic()
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('-----每日分红脚本开始运行-----'))

        # 获取分红配置
        self.get_dividend_config()

        # 获取所有锁定数据：用户、锁定金额、锁定时间
        user_coin_lock = UserCoinLock.objects.filter(is_free=False)
        print('获取到', len(user_coin_lock), '条锁定记录')

        # 获取已分红数据
        dividend_datetime = self.get_dividended_datetime(user_coin_lock)

        self.dividend_date = self.dividend_date.strftime('%Y-%m-%d')

        dividend_values = []
        coin_detail_values = []
        user_message_values = []
        for ucl in user_coin_lock:
            created_at = str(datetime.now())
            self.user_profit_coin_message = []

            # 判断锁定时间是否大于12小时
            if self.check_lock_time(ucl.created_at) is False:
                print('user_coin_lock id = ', ucl.id, ' 未达到12小时')
                continue

            # 判断是否已经分过红
            if self.dividend_date in dividend_datetime:
                print(ucl.id, ' 已分过红 ', self.dividend_date)
                continue

            # 获取分红金额
            dividend_coins = self.get_coin_dividend(ucl.amount)

            message_template = 'GSG' + self.dividend_date + '盈利情况：%s，根据您GSG锁定数量%s，获得的分红为%s，已发放至您的钱包，请查收！'
            message_template = message_template % (
            '、'.join(self.profit_coin_message), str(int(ucl.amount)), '、'.join(self.user_profit_coin_message))

            for coin_id in dividend_coins:
                dividend_amount = str(dividend_coins[coin_id])

                user_coin = UserCoin.objects.get(user_id=ucl.user_id, coin_id=coin_id)
                user_coin.balance += Decimal(dividend_amount)
                user_coin.save()

                # 插入分红记录
                dividend_values.append({
                    'coin_id': str(coin_id),
                    'user_lock_id': str(ucl.id),
                    'divide': dividend_amount,
                    'divide_config_id': str(self.dividend_id),
                    'user_id': str(ucl.user_id),
                    'created_at': created_at,
                })

                # 用户余额变更记录
                coin_detail_values.append({
                    'user_id': str(ucl.user_id),
                    'coin_name': self.get_coin_name(coin_id),
                    'amount': str(dividend_amount),
                    'rest': str(user_coin.balance),
                    'sources': str(CoinDetail.DEVIDEND),
                    'created_at': created_at,
                    'is_delete': str(0),
                })

            # 发送分红消息
            user_message_values.append({
                'status': '0',
                'user_id': str(ucl.user_id),
                'message_id': '6',
                'title': str(self.dividend_date) + '锁定分红情况',
                'title_en': '',
                'content': message_template,
                'content_en': '',
                'created_at': created_at,
            })

        if len(dividend_values) > 0:
            with connection.cursor() as cursor:
                cursor.execute(make_insert_sql('users_dividend', dividend_values))
                cursor.execute(make_insert_sql('users_coindetail', coin_detail_values))
                cursor.execute(make_insert_sql('users_usermessage', user_message_values))

        set_cache(self.key_daily_dividend_datetime + self.dividend_date, '1', 86400)
        self.stdout.write(self.style.SUCCESS('-----执行完成-----'))
