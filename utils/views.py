# -*- coding: UTF-8 -*-
import os

from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework import decorators, status, parsers, renderers
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.authtoken.models import Token

from captcha.models import CaptchaStore
from captcha.helpers import captcha_image_url
from django.conf import settings

from wc_auth.models import Permission
from .models import Image
from .forms import ImageForm
from api.settings import MEDIA_ROOT
from datetime import datetime


class ObtainAuthToken(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        if settings.IS_CAPTCHA_ENABLE:
            if 'key' not in self.request.data or 'challenge' not in self.request.data:
                return Response("need captcha and key", status=status.HTTP_400_BAD_REQUEST)
            key = request.data.pop("key")
            challenge = request.data.pop("challenge").upper()
            try:
                captcha = CaptchaStore.objects.get(challenge=challenge, hashkey=key)
                captcha.delete()
            except CaptchaStore.DoesNotExist:
                return Response("wrong captcha", status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})


@decorators.api_view()
def sitemap(request):
    return Response({
        "login": reverse("backend-login", request=request),
        "captcha": reverse("backend-captcha", request=request),
        "profile": reverse("backend-profile", request=request),
        "sidebar": reverse("backend-sidebar-control", request=request),
        "upload": reverse("backend-upload", request=request),
        "quiz-category": reverse("quiz-category-list", request=request),
        "quizs": reverse("quiz-list", request=request),
        # "coinlock": reverse("backend-coin-lock", request=request),
        "configs": reverse("config-list", request=request),
        "upload_file": reverse("backend-upload-file", request=request),
        "currency": reverse("backend-coin-currency", request=request),
        "userlock": reverse("backend-user-lock", request=request),
        "usercoin": reverse("backend-user-coin", request=request),
        "users": reverse("backend-user-list", request=request),
    })


@decorators.api_view()
def captcha_generate(request):
    response = {
        "key": CaptchaStore.generate_key(),
    }
    response["url"] = "https://" + request.get_host() + captcha_image_url(response["key"])
    return Response(response)


@decorators.api_view()
def sidebar_control(request):
    # auth = CCSignatureAuthBackend()
    # auth.authenticate(request)

    permissions = Permission.objects.get_role_menu(role_id=request.user.role_id)

    return Response(permissions)


@csrf_exempt
def upload(request):
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        safe_image_type = request.FILES['image'].name.split('.', 1)[1] in ('jpg', 'png', 'jpeg')
        if safe_image_type:
            if form.is_valid():
                new_doc = Image(image=request.FILES['image'])
                new_doc.save()
                # url = ""

                print('upload')
                print("MEDIA_DOMAIN_HOST值：" + settings.MEDIA_DOMAIN_HOST)
                print('new_doc.file.url值:' + new_doc.image.url)

                # if not settings.DEBUG:
                #     url = url.replace('/images', '')
                # else:
                # url = settings.MEDIA_DOMAIN_HOST + new_doc.image.url
                url = settings.MEDIA_DOMAIN_HOST + new_doc.image.url.replace('uploads/', '')

                print("上传的图片地址：" + url)

                return JsonResponse({
                    "url": url,
                    "submit": new_doc.image.url
                }, status=201)
        else:
            return JsonResponse({}, status=400)


@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        if 'files' not in request.FILES:
            return JsonResponse({"Error": "File Not Fount!"}, status=status.HTTP_400_BAD_REQUEST)
        files = request.FILES.get('files')
        if not files.chunks():
            return JsonResponse({"Error": "Empty File!"}, status=status.HTTP_400_BAD_REQUEST)
        file_type = files.name.split('.')[-1]
        if file_type == 'ipa':
            type = 'IOS'
        else:
            type = 'Android'
        if file_type not in ['apk', 'ipa']:
            return JsonResponse({"Error": "Upload File Type Error!"}, status=status.HTTP_400_BAD_REQUEST)
        date = datetime.now().strftime('%Y%m%d')
        media_android = MEDIA_ROOT + 'apps/Android'
        media_ios = MEDIA_ROOT + 'apps/IOS'
        if not os.path.exists(media_android):
            os.makedirs(media_android)
        if not os.path.exists(media_ios):
            os.makedirs(media_ios)
        if type == 'IOS':
            save_file = os.path.join(media_ios, date + '_' + files.name)
        else:
            save_file = os.path.join(media_android, date + '_' + files.name)
        with open(save_file, 'wb') as f:
            for line in files.chunks():
                f.write(line)
        return JsonResponse({'m_type': type}, status=201)
