# -*- coding: UTF-8 -*-
import json
import os

from django.http import HttpResponse
from config.models import Config, Article, AndroidVersion
from config.serializers import ConfigSerializer, ArticleSerializer, LargeResultsSetPagination, AndroidSerializer
from rest_framework import status
from django.http import JsonResponse

from api.settings import BASE_DIR
from utils.functions import value_judge
from base.exceptions import ParamErrorException
import base.code as error_code
from base.backend import ListCreateAPIView, RetrieveUpdateDestroyAPIView


# from base.log_operation import LogOperation

# from wcc_admin.models import SysLog
# from rest_framework.generics import ListCreateAPIView


class ConfigListView(ListCreateAPIView):
    """
    get:
    获取系统配置数据

    post:
    保存系统配置数据
    """
    queryset = Config.objects.all()
    serializer_class = ConfigSerializer
    pagination_class = LargeResultsSetPagination

    def post(self, request, *args, **kwargs):
        # TODO: add insert one logic
        request_data = request.data
        configs = [Config(**item) for item in request_data]

        for config in configs:
            if not config.configs:
                content = {'status': status.HTTP_417_EXPECTATION_FAILED}
                return HttpResponse(json.dumps(content), content_type='text/json')

        # delete config values
        Config.objects.filter(key__in=configs).delete()

        # insert into database
        Config.objects.bulk_create(configs)

        # 写日志
        # content_log = ''
        # for lst in request_data:
        #     if lst['key'].startswith('androidcontrol'):
        #         content_log += '配置键：' + lst['key'] + ",配置值：" + lst['configs'] + ";"
        #
        # LogOperation.save_log(SysLog.BACKSTAGE, SysLog.NORMAL, content_log, self.request.user.id)

        # write to cache file
        Config.objects.set()

        content = {'status': status.HTTP_201_CREATED}
        return HttpResponse(json.dumps(content), content_type='text/json')


# 文章 - 关于 - 公告
class ArticleView(ListCreateAPIView):
    """
    允许查看和编辑NewMail的 API endpoint
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer


class VersionView(ListCreateAPIView, RetrieveUpdateDestroyAPIView):
    """
    安卓版本信息
    """
    queryset = AndroidVersion.objects.filter(is_delete=False).order_by('-create_at')
    serializer_class = AndroidSerializer

    def list(self, request, *args, **kwargs):
        if "id" in request.GET:
            id_x = request.GET.get("id")
            item = AndroidVersion.objects.get(id=id_x)
            return self.response({'status': 200, 'results': {'id': item.id,
                                                             'version': item.version,
                                                             'is_update': item.is_update
                                                             }})
        else:
            return super().list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        values = value_judge(request, 'files', 'is_update', 'version')
        if values == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        files = request.data.get('files').split('\\')[-1]
        is_update = request.data.get('is_update')
        version = request.data.get('version')
        config = AndroidVersion()
        version_exist = AndroidVersion.objects.filter(version__contains=str(version))
        if version_exist:
            return JsonResponse({"Error":"Version Existed!"},status=status.HTTP_400_BAD_REQUEST)
        else:
            config.version = version
        config.version = version
        config.is_update = is_update
        config.upload_url = os.path.join(BASE_DIR, "uploads/", files)
        config.save()
        return self.response({"code": 0})

    def patch(self, request, *args, **kwargs):
        index = request.data.get('id')
        if not index:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        item = AndroidVersion.objects.get(id=index)
        if "files" in request.data:
            files = request.data.get("files")
            if files:
                files = files.split('\\')[-1]
                item.upload_url = os.path.join(BASE_DIR, "uploads/", files)
        if "version" in request.data:
            version = request.data.get('version')
            version_exist = AndroidVersion.objects.filter(version__contains=str(version))
            if version_exist:
                return JsonResponse({'Error': "Version Exist!"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                item.version = version
        if "is_update" in request.data:
            item.is_update = int(request.data.get('is_update'))
        item.save()
        return self.response({"code": 0})

    def delete(self, request, *args, **kwargs):
        ad_id = request.data.get("id")
        print(ad_id)
        if not ad_id:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        item = AndroidVersion.objects.get(id=ad_id)
        item.is_delete = 1
        item.save()
        return JsonResponse({}, status=status.HTTP_200_OK)
