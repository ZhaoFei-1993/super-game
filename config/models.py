# -*- coding: UTF-8 -*-
from django.db import models
from django.conf import settings
import json
import os
from django.core import serializers
import reversion


class ConfigManager(models.Manager):
    """
    配置数据缓存操作
    """
    cache_file = settings.CACHE_DIR + '/config'
    cache_type = 'json'
    format_type = 'kv'

    def set(self):
        """
        写入缓存
        :return: 
        """
        if not os.path.exists(settings.CACHE_DIR):
            os.mkdir(settings.CACHE_DIR, 0o777)

        data = Config.objects.all()
        config_data = serializers.serialize(self.cache_type, data)  # 序列化所有配置项数据
        config_cache = open(self.cache_file, 'w')
        config_cache.write(config_data)
        config_cache.close()

    def format(self, data):
        """
        格式化数据格式，目前采用key-value形式返回
        :param data: 
        :return: 
        """
        cache_data = {}

        if self.format_type == 'kv':
            for d in data:
                fields = d['fields']
                cache_data[fields['key']] = fields['configs']

        return cache_data

    def get_all(self):
        """
        获取所有配置数据
        :return: JSON数据
        """
        if not os.path.exists(self.cache_file):
            self.set()

        cache_config = open(self.cache_file, 'r')
        cache_data = json.loads(cache_config.read())
        cache_config.close()

        return self.format(cache_data)

    def get(self, key):
        """
        获取指定配置项值
        :param key: 配置项key，如：email.account
        :return: 
        """
        configs = self.get_all()
        return configs[key]


@reversion.register()
class Config(models.Model):
    """
    配置项说明：

    邮件配置
    email.
        provider: 'qq',             邮件服务商: qq => QQ企业邮箱，netease => 网易免费企业邮箱
        account: '',                邮件账号
        password: '',               邮件密码
        required_validate: 'no'     是否绑定邮箱需要验证

    短信配置
    message.
        provider: 'mxtong',         短信服务商：mxtong => 麦讯通
        account: '',                账号
        sub_account: '',            子账号
        password: '',               密码
        daily_limit: '',            每日发送限制
        required_validate: 'no'     绑定手机需要验证

    站点配置
    site.
        name: '',                   站点名称
        index: '',                  站点首页
        icon: '',                   网站图标
        short_name: ''              网站简称

    全局设置
    setting.
        exp_charge: '',             充值经验（%）
        exp_bet: '',                下注经验（%）
        exp_create: '',             擂主经验
        exp_sign: '',               签到经验
        coin_invite: '',            邀请返币
        coin_invite_limit: '',      返金上限
        create_fee: '',             系统收费
        create_deposit: '',         擂主保证金
        create_require: '',         发题积分要求
        sign_coin: '',              签到初始猜币
        sign_coin_step: '',         签到递增猜币
        sign_coin_limit: '',        签到封顶猜币
        return_rate: '',            返奖率（%）
        max_rate: '',               最大赔率（%）
        min_rate: ''                最小赔率（%）

    微信设置
    wechat.
        appid: '',                  AppID
        secret: '',                 APP Secret
        token: '',                  Token
        subscribe_reply: '',        关注回复消息
        guess: '',                  竞猜结果通知
        winner: ''                  擂主结果通知

    接口开关
    interface.
        registered：'',               注册开关,0关闭|1开启
        betting:''，                  下注开关,0关闭|1开启
        competition:''，              比赛开关,0关闭|1开启
        quizcomment:''，              竞猜评论开关,0关闭|1开启

    赠送猜币
    presented.
        register_isOn:0, //注册送猜币开关选项
        present_coins_register:0, //注册时送猜币
        login_present_isOn:0,  //登录送猜币开关选项
        present_coins: '1|0|',         //登录时送猜币
        present_diamonds_isOn:0,    //注册送钻石开关选项
        present_diamonds:0,          //注册送钻石数量
        present_diamonds_start:'2017-09-31 12:30:30' //注册赠送钻石开始时间
        present_diamonds_end:'2017-10-02 12:30:30'  //注册赠送钻石结束时间

    Android版本控制
    androidcontrol.
        apk_version:1.0.0,      apk版本号
        apk_content:'',            apk版本内容
        apk_url:''                     apk下载内容

    """
    key = models.CharField("配置项key值", max_length=32, unique=True)
    configs = models.CharField("配置数值", max_length=200)

    objects = ConfigManager()

    def __str__(self):
        return self.key


@reversion.register()
class AndroidVersion(models.Model):
    """
    安卓版本管理
    """
    version = models.CharField("安卓版本号", max_length=20)
    upload_url = models.CharField("apk地址", max_length=150)
    is_update = models.BooleanField("是否已更新", max_length=2, default=False)
    is_delete = models.BooleanField("是否已删除", max_length=2, default=False)
    create_at = models.DateTimeField("发布时间", auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "安卓版本管理"


# 审核状态
@reversion.register()
class Inspect_status(models.Model):
    INSPECT = 1
    NORMAL = 2

    STATUS_CHOICE = (
        (INSPECT, "正在审核"),
        (NORMAL, "正常状态")
    )
    category = models.CharField(verbose_name="状态", choices=STATUS_CHOICE, max_length=1, default=NORMAL)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "审核状态"


# 文章 - 关于我们 - 公告
@reversion.register()
class Article(models.Model):
    ABOUT_WE = 1  # 关于我们

    CATEGORY_CHOICE = (
        (ABOUT_WE, "关于我们"),
    )

    title = models.CharField(verbose_name="竞赛标题", max_length=100)
    content = models.TextField(verbose_name="文章内容")
    created_at = models.DateTimeField('date published')
    category = models.CharField(verbose_name="状态", choices=CATEGORY_CHOICE, max_length=1, default=ABOUT_WE)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "文章-关于我们-公告"
