# -*- coding: UTF-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    # html5 config
    path('h5/', views.Html5ConfigView.as_view(), name="app-html5-config"),
    path('web/domain/', views.WebDomainConfigView.as_view(), name="web-domain-config"),
]
