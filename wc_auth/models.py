from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)
import reversion


@reversion.register()
class Role(models.Model):
    """
    后台角色
    """
    name = models.CharField(verbose_name="角色名称", max_length=50)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="最后更新日期", auto_now=True)

    class Meta:
        ordering = ['updated_at']
        verbose_name = verbose_name_plural = '管理员角色'

    def __str__(self):
        return self.name


class PermissionManager(models.Manager):
    """
    后台权限操作
    """

    def get_role_menu(self, role_id):
        perms = self.model.objects.filter(role_id=role_id)
        permissions = {
            'menu': [],
            'opts': [],
        }
        for perm in perms:
            if perm.permission.find('-') == -1:
                permissions['menu'].append(perm.permission)
            else:
                permissions['opts'].append(perm.permission)
        return permissions


@reversion.register()
class Permission(models.Model):
    """
    后台权限
    """
    role = models.ForeignKey(Role, related_name='permissions', on_delete=models.CASCADE)
    permission = models.CharField(verbose_name="权限", max_length=100)

    objects = PermissionManager()

    class Meta:
        verbose_name = verbose_name_plural = "角色权限"

    def __str__(self):
        return self.permission


class AdminManager(BaseUserManager):
    """
    管理员操作
    """

    def create_user(self, username, password=None):
        if not username:
            raise ValueError("username need")
        user = self.model(
            username=username
        )
        user.set_password(password)
        user.role_id = 1
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None):
        user = self.create_user(username, password)
        user.save(using=self._db)
        return user


class Admin(AbstractBaseUser):
    """
    后台管理员
    1.管理员 2.财务 3.股东
    """
    username = models.CharField(verbose_name="登录账号", max_length=25, unique=True)
    truename = models.CharField(verbose_name="真实姓名", max_length=25)
    telephone = models.CharField(verbose_name="手机号码", max_length=11, unique=True)
    role = models.ForeignKey(Role, related_name='role', on_delete=models.DO_NOTHING)

    USERNAME_FIELD = 'username'
    objects = AdminManager

    def __str__(self):
        return self.username


