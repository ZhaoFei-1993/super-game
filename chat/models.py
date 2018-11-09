from django.db import models
from wc_auth.models import Admin
from users.models import User, Coin
import reversion
from base.models import BaseManager
import json
from django.conf import settings
import os
from datetime import datetime
import random
from utils.cache import set_cache, get_cache, delete_cache


class ClubManager(BaseManager):
    """
    俱乐部数据操作
    """
    key = 'club_data'

    # 在线人数时间段
    periods = {
        0: {
            'start': 0,
            'end': 9,
        },
        1: {
            'start': 9,
            'end': 12,
        },
        2: {
            'start': 12,
            'end': 20,
        },
        3: {
            'start': 20,
            'end': 23,
        },
        4: {
            'start': 23,
            'end': 0,
        }
    }

    key_online_users = 'club_online_users'
    key_online_period = 'club_online_users_period'

    def get_club_info(self):
        """
        从缓存读取club_info
        :return:
        """
        club_values = {}
        clubs = self.get_all()
        if len(clubs) == 0:
            return {}

        map_coin = {}
        coins = Coin.objects.get_all()
        for coin in coins:
            map_coin[coin.id] = coin

        for club in clubs:
            coin = map_coin[club.coin_id]

            club_values[club.id] = {
                'coin_id': club.coin_id,
                'club_name': club.room_title,
                'club_name_en': club.room_title_en,
                'coin_name': club.room_title.replace('俱乐部', ''),
                'coin_accuracy': coin.coin_accuracy,
                'coin_icon': coin.icon,
            }
        return club_values

    @staticmethod
    def save_online(online, club_id):
        """
        保存在线人数
        :return:
        """
        online = json.loads(online)
        players_online = {}
        for play_id in online:
            players_online[play_id] = online[play_id].split('|')
        cache_file = settings.CACHE_DIR + '/club_online/' + str(club_id)
        with open(cache_file, 'w') as file:
            file.write(json.dumps(players_online))

    @staticmethod
    def get_online_setting(club_id):
        """
        获取俱乐部在线人数配置
        :param club_id:
        :return:
        """
        cache_file = settings.CACHE_DIR + '/club_online/' + str(club_id)
        play_online = None
        if os.path.exists(cache_file):
            play_online = open(cache_file).readlines()[0]

        return play_online

    def get_club_online(self, club_id, club_play_id=None):
        """
        获取当前俱乐部人数
        先从缓存中获取，若缓存无数据，则从配置获取当前时间对应俱乐部下各个玩法的在线人数（范围）
        :param  club_id: 俱乐部ID
        :param  club_play_id: 玩法ID，若传该值，则返回该玩法下的在线人数，反之，返回该俱乐部下所有玩法人数总和
        :return:
        """
        # 获取缓存中的在线人数
        cache_online_users = get_cache(self.key_online_users)
        club_id = int(club_id)
        club_play_id = int(club_play_id) if club_play_id is not None else None

        # 获取所有玩法数据，未开放的不在统计范围内
        club_plays = ClubRule.objects.get_all()
        map_club_play = {}
        for club_play in club_plays:
            map_club_play[club_play.id] = club_play

        number = 0
        # 当缓存中有数据，则读取缓存中数据
        if cache_online_users is not None and club_id in cache_online_users:
            online = cache_online_users[club_id]

            # 是否只取出某个俱乐部下的玩法人数
            if club_play_id is not None:
                number = online[club_play_id]
            else:
                for play_id in online:
                    tmp_play = map_club_play[int(play_id)]
                    if tmp_play.is_dissolve is False or tmp_play.is_deleted is True:
                        continue

                    number += online[play_id]
        else:
            online = self.get_online_setting(club_id)
            # 未配置，则返回0
            if online is None:
                return 0
            online = json.loads(online)

            # 判断当前时间在哪个时间范围内
            hour = int(datetime.now().strftime('%H'))
            period = 0
            for p in self.periods:
                if self.periods[p]['start'] <= hour < self.periods[p]['end']:
                    period = p
                    break

            if cache_online_users is None:
                cache_online_users = {club_id: {}}
            else:
                cache_online_users[club_id] = {}
            for play_id in online:
                # 获取当前时间数据范围
                n = online[play_id][period]
                start, end = n.split(',')
                random_number = random.randint(int(start), int(end))
                cache_online_users[club_id][int(play_id)] = random_number        # club id 对应 play id 随机人数

                # 是否只取出某个俱乐部下的玩法人数
                if club_play_id is not None:
                    number = random_number
                else:
                    # 俱乐部列表统计总数
                    number += random_number

            set_cache(self.key_online_users, cache_online_users)

        return number

    def fluctuation_club_online(self):
        """
        俱乐部在线人数波动
        间隔时间：5分钟，crontab实现
        波动幅度：加减1~5范围内，波动人数也必须在设定范围内
        :return:
        """
        # 判断当前时间在哪个时间范围内
        hour = int(datetime.now().strftime('%H'))
        period = 0
        for p in self.periods:
            if self.periods[p]['start'] <= hour < self.periods[p]['end']:
                period = p
                break

        # 如果跨区间时间，则直接清除缓存等待重新生成
        cache_online_users_period = get_cache(self.key_online_period)
        if cache_online_users_period is None:
            set_cache(self.key_online_period, period)
        else:
            if cache_online_users_period != period:
                print('跨时区，清除缓存')
                delete_cache(self.key_online_period)
                return False

        print('current period = ', period)

        # 未生成缓存则不处理
        cache_online_users = get_cache(self.key_online_users)
        if cache_online_users is None:
            print('未生成缓存，跳过')
            return False

        cache_online_users_new = {}
        for club_id in cache_online_users:
            cache_online_users_new[club_id] = {}

            online = self.get_online_setting(club_id)
            online = json.loads(online)

            for play_id in cache_online_users[club_id]:
                value = cache_online_users[club_id][play_id]

                online_range = online[str(play_id)][period]
                start, end = online_range.split(',')
                start = int(start)
                end = int(end)

                # 随机加减
                operator = random.randint(1, 2)     # 1为减，2为加

                # 1~5随机数
                if operator == 1:
                    number = value - random.randint(1, 5)
                    number = number if number >= start else start
                else:
                    number = value + random.randint(1, 5)
                    number = number if number <= end else end

                cache_online_users_new[club_id][play_id] = number

        set_cache(self.key_online_users, cache_online_users_new)
        return True


