# -*- coding: UTF-8 -*-
from django.db import models
import datetime


class Image(models.Model):
    path = "./images/" + datetime.datetime.now().strftime('%Y%m%d')

    image = models.ImageField(upload_to=path)

