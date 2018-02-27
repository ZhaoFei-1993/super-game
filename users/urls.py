# -*- coding: UTF-8 -*-
from django.urls import path, include

urlpatterns = [
    path('app/v1/', include('users.app.v1.urls')),
    path('backend/', include('users.backend.urls')),
]
