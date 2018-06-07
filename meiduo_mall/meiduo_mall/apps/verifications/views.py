from rest_framework.views import APIView
from django.http.response import HttpResponse
from django_redis import get_redis_connection
from redis.exceptions import RedisError
from rest_framework.response import Response
from rest_framework import status
import logging
import random
from rest_framework.generics import GenericAPIView

from . import constants
from meiduo_mall.libs.captcha.captcha import captcha
from celery_tasks.sms import tasks as sms_tasks
from users.models import User
from . import serializers

# Create your views here.

logger = logging.getLogger("django")


class ImageCodeView(APIView):
    """
    图片验证码
    """

    def get(self, request, image_code_id):
        """
        获取图片验证码
        """

        # 生成验证码图片
        text, image = captcha.generate_captcha()

        redis_conn = get_redis_connection("verify_codes")
        redis_conn.setex("img_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        # 固定返回验证码图片数据，不需要REST framework框架的Response帮助我们决定返回响应数据的格式
        # 所以此处直接使用Django原生的HttpResponse即可
        return HttpResponse(image, content_type="images/jpg")


class SMSCodeView(GenericAPIView):
    """
    短信验证码
    """
    serializer_class = serializers.ImageCodeCheckSerializer

    def get(self, request, mobile):
        """
        创建短信验证码
        """
        # 判断图片验证码, 判断是否在60s内
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # 生成短信验证码
        sms_code = "%06d" % random.randint(0, 999999)

        # 保存短信验证码与发送记录
        redis_conn = get_redis_connection('verify_codes')
        pl = redis_conn.pipeline()
        pl.setex("sms_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex("send_flag_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()

        # 发送短信验证码
        sms_code_expires = str(constants.SMS_CODE_REDIS_EXPIRES // 60)
        sms_tasks.send_sms_code.delay(mobile, sms_code, sms_code_expires)

        return Response({"message": "OK"})

