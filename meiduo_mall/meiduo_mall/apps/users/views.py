from rest_framework.generics import GenericAPIView
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django_redis import get_redis_connection
from rest_framework.decorators import detail_route
import logging
import re
from rest_framework_jwt.views import ObtainJSONWebToken
from rest_framework.permissions import IsAuthenticated

from .models import User, Address
from .serializers import UserDetailSerializer, CreateUserSerializer, ResetPasswordSerializer, UserAddressSerializer, \
    AddressTitleSerializer, AddUserBrowsingHistorySerializer
from .serializers import EmailSerializer, ChangePasswordSerializer
from meiduo_mall.utils.permissions import IsOwner
from verifications.utils import check_image_code
from celery_tasks.email.tasks import send_verify_email
from .utils import get_user_by_account
from . import constants
from goods.models import SKU
from goods.serializers import SKUSerializer
from carts.utils import merge_cart_cookie_to_redis


# Create your views here.
logger = logging.getLogger('django')


class UserViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    """
    用户信息
    """
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateUserSerializer
        else:
            return UserDetailSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        else:
            return [IsOwner()]

    # # 重置密码的另一种实现方案
    # @detail_route(methods=['post'])
    # def password(self, request, pk=None):
    #     user = self.get_object()
    #     context = self.get_serializer_context()
    #     serializer = ResetPasswordSerializer(data=request.data, instance=user, context=context)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response(serializer.data)

    @detail_route(methods=['post'])
    def email(self, request, pk=None):
        """
        保存邮箱
        """
        user = self.get_object()
        serializer = EmailSerializer(data=request.data, instance=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # 生成验证邮箱的url
        verify_url = user.generate_verify_email_url()

        # 发送验证邮箱的邮件
        send_verify_email.delay(user.email, verify_url)

        return Response(serializer.data)


class UsernameCountView(APIView):
    """
    用户名数量
    """
    def get(self, request, username):
        """
        获取指定用户名数量
        """
        count = User.objects.filter(username=username).count()

        data = {
            'username': username,
            'count': count
        }

        return Response(data)


class MobileCountView(APIView):
    """
    手机号数量
    """
    def get(self, request, mobile):
        """
        获取指定手机号数量
        """
        count = User.objects.filter(mobile=mobile).count()

        data = {
            'mobile': mobile,
            'count': count
        }

        return Response(data)


class SMSTokenView(APIView):
    """
    用户帐号发送短信token
    """
    def get(self, request, account):
        """
        获取指定帐号的发送短信的token
        """
        # 判断图片验证码
        response = check_image_code(request)
        if response is not None:
            return response

        user = get_user_by_account(account)
        if user is None:
            return Response({'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 生成发送短信的access_token
        access_token = user.generate_send_sms_code_token()

        # 处理手机号
        mobile = re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', user.mobile)
        return Response({'mobile': mobile, 'access_token': access_token})


class PasswordTokenView(APIView):
    """
    用户帐号设置密码的token
    """
    def get(self, request, account):
        """
        根据用户帐号获取修改密码的token
        """
        # 验证短信验证码
        sms_code = request.query_params.get('code')
        if not sms_code:
            return Response({'message': '缺少短信验证码'}, status=status.HTTP_400_BAD_REQUEST)

        # 获取user
        user = get_user_by_account(account)
        if user is None:
            return Response({'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get('sms_%s' % user.mobile)
        if real_sms_code is None:
            return Response({'message': '无效的短信验证码'}, status=status.HTTP_400_BAD_REQUEST)
        if sms_code != real_sms_code.decode():
            return Response({'message': '短信验证码错误'}, status=status.HTTP_400_BAD_REQUEST)

        # 生成修改用户密码的access token
        access_token = user.generate_set_password_token()

        return Response({'user_id': user.id, 'access_token': access_token})


class PasswordViewSet(mixins.UpdateModelMixin, GenericViewSet):
    """
    用户密码
    """
    queryset = User.objects.all()

    def get_permissions(self):
        """
        设置权限
        """
        if self.action == 'update':
            return [IsOwner()]
        else:
            return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.action == 'create':
            return ResetPasswordSerializer
        else:
            return ChangePasswordSerializer

    def create(self, request, *args, **kwargs):
        """
        重置用户密码
        """
        return self.update(request, *args, **kwargs)


class VerifyEmailView(APIView):
    """
    邮箱验证
    """
    def get(self, request):
        # 获取token
        token = request.query_params.get('token')
        if not token:
            return Response({'message': '缺少token'}, status=status.HTTP_400_BAD_REQUEST)

        # 验证token
        user = User.check_verify_email_token(token)
        if user is None:
            return Response({'message': '链接信息无效'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            user.email_active = True
            user.save()
            return Response({'message': 'OK'})


class UserAddressViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, GenericViewSet):
    """
    用户地址新增与修改
    """
    serializer_class = UserAddressSerializer
    permissions = [IsOwner]
    lookup_url_kwarg = 'address_id'

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    def list(self, request, *args, **kwargs):
        """
        用户地址列表数据
        """
        queryset = self.get_queryset()
        serializer = UserAddressSerializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,
            'addresses': serializer.data,
        })

    def create(self, request, *args, **kwargs):
        """
        保存用户地址数据
        """
        # 检查用户地址数据数目不能超过上限
        count = request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message': '保存地址数据已达到上限'}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    def perform_destroy(self, instance):
        """
        处理删除
        """
        # 进行逻辑删除
        instance.is_deleted = True
        instance.save()

    @detail_route(methods=['put'])
    def status(self, request, pk=None, address_id=None):
        """
        设置默认地址
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    @detail_route(methods=['put'])
    def title(self, request, pk=None, address_id=None):
        """
        修改标题
        """
        address = self.get_object()
        serializer = AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserBrowsingHistoryView(mixins.CreateModelMixin, GenericAPIView):
    """
    用户浏览历史记录
    """
    # serializer_class = AddUserBrowsingHistorySerializer
    # permission_classes = [IsAuthenticated]
    #
    # def post(self, request):
    #     """
    #     保存
    #     """
    #     return self.create(request)
    def post(self, request, user_id):
        """
        保存
        """
        # 检查user_id是否存在
        try:
            User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'message': '非法用户'}, status=status.HTTP_400_BAD_REQUEST)

        s = AddUserBrowsingHistorySerializer(data=request.data, context={'user_id': user_id})
        s.is_valid(raise_exception=True)
        s.save()
        return Response({'message': 'OK'}, status=status.HTTP_201_CREATED)

    def get(self, request, user_id):
        """
        获取
        """
        # 检查user_id是否存在
        try:
            User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'message': '非法用户'}, status=status.HTTP_400_BAD_REQUEST)

        redis_conn = get_redis_connection("default")
        history = redis_conn.lrange("history_%s" % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT-1)
        skus = []
        for sku_id in history:
            sku = SKU.objects.get(id=sku_id)
            skus.append(sku)

        s = SKUSerializer(skus, many=True)
        return Response(s.data)


class UserAuthorizeView(ObtainJSONWebToken):
    """
    用户认证
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if request.version == 'v1.1':
            # 版本1.1 补充合并购物车
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data.get('user') or request.user
                response = merge_cart_cookie_to_redis(request, user, response)

        return response
