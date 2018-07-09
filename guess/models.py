from django.db import models, transaction
from wc_auth.models import Admin
from mptt.models import MPTTModel, TreeForeignKey
from users.models import Coin, User, CoinValue
from chat.models import Club
import reversion
from django.conf import settings
from django.db.models import Sum, F, FloatField

from decimal import Decimal

# Create your models here.



# @reversion.register()
# class GuessCategory(MPTTModel):
#     name = models.CharField(verbose_name="股票名称", max_length=50)
#     name_en = models.CharField(verbose_name="股票名称(英文)", max_length=50, default='')
#     icon = models.CharField(verbose_name="股票编号", max_length=50, default='')
#     admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
#     order = models.IntegerField(verbose_name="排序", default=0)
#     is_delete = models.BooleanField(verbose_name="是否删除", default=False)
#
#     class Meta:
#         ordering = ['-id']
#         verbose_name = verbose_name_plural = "股票表"