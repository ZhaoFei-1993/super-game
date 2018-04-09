from django.db import models

# Create your models here.


class Sms(models.Model):
    NORMAL = 1
    ABNORMAL = 2
    FORGET_PASSWORD = 3

    READY = 1
    SUCCESS = 2
    FAIL = 3

    TYPE_CHOICE = (
        (NORMAL, "绑定手机"),
        (ABNORMAL, "解除手机绑定"),
        (FORGET_PASSWORD, "忘记密保"),
    )

    STATUS_CHOICE = (
        (READY, "等待发送"),
        (SUCCESS, "发送成功"),
        (FAIL, "发送失败"),
    )

    telephone = models.CharField(verbose_name="接收手机号码", max_length=20)
    code = models.CharField(verbose_name="短信验证码", max_length=10, default='')
    message = models.CharField(verbose_name="短信内容", max_length=255)
    type = models.CharField(verbose_name="短信类型", choices=TYPE_CHOICE, max_length=1)
    status = models.CharField(verbose_name="发送状态", choices=STATUS_CHOICE, max_length=1, default=READY)
    feedback = models.CharField(verbose_name="失败反馈", max_length=255)
    is_passed = models.BooleanField(verbose_name="是否通过校验", default=False)
    created_at = models.DateTimeField(verbose_name="发送时间", auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = verbose_name_plural = '短信发送记录表'
