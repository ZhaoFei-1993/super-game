# -*- coding: UTF-8 -*-
import pytz
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from config.models import Config, Article, AndroidVersion
from django.utils import timezone
from users.models import DailySettings


class LargeResultsSetPagination(PageNumberPagination):
    """
    获取所有配置项记录
    """
    page_size = 1000
    page_size_query_param = 'page_size'
    max_page_size = 10000


class ConfigSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Config
        fields = ("id", "key", "configs")


# 文章 - 关于用户 - 公告
class ArticleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Article
        fields = ('title', 'content', 'created_at', 'category')


class AndroidSerializer(serializers.HyperlinkedModelSerializer):
    """
    安卓版本信息
    """
    create_at = serializers.SerializerMethodField()

    class Meta:
        model = AndroidVersion
        fields = ("id", "version", "comment", "upload_url", "is_update", "is_delete", "create_at")

    @staticmethod
    def get_create_at(obj):
        create_at = obj.create_at.strftime("%Y-%m-%d %H:%M:%S")
        # create_time = timezone.localtime(obj.create_at)
        create_time = obj.create_at
        create_at = create_time.strftime("%Y-%m-%d %H:%M:%S")
        return create_at


class DailySettingSerializer(serializers.ModelSerializer):
    """
    每日签到设置
    """

    class Meta:
        model = DailySettings
        fields = ("days", "rewards", "days_delta")
