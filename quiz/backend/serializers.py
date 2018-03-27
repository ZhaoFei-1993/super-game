# -*- coding: UTF-8 -*-
from rest_framework import serializers

from ..models import Category


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    """
    竞猜分类
    """
    class Meta:
        model = Category
        fields = ("name", "parent", "is_delete")


