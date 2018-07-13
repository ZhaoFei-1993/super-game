# -*- coding: UTF-8 -*-
from django.urls import path, include

urlpatterns = [
    path('app/v1/', include('marksix.app.v1.urls')),
    path('backend/', include('marksix.backend.urls')),
]
