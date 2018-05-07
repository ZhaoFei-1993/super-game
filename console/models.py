from django.db import models
from users.models import Coin, User


class Address(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    address = models.CharField(verbose_name='地址', max_length=128)
    passphrase = models.CharField(verbose_name='密串', max_length=128)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

