# -*- coding: UTF-8 -*-
import json

from django.http import HttpResponse
from config.models import Config, Article, AndroidVersion
from config.serializers import ConfigSerializer, ArticleSerializer, LargeResultsSetPagination, AndroidSerializer, \
    DailySettingSerializer
from rest_framework import status
from django.http import JsonResponse

from api.settings import MEDIA_DOMAIN_HOST
from utils.functions import value_judge, genarate_plist
from base.exceptions import ParamErrorException
import base.code as error_code
from base.backend import ListCreateAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView
from users.models import UserSettingOthors, User, DailySettings, Coin
import reversion
from django.contrib import admin
from utils.functions import reversion_Decorator
from datetime import datetime
from url_filter.integrations.drf import DjangoFilterBackend

admin.autodiscover()


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

    @reversion_Decorator
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
    系统设置->安卓版本管理
    """
    queryset = AndroidVersion.objects.filter(is_delete=False).order_by('-create_at')
    serializer_class = AndroidSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['mobile_type']

    def list(self, request, *args, **kwargs):
        if "id" in request.GET:
            id_x = request.GET.get("id")
            try:
                item = AndroidVersion.objects.get(id=id_x)
            except Exception:
                JsonResponse({'Error': 'Instance Not Exist!'}, status=status.HTTP_400_BAD_REQUEST)
            serialize = AndroidSerializer(item)
            return self.response({'status': 200, 'results': serialize.data})
        else:
            return super().list(request, *args, **kwargs)

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        values = value_judge(request, 'files', 'is_update', 'version', 'comment', 'mobile_type')
        if values == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        files = request.data.get('files').split('\\')[-1]
        is_update = request.data.get('is_update')
        version = request.data.get('version')
        comment = request.data.get('comment')
        comment_en = request.data.get('comment_en')
        mobile_type = request.data.get('mobile_type')
        mobile_plugin = request.data.get('mobile_plugin')
        config = AndroidVersion()
        if str(mobile_type).upper() == 'IOS':
            type = 1
        else:
            type = 0
        version_exist = AndroidVersion.objects.filter(version=version, is_delete=0, mobile_type=type).exists()
        if version_exist:
            return JsonResponse({"Error": "Version Existed!"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            config.version = version
        config.is_update = is_update
        config.comment = comment
        config.comment_en = comment_en
        config.mobile_type = type
        config.mobile_plugin = mobile_plugin
        date = datetime.now().strftime('%Y%m%d')
        config.upload_url = ''.join([MEDIA_DOMAIN_HOST, "/apps/", mobile_type, '/', date + '_' + files])
        if type == 1:
            plist_url = genarate_plist(version, config.upload_url)
            config.plist_url = plist_url
        config.save()
        return self.response({"code": 0})

    @reversion_Decorator
    def patch(self, request, *args, **kwargs):
        index = request.data.get('id')
        if not index:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        try:
            item = AndroidVersion.objects.get(id=index)
        except item.DoesNotExist:
            JsonResponse({'Error': 'Instance Not Exist'}, status=status.HTTP_400_BAD_REQUEST)
        mobile_type = request.data.get('mobile_type')
        if str(mobile_type).upper() == "IOS":
            type = 1
        else:
            type = 0
        if "files" in request.data:
            files = request.data.get("files")
            if files:
                files = files.split('\\')[-1]
                date = datetime.now().strftime('%Y%m%d')
                item.upload_url = ''.join([MEDIA_DOMAIN_HOST, "/apps/", mobile_type, '/', date + '_' + files])
                if type == 1:
                    plist_url=genarate_plist(item.version, item.upload_url)
                    item.plist_url=plist_url
        if "version" in request.data:
            version = request.data.get('version')
            version_exist = AndroidVersion.objects.filter(version=version, is_delete=0, mobile_type=type)
            if version_exist:
                return JsonResponse({'Error': "Version Exist!"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                item.version = version
        if "is_update" in request.data:
            item.is_update = int(request.data.get('is_update'))
        if "comment" in request.data:
            item.comment = request.data.get('comment')
        if "comment_en" in request.data:
            item.comment_en = request.data.get('comment_en')
        if "recommend" in request.data:
            item.mobile_plugin = request.data.get('mobile_plugin')
        item.save()
        return self.response({"code": 0})

    @reversion_Decorator
    def delete(self, request, *args, **kwargs):
        ad_id = request.data.get("id")
        if not ad_id:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        try:
            item = AndroidVersion.objects.get(id=ad_id)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        item.is_delete = 1
        item.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


class AppSetting(RetrieveUpdateDestroyAPIView, ):
    """
    系统设置->App设置
    """

    def retrieve(self, request, *args, **kwargs):
        if "reg_type" not in request.query_params:
            return JsonResponse({"Error": "ParamError"}, status=status.HTTP_400_BAD_REQUEST)
        r_type = int(request.query_params.get('reg_type'))
        others = UserSettingOthors.objects.filter(reg_type=r_type)
        if not others.exists():
            other_data = {
                "about": '',
                "helps": '',
                "sv_contractus": '',
                "pv_contractus": ''
            }
            exist = 0
        else:
            other_data = {
                "about": others[0].about,
                "helps": others[0].helps,
                "sv_contractus": others[0].sv_contractus,
                "pv_contractus": others[0].pv_contractus
            }
            exist = 1
        seletions = {}
        for v in User.REGISTER_TYPE:
            x = str(v[0])
            seletions[x] = v[1]
        system_m = Config.objects.filter(key="system_maintenance")
        if not system_m.exists():
            config_data = 0
        else:
            config_data = {"system_maintenance": system_m[0].configs}
        results = dict(**config_data, **other_data)
        data = {
            "seletions": seletions,
            'is_exist': exist,
            "results": results
        }
        return JsonResponse(data, status=status.HTTP_200_OK)

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        fields_in = ('reg_type', 'system_maintenance', 'about', 'helps', 'sv_contractus', 'pv_contractus')
        value = [x for x in request.data.keys() if x in fields_in]
        if len(value) != len(fields_in):
            lost_fields = list(set(fields_in) - set(value))
            losts = ','.join(lost_fields)
            return JsonResponse({'Error': 'Lost Fields: %s' % losts}, status=status.HTTP_400_BAD_REQUEST)
        values = dict(request.data)
        config = Config.objects.filter(key="system_maintenance")
        if config.exists():
            if config[0].configs != int(values["system_maintenance"]):
                config[0].configs = int(values["system_maintenance"])
        values.pop("system_maintenance")
        reg_type = int(values['reg_type'])
        values['reg_type'] = reg_type
        others = UserSettingOthors(**values)
        others.save()
        return JsonResponse({}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def patch(self, request, *args, **kwargs):
        if "reg_type" not in request.data:
            return JsonResponse({"Error": "ParamError"}, status=status.HTTP_400_BAD_REQUEST)
        r_type = int(request.data.pop('reg_type'))
        try:
            others = UserSettingOthors.objects.get(reg_type=r_type)
        except Exception:
            return JsonResponse({'Error': 'No UserSettingOthors data'}, status=status.HTTP_400_BAD_REQUEST)
        filed_s = ["system_maintenance", "about", "helps", "sv_contractus", "pv_contractus"]
        for key, value in request.data.items():
            if key not in filed_s:
                return JsonResponse({"Error": "Not Allow Field"}, status=status.HTTP_400_BAD_REQUEST)
            if key == "system_maintenance":
                try:
                    sm = Config.objects.get(key='system_maintenance')
                except Exception:
                    return JsonResponse({'Error': 'No Config data'}, status=status.HTTP_400_BAD_REQUEST)
                sm.configs = int(value)
                sm.save()
            else:
                if key == 'about':
                    others.about = value
                elif key == 'helps':
                    others.helps = value
                elif key == 'sv_contractus':
                    others.sv_contractus = value
                else:
                    others.pv_contractus = value
                others.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


class DailySettingView(ListCreateAPIView):
    """
    每日签到设置
    """
    queryset = DailySettings.objects.filter().order_by('days')
    serializer_class = DailySettingSerializer

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        return JsonResponse({"results": items}, status=status.HTTP_200_OK)
        # return self.response({"status":status.HTTP_200_OK,"results":data})

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        if request.data:
            items = []
            for index, x in enumerate(request.data):
                for y in ['days', 'rewards', 'days_delta']:
                    value = (True if (y not in x) else False)
                if value:
                    return JsonResponse({"Error": "%d Item ParamError" % (index + 1)},
                                        status=status.HTTP_400_BAD_REQUEST)
                x['admin_id'] = request.user.id
                x['coin_id'] = 1
                items.append(x)
            DailySettings.objects.all().delete()
            for item in items:
                new_item = DailySettings(**item)
                new_item.save()
            return JsonResponse({}, status=status.HTTP_200_OK)
