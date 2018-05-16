from django.db import models
from users.models import Coin


class Address(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    address = models.CharField(verbose_name='地址', max_length=128)
    passphrase = models.CharField(verbose_name='密串', max_length=128)
    user = models.CharField(verbose_name="用户ID", max_length=128, default="")
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "充值地址"
