from django.db import models
from chat.models import Club
from users.models import User, UserCoin, Coin, CoinDetail
from base.models import BaseManager
from decimal import Decimal

# Create your models here.


class BankerShare(models.Model):
    """
    联合做庄： 份额表
    """
    FOOTBALL = 1
    BASKETBALL = 2
    SIX = 3
    GUESS = 4
    GUESSPK = 5
    BACCARAT = 6
    DRAGON_TIGER = 7
    SOURCE = (
        (FOOTBALL, "足球"),
        (BASKETBALL, "篮球"),
        (SIX, "六合彩"),
        (GUESS, "猜股票"),
        (GUESSPK, "股票PK"),
        (BACCARAT, "百家乐"),
        (DRAGON_TIGER, "龙虎斗")
    )
    club = models.ForeignKey(Club, on_delete=models.DO_NOTHING, related_name='banker_club', verbose_name="俱乐部ID")
    source = models.IntegerField(verbose_name="类型", choices=SOURCE, default=FOOTBALL)
    balance = models.DecimalField(verbose_name='份额', max_digits=32, decimal_places=18, default=0.000000000000000000)
    proportion = models.DecimalField(verbose_name='占比', max_digits=4, decimal_places=3, default=0.000)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "份额表"


class BankerRecordManager(BaseManager):
    """
    联合做庄： 记录表数据库操作
    """

    def banker_settlement(self, list, source):
        """

        :param list: 例子
        [{"key_id": 1, "profit": 单场总盈利金额, "club_id": 5, "status": 正常开奖: 2  流盘: 3},
        {"key_id": 1, "profit": 单场总盈利金额, "club_id": 5, "status": 正常开奖: 2  流盘: 3}]
        :param source:  # 1.足球 2.篮球  3.六合彩  4.猜股指 5.股指PK  6.百家乐 7.龙虎斗
        :return:
        """
        info = {}
        print("list=======================", list)
        for i in list:
            key_id = int(i["key_id"])
            profit = Decimal(i["profit"])
            print("单局，盈亏===================", profit)
            club_id = int(i["club_id"])
            club_info = Club.objects.get_one(pk=club_id)
            coin_id = club_info.coin_id
            status = int(i["status"])
            info_list = BankerRecord.objects.filter(club_id=club_id, source=int(source), key_id=key_id, status=1)
            if len(info_list) > 0:  # 判断当局有无做庄记录
                for s in info_list:
                    if status == 2:    # 正常开奖才要录入总收益
                        proportion = Decimal(s.proportion)
                        s.earn_coin = proportion*profit*0.4
                        print("个人盈亏================", proportion)
                    else:
                        s.earn_coin = 0
                    s.status = status
                    s.save()
                    print("个人盈亏================", s.earn_coin)
                    print("个人押金================", s.balance)
                    info[key_id] = {
                        "coin_id": coin_id,
                        "user_id": s.user_id,
                        "earn_coin": Decimal(s.earn_coin),
                        "balance": Decimal(s.balance),
                    }
        print("info================", info)
        if len(info) > 0:   # info有数据老夫才派钱
            for a in info:
                coin_id = int(info[a]["coin_id"])
                coin_info = Coin.objects.get_one(pk=coin_id)
                user_id = int(info[a]["user_id"])
                print("user_id============" + str(user_id) + "coin_id=================" + str(coin_id))
                earn_coin = info[a]["earn_coin"]
                balance = info[a]["balance"]
                if earn_coin > 0:        # 有赚的情况下派钱
                    amount = Decimal(balance + earn_coin)
                    user_coin_info = UserCoin.objects.get(coin_id=coin_id, user_id=user_id)
                    user_coin_info.balance += amount
                    user_coin_info.save()

                    coin_detail = CoinDetail()
                    coin_detail.user = user_coin_info.user
                    coin_detail.coin_name = coin_info.name
                    coin_detail.amount = Decimal(amount)
                    coin_detail.rest = user_coin_info.balance
                    coin_detail.sources = 21
                    coin_detail.save()
                    print("用户--" + str(user_id) + "做庄赚了，加本金合计归还" + str(amount) + "个" + str(coin_info.name))
                elif abs(earn_coin) == 0:     # 不赚不亏或流盘,还钱
                    amount = balance
                    user_coin_info = UserCoin.objects.get(coin_id=coin_id, user_id=user_id)
                    user_coin_info.balance += amount
                    user_coin_info.save()

                    coin_detail = CoinDetail()
                    coin_detail.user = user_coin_info.user
                    coin_detail.coin_name = coin_info.name
                    coin_detail.amount = Decimal(amount)
                    coin_detail.rest = user_coin_info.balance
                    coin_detail.sources = 23
                    coin_detail.save()
                    print("用户--" + str(user_id) + "做庄没有赚没有亏或者流盘，系统还回做庄押金" + str(amount) + "个" + str(coin_info.name))
                else:    # 亏，但是没有亏完，交还部分本金
                    print("earn_coin=================", earn_coin)
                    print("earn_coin=================", abs(earn_coin))
                    if abs(earn_coin) < balance:
                        amount = balance + earn_coin
                        user_coin_info = UserCoin.objects.get(coin_id=coin_id, user_id=user_id)
                        user_coin_info.balance += amount
                        user_coin_info.save()

                        coin_detail = CoinDetail()
                        coin_detail.user = user_coin_info.user
                        coin_detail.coin_name = coin_info.name
                        coin_detail.amount = Decimal(amount)
                        coin_detail.rest = user_coin_info.balance
                        coin_detail.sources = 22
                        coin_detail.save()
                        print("用户--" + str(user_id) + "做庄亏了, 但押金还有剩，归还剩余" + str(amount) + "个" + str(coin_info.name))
                    else:   # 倾家荡产的忽略
                        print("用户--" + str(user_id) + "做庄，倾家荡产，亏了" + str(balance) + "个" + str(coin_info.name))
                    #     pass


