# -*- coding: UTF-8 -*-
from django.urls import path, include

urlpatterns = [
    path('app/v1/', include('dragon_tiger.app.v1.urls')),
    # path('backend/', include('dragon_tiger.backend.urls')),
]
