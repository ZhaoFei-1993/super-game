# -*- coding: UTF-8 -*-
# encoding: utf-8

"""
@author: h3l
@contact: xidianlz@gmail.com
@file: filter.py
@time: 2017/2/21 17:49
"""

from django_filters import filters
from django_filters.fields import Lookup

from django.utils import six
from django import forms


class CustomBaseFilter(filters.Filter):
    def filter(self, qs, value):
        if isinstance(value, Lookup):
            lookup = six.text_type(value.lookup_type)
            value = value.value
        else:
            lookup = self.lookup_expr
        if value in filters.EMPTY_VALUES:
            return qs
        if self.distinct:
            qs = qs.distinct()
        res = ""
        for i in value:
            if ord(i) > 127:
                res += "\\u" + str(hex(ord(i)))[2:]
            else:
                res += i
        value = res

        qs = self.get_method(qs)(**{'%s__%s' % (self.name, lookup): value})
        return qs


class JsonFilter(CustomBaseFilter):
    field_class = forms.CharField
