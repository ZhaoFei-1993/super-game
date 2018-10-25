# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
import time
from datetime import datetime
from utils.cache import get_cache, set_cache
import random
from django.db import transaction
from django.db.models import Q

from guess.models import OptionStockPk, BetLimit, Issues, RecordStockPk
from users.models import User, Coin
from chat.models import Club
from utils.weight_choice import WeightChoice


class Command(BaseCommand):
    """
    机器人下注
    目前暂先实现随机时间对进行中的竞猜下注，下注金额随机
    """
    help = "系统用户自动下注-猜股指"

    # 本日生成的系统用户总量
    key_today_random = 'robot_pk_bet_total'

    # 本日生成的系统用户随机时间
    key_today_random_datetime = 'robot_pk_bet_datetime'

    # 本日已生成的系统用户时间
    key_today_generated = 'robot_pk_bet_datetime'

    robot_bet_change_odds = False

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
        user_total = random.randint(800, 1000)
        start_date, end_date = self.get_date()

        random_datetime = []
        for i in range(0, user_total):
            random_datetime.append(random.randint(start_date, end_date))

        set_cache(self.get_key(self.key_today_random), user_total, 24 * 3600)
        set_cache(self.get_key(self.key_today_random_datetime), random_datetime, 24 * 3600)

    @staticmethod
    def get_bet_club():
        """
        获取下注的俱乐部
        不同俱乐部选择权重不同
        :return:
        """
        clubs = Club.objects.filter(~Q(is_recommend=Club.CLOSE))
        if len(clubs) == 0:
            return False

        club_weight = {
            1: 350,
            2: 100,
            3: 100,
            4: 100,
            5: 300,
            6: 350,
            7: 100,
            8: 200,
            9: 300,
        }

        weight_choice = WeightChoice()
        weight_choice.set_choices(club_weight)
        club_id = weight_choice.choice()

        club_choice = None
        for club in clubs:
            if int(club.id) == int(club_id):
                club_choice = club
                break

        if club_choice is None:
            raise CommandError('未匹配到俱乐部，club_id = ', club_id)

        return club_choice

    @staticmethod
    def get_bet_option(issue, last_issue):
        """
        获取下注选项
        :param last_issue 上期数据
        :return:
        """
        options = OptionStockPk.objects.filter(play_id=1, stock_pk=issue.stock_pk_id).order_by('order')
        if len(options) == 0:
            return False

        # 获取上一期大小的开奖结果
        # 上期大，则下注权重为：押大:押和:押小=50:10:40
        # 上期和，则下注权重为：押大:押和:押小=40:20:40
        # 上期小，则下注权重为：押大:押和:押小=40:10:50
        if '大' in last_issue.size_pk_result:
            choices = {
                0: 50,
                1: 10,
                2: 40,
            }
        elif '小' in last_issue.size_pk_result:
            choices = {
                0: 40,
                1: 10,
                2: 50,
            }
        else:
            choices = {
                0: 40,
                1: 20,
                2: 40,
            }
        weight_choice = WeightChoice()
        weight_choice.set_choices(choices)
        idx = weight_choice.choice()
        return options[idx]

    @staticmethod
    def get_bet_user():
        """
        随机获取用户
        :return:
        """
        users = User.objects.filter(is_robot=True)
        secure_random = random.SystemRandom()
        return secure_random.choice(users)

    @staticmethod
    def get_bet_wager(club_id):
        """
        获取用户拥有哪些币种，并返回币种可下注金额
        高价值币种选择较下注金额
        :param club_id
        :return:
        """
        club = Club.objects.get(pk=club_id)
        coin_id = club.coin_id

        # 获取 bet_limit, 共用旧股指玩法的限制指数
        bet_limit = BetLimit.objects.get(club_id=club_id, play_id=1)
        bets_one = bet_limit.bets_one
        bets_two = bet_limit.bets_two
        bets_three = bet_limit.bets_three

        choices = {
            bets_one: 334,
            bets_two: 333,
            bets_three: 333,
        }
        if coin_id == Coin.BTC:
            """
            BTC下币权重
            """
            choices = {
                bets_one: 70,
                bets_two: 29,
                bets_three: 1,
            }
        elif coin_id == Coin.ETH:
            """
            ETH下币权重
            """
            choices = {
                bets_one: 80,
                bets_two: 15,
                bets_three: 5,
            }
        elif coin_id == Coin.USDT:
            """
            USDT下币权重
            """
            choices = {
                bets_one: 80,
                bets_two: 15,
                bets_three: 5,
            }

        weight_choice = WeightChoice()
        weight_choice.set_choices(choices)
        return weight_choice.choice()

    @transaction.atomic()
    def handle(self, *args, **options):
        # 获取当天随机注册用户量
        random_total = get_cache(self.get_key(self.key_today_random))
        random_datetime = get_cache(self.get_key(self.key_today_random_datetime))
        if random_total is None or random_datetime is None:
            self.set_today_random()
            raise CommandError('已生成随机下注时间')

        random_datetime.sort()
        user_generated_datetime = get_cache(self.get_key(self.key_today_generated))
        if user_generated_datetime is None:
            user_generated_datetime = []

        # 算出随机注册时间与已注册时间差集
        diff_random_datetime = list(set(random_datetime) - set(user_generated_datetime))
        print('今日总下注数 = ', random_total)
        print('今日剩余下注数 = ', len(diff_random_datetime))

        current_generate_time = ''
        for dt in diff_random_datetime:
            if self.get_current_timestamp() >= dt:
                current_generate_time = dt
                break

        if current_generate_time == '':
            raise CommandError('非自动下注时间')

        # 获取进行中的竞猜
        print(datetime.now())
        item = Issues.objects.filter(open__gt=datetime.now()).order_by('open').first()
        if item is None:
            raise CommandError('当前无进行中的竞猜')
        # 获取上期开奖结果
        last_issue = Issues.objects.filter(~Q(size_pk_result=''), open__lt=datetime.now()).order_by('-open').first()

        # 按照比赛时间顺序递减下注数
        bet_number = random.randrange(2, 4)

        for n in range(1, bet_number):
            # 随机获取俱乐部
            club = self.get_bet_club()
            if club is False:
                continue

            # 随机下注选项
            option = self.get_bet_option(item, last_issue)
            if option is False:
                continue

            # 随机下注用户
            user = self.get_bet_user()

            # 随机下注币、赌注
            wager = self.get_bet_wager(club.id)

            record = RecordStockPk()
            record.issue_id = item.id
            record.user = user
            record.club_id = club.id
            record.play_id = 1
            record.option_id = option.id
            record.bets = wager
            record.odds = option.odds
            record.source = RecordStockPk.ROBOT
            record.save()

            bet_message = club.room_title + '-' + '股指pk' + '-' + '投注选项为:' + option.title + '：金额=' + str(wager)
            self.stdout.write(self.style.SUCCESS(bet_message))
            self.stdout.write(self.style.SUCCESS(''))

        user_generated_datetime.append(current_generate_time)
        set_cache(self.get_key(self.key_today_generated), user_generated_datetime)

        self.stdout.write(self.style.SUCCESS('下注成功'))