class BankerRecord(models.Model):
    """
    联合做庄： 记录表
    """
    FOOTBALL = 1
    BASKETBALL = 2
    SIX = 3
    GUESS = 4
    GUESSPK = 5
    BACCARAT = 6
    DRAGON_TIGER = 7
    SOURCE = (
        (FOOTBALL, "足球"),
        (BASKETBALL, "篮球"),
        (SIX, "六合彩"),
        (GUESS, "猜股指"),
        (GUESSPK, "股指PK"),
        (BACCARAT, "百家乐"),
        (DRAGON_TIGER, "龙虎斗")
    )

    READY = 1
    SUCCESS = 2
    FLOW_DISK = 3
    TYPE_CHOICE = (
        (READY, "未分配奖励"),
        (SUCCESS, "已分配奖励"),
        (FLOW_DISK, "流盘")
    )
    club = models.ForeignKey(Club, on_delete=models.DO_NOTHING, related_name='banker_record_club', verbose_name="俱乐部ID")
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='banker_record_user', verbose_name="用户ID")
    balance = models.DecimalField(verbose_name='让购份额', max_digits=32, decimal_places=18, default=0.000000000000000000)
    proportion = models.DecimalField(verbose_name='份额占比', max_digits=12, decimal_places=10, default=0.0000000000)
    earn_coin = models.DecimalField(verbose_name="总收益", max_digits=18, decimal_places=8, default=0.00000000)
    source = models.IntegerField(verbose_name="玩法", choices=SOURCE, default=FOOTBALL)
    key_id = models.IntegerField(verbose_name="外键ID(玩法不同外键表不同)", default=0)
    status = models.IntegerField(verbose_name="是否分配奖励", choices=TYPE_CHOICE, default=READY)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    objects = BankerRecordManager()

    class Meta:
        verbose_name = verbose_name_plural = "做庄记录表"


class BankerBigHeadRecord(models.Model):
    """
    联合做庄： 局头记录表
    """

    club = models.ForeignKey(Club, on_delete=models.DO_NOTHING, related_name='banker_big_head_record_club', verbose_name="俱乐部ID")
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='banker_big_head_record_user', verbose_name="用户ID")
    proportion = models.DecimalField(verbose_name='局头份额占比', max_digits=3, decimal_places=2, default=0.35)
    is_receive = models.BooleanField(verbose_name="是否已有效", default=False)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    end_time = models.DateTimeField(verbose_name="失效时间", null=True)

    class Meta:
        verbose_name = verbose_name_plural = "做庄局头表表"




