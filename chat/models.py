from django.db import models
from wc_auth.models import Admin
from users.models import User, Coin


# Create your models here.

class Club(models.Model):
    room_title = models.CharField(verbose_name="俱乐部名", max_length=100)
    autograph = models.CharField(verbose_name="俱乐部签名", max_length=255)
    # user_number = models.IntegerField(verbose_name="参与人数", default=1)
    icon = models.CharField(verbose_name="分类图标", max_length=255, default='')
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    room_number = models.IntegerField(verbose_name="俱乐部编号", default=0)
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_recommend = models.BooleanField(verbose_name="是否推荐", default=False)
    is_dissolve = models.BooleanField(verbose_name="是否删除俱乐部", default=False)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "俱乐部表"
