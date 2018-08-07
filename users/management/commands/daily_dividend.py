# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from datetime import datetime, timedelta
from users.models import Coin, UserCoin, UserCoinLock, Dividend, CoinDetail, DividendConfig, DividendConfigCoin
import dateparser
from decimal import Decimal
from utils.functions import make_insert_sql
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
    total_gsg = 1000000000  # GSG总发行量
    dividend_decimal = settings.DIVIDEND_DECIMAL    # 分红精度

    total_dividend = 0
    dividend_date = ''
    dividend_percent = {}
    coin_price = {}

    lock_time_delta = 12 * 3600        # 锁定12小时后方可享受分红，单位（秒）

    def check_lock_time(self, lock_time):
        """
        判断锁定时间到00:00:00是否超过12小时
        :param lock_time:
        :return:
        """
        end_dt = datetime.now().strftime("%Y-%m-%d 23:59:59")
        return lock_time + timedelta(seconds=self.lock_time_delta) <= dateparser.parse(end_dt)

    def get_coin_dividend(self, amount):
        """
        获取每种币用户可分得数量
        公式：( 分红金额 * 币种比例 / 币种价格 ) * ( 用户锁定量 / GSG总发行量 )
        :param amount   锁定数量
        :return:
        """
        percent = Decimal(amount / self.total_gsg)
        coin_dividend = {}
        for coin_id in self.dividend_percent:
            coin_percent = Decimal(self.dividend_percent[coin_id])
            dividend = self.total_dividend * coin_percent / Decimal(self.coin_price[coin_id]) * percent
            dividend = int(dividend * self.dividend_decimal) / self.dividend_decimal
            coin_dividend[coin_id] = '%.6f' % dividend

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
        dividend_date = dateparser.parse(datetime.strftime(datetime.now(), '%Y-%m-%d'))

        try:
            dividend_config = DividendConfig.objects.get(dividend_date=dividend_date)
        except DividendConfig.DoesNotExist:
            raise CommandError('Not set yet')

        dividend_config_coin = DividendConfigCoin.objects.filter(dividend_config=dividend_config)

        self.total_dividend = dividend_config.dividend      # 分红总额
        self.dividend_date = dividend_config.dividend_date - timedelta(1)  # 分红日期

        percent = {}
        price = {}
        for ditem in dividend_config_coin:
            percent[ditem.coin_id] = ditem.scale / 100
            price[ditem.coin_id] = ditem.price

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
        message_template = 'GSG' + self.dividend_date + '盈利情况：xxxBTC、xxxETH、xxxINT，根据您GSG锁定数量xxx，获得的分红为xxxBTC、xxxETH、xxxINT，已发放至您的钱包，请查收！'
        for ucl in user_coin_lock:
            created_at = str(datetime.now())

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

        self.stdout.write(self.style.SUCCESS('-----执行完成-----'))
