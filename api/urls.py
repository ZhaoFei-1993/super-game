"""api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    # 用户模块路由
    path('user/', include('users.urls')),
    # 竞猜模块路由
    path('quiz/', include('quiz.urls')),
    # 手机短信
    path('sms/', include('sms.urls')),
    # 后台管理模块路由
    path('admin/', include('wc_auth.urls')),
    # utils模块路由
    path('utils/', include('utils.urls')),
    # captcha
    path('captcha/', include('captcha.urls')),
    # config
    path('configs/', include('config.urls')),
    #
    path('chat/', include('chat.urls')),
    #
    path('guess/', include('guess.urls')),
    #
    path('marksix/', include('marksix.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
