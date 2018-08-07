# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
import time
from datetime import datetime
from utils.cache import get_cache, set_cache
import random
from django.db import transaction
from django.db.models import Q

from guess.models import Stock, Periods, Record, Play, Options, BetLimit
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
    key_today_random = 'robot_stock_bet_total'

    # 本日生成的系统用户随机时间
    key_today_random_datetime = 'robot_stock_bet_datetime'

    # 本日已生成的系统用户时间
    key_today_generated = 'robot_stock_bet_quiz_datetime'

    robot_bet_change_odds = False

    @staticmethod
    def get_stock(stock_id):
        """
        获取股票名称
        :param stock_id
        :return:
        """
        stock_name = ''
        for stock in Stock.STOCK:
            sid, sname = stock
            if int(sid) == int(stock_id):
                stock_name = sname
                break

        return stock_name

    @staticmethod
    def get_play(play_id):
        """
        获取玩法名称
        :param play_id:
        :return:
        """
        play_name = ''
        for play in Play.PLAY:
            pid, pname = play
            if int(pid) == int(play_id):
                play_name = pname
                break

        return play_name

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
        items = Periods.objects.filter(is_seal=False, is_result=False).order_by('rotary_header_time')
        if len(items) == 0:
            raise CommandError('当前无进行中的竞猜')

        # items = self.get_get_quiz(items)
        item_len = len(items)

        idx = 0
        for item in items:
            # 按照比赛时间顺序递减下注数
            bet_number = random.randrange(item_len + 1, item_len * 3 + 1)
            bet_number -= idx * 2

            # 结束投注前前两个小时下注更密集
            time_now = datetime.now()
            countdown = (item.rotary_header_time - time_now).seconds

            # 两个小时内
            if 3600 < countdown <= 7200:
                bet_number *= 2
            elif countdown <= 3600:
                bet_number *= 3

            if bet_number < 2:
                continue

            for n in range(1, bet_number):
                # 随机获取俱乐部
                club = self.get_bet_club()
                if club is False:
                    continue

                # 随机获取股票
                stock = self.get_bet_stock()
                if stock is False:
                    continue

                # 随机抽取玩法
                rule = self.get_bet_rule(stock.id)
                if rule is False:
                    continue

                # 随机下注选项
                option = self.get_bet_option(rule.id)
                if option is False:
                    continue

                # 随机下注用户
                user = self.get_bet_user()

                # 随机下注币、赌注
                wager = self.get_bet_wager(club.id, rule.id)
                current_odds = option.odds

                record = Record()
                record.user = user
                record.periods = item
                record.club = club
                record.play = rule
                record.options = option
                record.bets = wager
                record.odds = current_odds
                record.source = Record.ROBOT
                record.save()

                bet_message = club.room_title + '-' + self.get_stock(stock.name) + '-' + self.get_play(rule.play_name) + '投注' + option.title + '：金额=' + str(wager)
                self.stdout.write(self.style.SUCCESS(bet_message))
                self.stdout.write(self.style.SUCCESS(''))

            idx += 1

        user_generated_datetime.append(current_generate_time)
        set_cache(self.get_key(self.key_today_generated), user_generated_datetime)

        self.stdout.write(self.style.SUCCESS('下注成功'))

    @staticmethod
    def get_get_quiz(items):
        """
        进行中的比赛下注权重
        3天数据：今天比赛:明天比赛:后天比赛 = 7:2:1
        4天数据：今天比赛:明天比赛:后天比赛:大后天 = 6:2:1:1
        5天以上数据，则随机用3天或4天数据
        :param items:
        :return:
        """
        secure_random = random.SystemRandom()
        return secure_random.choice(items)

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
            6: 350
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
    def get_bet_stock():
        """
        获取股票信息
        :return:
        """
        stocks = Stock.objects.filter(is_delete=False)
        secure_random = random.SystemRandom()
        return secure_random.choice(stocks)

    @staticmethod
    def get_bet_rule(stock_id):
        """
        获取下注玩法，随机获取，猜涨跌不下注
        :param stock_id:
        :return:
        """
        plays = Play.objects.filter(stock_id=stock_id)
        plays_weight = {
            1: 70,  # 大小
            2: 20,  # 点数
            3: 10,  # 对子
        }
        weight_choice = WeightChoice()
        weight_choice.set_choices(plays_weight)
        play_id = weight_choice.choice()

        choice = None
        for play in plays:
            if int(play.play_name) == int(play_id):
                choice = play
                break

        if choice is None:
            raise CommandError('未匹配到玩法 stock_id = ' + str(stock_id))
        return choice

    @staticmethod
    def get_bet_option(play_id):
        """
        获取下注选项，目前随机获取
        :param play_id 玩法ID
        :return:
        """
        options = Options.objects.filter(play_id=play_id).order_by('odds')
        if len(options) == 0:
            return False

        if play_id == 1:
            choice_a = random.randint(30, 70)
            choice_b = 100 - choice_a
            choices = {
                0: choice_a,
                1: choice_b,
            }
            weight_choice = WeightChoice()
            weight_choice.set_choices(choices)
            idx = weight_choice.choice()

            return options[idx]
        else:
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
    def get_bet_wager(club_id, play_id):
        """
        获取用户拥有哪些币种，并返回币种可下注金额
        高价值币种选择较下注金额
        :param club_id
        :param play_id
        :return:
        """
        club = Club.objects.get(pk=club_id)
        coin_id = club.coin_id

        bet_limit = BetLimit.objects.get(club_id=club_id, play_id=play_id)
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
