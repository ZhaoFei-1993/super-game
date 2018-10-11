"""chnl URL Configuration

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
from django.conf.urls import url
from .consumers import QuizConsumer
from dragon_tiger.dragontigerconsumer import DragonTigerConsumer
from baccarat.baccaratconsumer import BaccaratConsumer
from marksix.mark_six_consumers import MarkSixConsumer
from guess.guess_consemers import GuessConsumer

websocket_urlpatterns = [
    # 球赛推送
    url(r'^quiz/', QuizConsumer),
    # 赌场推送
    url(r'^dragon_tiger/', DragonTigerConsumer),
    # 百家乐
    url(r'^baccarat/', BaccaratConsumer),
    # mark_six
    url(r'^mark_six/', MarkSixConsumer),
    # 股指
    url(r'^guess/', GuessConsumer),
]
