from django.db import models
from wc_auth.models import Admin
from users.models import User, Coin
import reversion


# Create your models here.
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
    is_recommend = models.CharField(verbose_name="", choices=STATUS_CHOICE, max_length=1, default=PENDING)
    is_dissolve = models.BooleanField(verbose_name="是否删除俱乐部", default=False)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "俱乐部表"


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

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "俱乐部玩法表"


@reversion.register()
class ClubBanner(models.Model):
    image = models.CharField(verbose_name="图像", max_length=255, default='')
    active = models.CharField(verbose_name="活动标识", max_length=255, default='')
    order = models.IntegerField(verbose_name="轮播顺序")
    language = models.CharField(verbose_name="语言", max_length=32, default='')
    is_delete = models.BooleanField(verbose_name="是否删除", default=0)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = verbose_name_plural = "轮播图表"
