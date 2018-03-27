# -*- coding: UTF-8 -*-
# encoding: utf-8

"""
@author: Rex Lin
@contact: system@xiqjv.com
@file: custom_backend.py
@time: 2017/4/10
"""

from django.contrib.auth.backends import ModelBackend
from wc_auth.models import Admin


class UsernameOrIdCardBackend(ModelBackend):
    def authenticate(self, username=None, password=None, **kwargs):
        try:
            # Try to fetch the user by searching the username field
            user = Admin.objects.get(username=username)
            if user.check_password(password):
                return user
        except Admin.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            Admin().set_password(password)

