# -*- coding: UTF-8 -*-
from django.urls import path, include

urlpatterns = [
    path('app/v1/', include('promotion.app.v1.urls')),
]
