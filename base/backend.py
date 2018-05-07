from rest_framework import generics
from django.conf import settings
from django.http import HttpResponse
from .auth import CCSignatureAuthBackend

from django.core.paginator import Paginator as DjangoPaginator
from django.core.paginator import InvalidPage
from rest_framework.pagination import PageNumberPagination
from django.db import connection
import json


class BaseView(generics.GenericAPIView):
    authentication_classes = (CCSignatureAuthBackend,)

    def get_list_by_sql(self, sql, page_size=10):
        """
        使用原生SQL获取数据
        :param sql:
        :param page_size: 每页显示记录数，默认为10
        :return:
        """
        page = 1
        page_size = page_size
        if 'page' in self.request.GET:
            try:
                page = int(self.request.GET.get('page'))
            except InvalidPage:
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

    @staticmethod
    def response(data):
        """
        接口返回统一处理
        :param data: 
        :return: 
        """
        return HttpResponse(json.dumps(data), content_type='text/json')


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

        page = request.GET.get('page')
        if page is None:
            page = 1

        content = {
            'list': items,
            'pagination': {
                'current': page,
                'pageSize': settings.REST_FRAMEWORK['PAGE_SIZE'],
                'total': results.data.get('count'),
            }
        }
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
