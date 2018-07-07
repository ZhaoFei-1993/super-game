# -*- coding: UTF-8 -*-
from django.urls import path, include

urlpatterns = [
    path('app/v1/', include('guess.app.v1.urls')),
    path('backend/', include('guess.backend.urls')),
]
