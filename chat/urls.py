# -*- coding: UTF-8 -*-
from django.urls import path, include

urlpatterns = [
    path('app/v1/', include('chat.app.v1.urls')),
    path('backend/', include('chat.backend.urls')),
]
