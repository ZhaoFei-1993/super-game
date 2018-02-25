from rest_framework import generics
from django.http import JsonResponse
from rest_framework.response import Response
from .auth import CCSignatureAuthentication
from .code import API_ERROR_MESSAGE

from django.core.paginator import Paginator as DjangoPaginator
from django.core.paginator import InvalidPage
from rest_framework.pagination import PageNumberPagination
from django.db import connection
from collections import OrderedDict


class BaseView(generics.GenericAPIView):
    authentication_classes = (CCSignatureAuthentication, )

    def get_list_by_sql(self, sql, page_size = 10):
        """
        使用原生SQL获取数据
        :param sql: 
        :return: 
        """
        page = 1
        page_size = page_size
        if 'page' in self.request.GET:
            try:
                page = int(self.request.GET.get('page'))
            except Exception:
                pass

        offset = ' LIMIT ' + str((page - 1) * page_size) + ',' + str(page_size)
        sql += offset
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
        return rows

    def paginate_queryset(self, queryset):
        pnp = PageNumberPagination
        page_size = self.request.GET.get('page_size')
        if page_size is None:
            page_size = pnp.page_size
        page_size = int(page_size)
        if page_size < 0 or page_size == 0:
            page_size = pnp.page_size
        if page_size > 100:
            page_size = 100

        pnp.request = self.request
        paginator = DjangoPaginator(queryset, page_size)
        page_number = self.request.GET.get('page')
        if page_number is None:
            page_number = 1

        try:
            pnp.page = paginator.page(page_number)
        except InvalidPage:
            return list()

        return list(pnp.page)

    def get_paginated_response(self, data):
        """Avoid case when self does not have page properties for empty list"""
        if hasattr(self, 'page') and self.page is not None:
            return super(self).get_paginated_response(data)
        else:
            return Response(OrderedDict([
                ('count', None),
                ('next', None),
                ('previous', None),
                ('results', data)
            ]))

    @staticmethod
    def response(data):
        """
        接口返回统一处理
        :param data: 
        :return: 
        """
        response = {}
        for k in data:
            response[k] = data[k]
            if k == 'code' and 'message' not in data:
                response['message'] = API_ERROR_MESSAGE[data['code']]

        return JsonResponse(response)


class CreateAPIView(generics.CreateAPIView, BaseView):
    pass


class ListAPIView(generics.ListAPIView, BaseView):
    pass


class RetrieveAPIView(generics.RetrieveAPIView, BaseView):
    pass


class DestroyAPIView(generics.DestroyAPIView, BaseView):
    pass


class UpdateAPIView(generics.UpdateAPIView, BaseView):
    pass


class ListCreateAPIView(generics.ListCreateAPIView, BaseView):
    pass


class RetrieveUpdateAPIView(generics.RetrieveUpdateAPIView, BaseView):
    pass


class RetrieveDestroyAPIView(generics.RetrieveDestroyAPIView, BaseView):
    pass


class RetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView, BaseView):
    pass


class FormatListAPIView(generics.ListAPIView, BaseView):
    def list(self, request, *args, **kwargs):
        """
        返回列表数据
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')

        content = {'code': 0, 'data': items}
        return self.response(content)


class FormatRetrieveAPIView(generics.RetrieveAPIView, BaseView):
    def get(self, request, *args, **kwargs):
        """
        获取数据详情
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        data = super().get(request, *args, **kwargs)
        item = data.data

        content = {'code': 0, 'data': item}
        return self.response(content)
