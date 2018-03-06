# -*- coding: UTF-8 -*-
from rest_framework import serializers
from ...models import User



class UserSerializer(serializers.HyperlinkedModelSerializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    @staticmethod
    def validate_password(value):
        if len(value) < 6:
            raise serializers.ValidationError("password can't less than 6")
        return value

    @staticmethod
    def validate_username(value):
        user = User.objects.filter(username=value)
        if len(user) > 0:
            raise serializers.ValidationError("username exists")
        return value

    def save(self, **kwargs):
        user = super().save(**kwargs)
        if 'password' in self.validated_data:
            password = self.validated_data['password']
            user.set_password(password)
            user.save()
        return user

    def to_representation(self, instance):
        return super().to_representation(instance)

    class Meta:
        model = User
        fields = ("id", "username", "password", "avatar")


class ListSerialize(serializers.ModelSerializer):
    """
    用户列表
    """
    class Meta:
        model = User
        fields = ("id", "nickname")


class UserInfoSerializer(serializers.ModelSerializer):
    """
    用户信息
    """
    class Meta:
        model = User
        fields = ("id", "nickname", "avatar", "meth", "ggtc", )


class UserSerializer(serializers.ModelDurationField):
    """
    放着
    """

    pass