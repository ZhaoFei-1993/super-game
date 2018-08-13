from django.db import models


# Create your models here.


class Sms(models.Model):
    NORMAL = 1
    ABNORMAL = 2
    FORGET_PASSWORD = 3
    REGISTER = 4
    FORGET_REGISTER = 5
    PROVING_PASSWORD = 6
    BAKEND_CHANGE_MESSAGE = 7
    CHANGE_REGISTER = 8

    READY = 1
    SUCCESS = 2
    FAIL = 3

    TYPE_CHOICE = (
        (NORMAL, "绑定手机"),
        (ABNORMAL, "解除手机绑定"),
        (FORGET_PASSWORD, "忘记密保"),
        (REGISTER, "用户注册"),
        (FORGET_REGISTER, "忘记密码"),
        (PROVING_PASSWORD, "验证密保"),
        (BAKEND_CHANGE_MESSAGE, '后台修改密码'),
        (CHANGE_REGISTER, '修改密码')
    )

    STATUS_CHOICE = (
        (READY, "等待发送"),
        (SUCCESS, "发送成功"),
        (FAIL, "发送失败"),
    )

    area_code = models.IntegerField(verbose_name="手机区号", default=86)
    telephone = models.CharField(verbose_name="接收手机号码", max_length=20)
    code = models.CharField(verbose_name="短信验证码", max_length=10, default='')
    message = models.CharField(verbose_name="短信内容", max_length=255)
    type = models.CharField(verbose_name="短信类型", choices=TYPE_CHOICE, max_length=1)
    status = models.CharField(verbose_name="发送状态", choices=STATUS_CHOICE, max_length=1, default=READY)
    feedback = models.CharField(verbose_name="失败反馈", max_length=255)
    degree = models.IntegerField(verbose_name="校验次数", default=0)
    is_passed = models.BooleanField(verbose_name="是否通过校验", default=False)
    created_at = models.DateTimeField(verbose_name="发送时间", auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = verbose_name_plural = '短信发送记录表'
