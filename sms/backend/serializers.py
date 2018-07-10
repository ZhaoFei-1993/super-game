# -*- coding: UTF-8 -*-
# -*- coding: UTF-8 -*-
from rest_framework import serializers
from users.models import User
from base.validators import PhoneValidator
from sms.models import Sms


class SmsSerializer(serializers.HyperlinkedModelSerializer):
    telephone = serializers.CharField(write_only=True)

    def save(self, **kwargs):
        pass

    class Meta:
        model = Sms
        validators = [PhoneValidator(field='telephone')]
        fields = ("code", "telephone")