@reversion.register()
class Club(models.Model):
    PENDING = 2  # 人气
    PUBLISHING = 3  # 热门
    CLOSE = 0  # 未开启
    NIL = 1   # 无角标

    STATUS_CHOICE = (
        (PENDING, "人气"),
        (PUBLISHING, "热门"),
        (CLOSE, "未开启"),
        (NIL, "无角标"),
    )

    room_title = models.CharField(verbose_name="俱乐部名", max_length=100)
    room_title_en = models.CharField(verbose_name="俱乐部名", max_length=100, default='')
    autograph = models.CharField(verbose_name="俱乐部签名", max_length=255)
    autograph_en = models.CharField(verbose_name="俱乐部签名", max_length=255, default='')
    # user_number = models.IntegerField(verbose_name="参与人数", default=1)
    icon = models.CharField(verbose_name="分类图标", max_length=255, default='')
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    room_number = models.IntegerField(verbose_name="俱乐部编号", default=0)
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    user = models.IntegerField(verbose_name="俱乐部创始人", default=0)
    is_banker = models.BooleanField(verbose_name="是否开启联合做庄", default=True)
    is_recommend = models.CharField(verbose_name="", choices=STATUS_CHOICE, max_length=1, default=PENDING)
    is_dissolve = models.BooleanField(verbose_name="是否删除俱乐部", default=False)

    objects = ClubManager()

    class Meta:
        ordering = ['user']
        verbose_name = verbose_name_plural = "俱乐部表"


class ClubRuleManager(BaseManager):
    """
    俱乐部玩法数据操作
    """
    key = 'club_rule_data'


@reversion.register()
class ClubRule(models.Model):
    title = models.CharField(verbose_name="玩法昵称", max_length=25)
    title_en = models.CharField(verbose_name="玩法昵称(en)", max_length=25, default='')
    icon = models.CharField(verbose_name="图片", max_length=255)
    room_number = models.IntegerField(verbose_name="在线人数", default=0)
    sort = models.IntegerField(verbose_name="排序", default=0)
    is_dissolve = models.BooleanField(verbose_name="是否开放", default=True)
    is_deleted = models.BooleanField(verbose_name="是否删除", default=False)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    banker_sort = models.IntegerField(verbose_name="联合做庄排序", default=0)
    banker_icon = models.CharField(verbose_name="联合做庄图片", max_length=255, default='')
    is_banker = models.BooleanField(verbose_name="是否开启联合做庄", default=True)

    objects = ClubRuleManager()

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "俱乐部玩法表"


@reversion.register()
class ClubBanner(models.Model):
    URL = 0
    CLUB = 1

    image = models.CharField(verbose_name="图像", max_length=255, default='')
    active = models.CharField(verbose_name="活动标识", max_length=255, default='')
    banner_type = models.IntegerField(verbose_name="轮播图类型", default=URL)
    param = models.CharField(verbose_name="轮播参数", default='', max_length=255)
    title = models.CharField(verbose_name="页面标题", default='', max_length=100)
    order = models.IntegerField(verbose_name="轮播顺序")
    language = models.CharField(verbose_name="语言", max_length=32, default='')
    is_delete = models.BooleanField(verbose_name="是否删除", default=0)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = verbose_name_plural = "轮播图表"

