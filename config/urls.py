# -*- coding: UTF-8 -*-
from django.urls import path

from .views import *

urlpatterns = [
    path('', view=ConfigListView.as_view(), name="config-list"),
    path('article/', view=ArticleView.as_view(), name="config-article"),
    path('versions/', view=VersionView.as_view(), name="config-android"),
    path('app_setting/', view=AppSetting.as_view(), name="config-app_setting"),
    path('daily_setting/', view=DailySettingView.as_view(), name="config-daily_setting")
]
