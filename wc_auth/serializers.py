# -*- coding: UTF-8 -*-
from rest_framework import serializers
from .models import Admin, Role, Admin_Operation
from quiz.models import Quiz
from django.utils import timezone
from datetime import datetime
from reversion.models import Revision

class InfoSerialize(serializers.ModelSerializer):
    """
    管理信息
    """
    class Meta:
        model = Admin
        fields = ("id", "username", "truename")


class QuizSerialize(serializers.ModelSerializer):
    """
    竞猜表
    """
    key = serializers.SerializerMethodField()  # mapping to id

    class Meta:
        model = Quiz
        fields = ("key", "host_team", "guest_team", "begin_at", "match_name", "status")

    @staticmethod
    def get_key(obj):
        return obj.id


class RoleListSerialize(serializers.ModelSerializer):
    """
    管理员角色列表
    """
    key = serializers.SerializerMethodField()   # mapping to id

    class Meta:
        model = Role
        fields = ("key", "name")

    @staticmethod
    def get_key(obj):
        return obj.id


class AdminOperationSerialize(serializers.ModelSerializer):

    date = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    pre_value = serializers.SerializerMethodField()
    mod_value = serializers.SerializerMethodField()
    op_object = serializers.CharField(source='mod_version.object_repr')
    comment = serializers.CharField(source='revision.comment')
    user = serializers.CharField(source='admin.username')

    class Meta:
        model = Admin_Operation
        fields = ("id", "date","time", "pre_value", "mod_value", "op_object", "comment", "user")

    @staticmethod
    def cmp_dict(obj, in_first=True):
        if obj.revision.comment in ['PATCH', 'PUT', 'DELETE']:
            mod_v = obj.mod_version.field_dict
            pre_v = obj.pre_version.field_dict
            mod_keys = mod_v.keys()
            pre_keys = pre_v.keys()
            temp_pre={}
            temp_mod={}
            if mod_keys==pre_keys:
                for key in mod_keys:
                    if pre_v[key]!= mod_v[key]:
                        temp_pre[key]=pre_v[key]
                        temp_mod[key]=mod_v[key]
                if in_first:
                    return temp_pre
                else:
                    return temp_mod
            else:
                if in_first:                     # in_first判断是否将第一个参数作为 for in的值
                    for key in pre_keys:
                        if key not in mod_keys or pre_v[key]!=mod_keys[key]:
                            temp_pre[key]= pre_v[key]
                    return temp_pre
                else:
                    for key in mod_keys:
                        if key not in pre_keys or pre_v[key]!=mod_keys[key]:
                            temp_mod[key]= mod_v[key]
                    return temp_mod
        else:
            if in_first:
                return ''
            else:
                return obj.mod_version.field_dict

    @staticmethod
    def get_pre_value(obj):
        return AdminOperationSerialize.cmp_dict(obj)

    @staticmethod
    def get_mod_value(obj):
        return AdminOperationSerialize.cmp_dict(obj,in_first=False)

    @staticmethod
    def get_date(obj):
        # date_data = timezone.localtime(obj.revision.date_created)
        date_data = obj.revision.date_created
        date = datetime.strftime(date_data, '%Y-%m-%d')
        return date
    #
    # @staticmethod
    # def get_op_object(obj):
    #     object_text = obj.mod_version.object_repr.replace('object ','pk=').replace('(','').replace(')','')
    #     return object_text

    @staticmethod
    def get_time(obj):
        # time_data = timezone.localtime(obj.revision.date_created)
        time_data = obj.revision.date_created
        time = time_data.strftime('%H:%M:%S')
        return time



