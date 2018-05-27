# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
import time
from datetime import datetime
from utils.cache import get_cache, set_cache
import random
from django.db import transaction
from django.db.models import Q

from quiz.models import Quiz, Option, Record, Rule, OptionOdds
from users.models import User, UserCoin, CoinValue
from chat.models import Club


class Command(BaseCommand):
    """
    机器人下注频率影响因素：
    1.　题目下注数范围
    2.　题目创建时间长短
    3.　题目周期
    4.　赔率调整需要
    目前暂先实现随机时间对进行中的竞猜下注，下注金额随机
    """
    help = "系统用户自动下注"

    # 本日生成的系统用户总量
    key_today_random = 'robot_bet_total'

    # 本日生成的系统用户随机时间
    key_today_random_datetime = 'robot_bet_datetime'

    # 本日已生成的系统用户时间
    key_today_generated = 'robot_bet_quiz_datetime'

    robot_bet_change_odds = False

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

        current_generate_time = ''
        for dt in diff_random_datetime:
            if self.get_current_timestamp() >= dt:
                current_generate_time = dt
                break

        if current_generate_time == '':
            raise CommandError('非自动下注时间')

        # 获取所有进行中的竞猜
        quizs = Quiz.objects.filter(status=Quiz.PUBLISHING, is_delete=False, begin_at__gt=datetime.now())
        if len(quizs) == 0:
            raise CommandError('当前无进行中的竞猜')

        for quiz in quizs:
            # 随机获取俱乐部
            club = self.get_bet_club()
            if club is False:
                continue

            # 随机抽取玩法
            rule = self.get_bet_rule(quiz.id)
            if rule is False:
                continue

            # 随机下注选项
            option = self.get_bet_option(rule.id)
            if option is False:
                continue

            # 随机下注用户
            user = self.get_bet_user()

            # 随机下注币、赌注
            wager = self.get_bet_wager(club.coin_id)

            current_odds = option.odds

            record = Record()
            record.quiz = quiz
            record.user = user
            record.rule = rule
            record.option = option
            record.roomquiz_id = club.id
            record.bet = wager
            record.odds = current_odds
            record.source = Record.CONSOLE
            record.save()

            if self.robot_bet_change_odds is True:
                Option.objects.change_odds(rule.id, club.coin_id, club.id)

            # 用户减少对应币持有数
            user_coin = UserCoin.objects.get(user=user, coin_id=club.coin_id)
            user_coin.balance -= wager
            user_coin.save()

        self.stdout.write(self.style.SUCCESS('下注成功'))

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
        user_total = random.randint(1, 10)
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
        :return:
        """
        club = Club.objects.filter(~Q(is_recommend=Club.CLOSE))
        if len(club) == 0:
            return False

        secure_random = random.SystemRandom()
        choice_club = secure_random.choice(club)
        print('choice_club = ', choice_club)
        return choice_club

    @staticmethod
    def get_bet_rule(quiz_id):
        """
        获取下注玩法，随机获取
        :param quiz_id:
        :return:
        """
        rule = Rule.objects.filter(quiz_id=quiz_id)
        if len(rule) == 0:
            return False

        secure_random = random.SystemRandom()
        return secure_random.choice(rule)

    @staticmethod
    def get_bet_option(rule_id):
        """
        获取下注选项，目前随机获取
        :param rule_id 玩法ID
        :return:
        """
        options = OptionOdds.objects.filter(option__rule_id=rule_id)
        if len(options) == 0:
            return False

        secure_random = random.SystemRandom()
        return secure_random.choice(options)

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
    def get_bet_wager(coin_id):
        """
        获取用户拥有哪些币种，并返回币种可下注金额
        :param coin_id
        :return:
        """
        secure_random = random.SystemRandom()
        coin_value = CoinValue.objects.filter(coin_id=coin_id)
        use_value = secure_random.choice(coin_value)

        return use_value.value
