from rest_framework.generics import GenericAPIView, CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django_redis import get_redis_connection
from rest_framework.decorators import action
import logging
import re
from rest_framework_jwt.views import ObtainJSONWebToken
from rest_framework.permissions import IsAuthenticated

from .models import User
from . import serializers
from verifications.serializers import ImageCodeCheckSerializer
from meiduo_mall.utils.permissions import IsOwner
from .utils import get_user_by_account
from . import constants
from goods.models import SKU
from goods.serializers import SKUSerializer
from carts.utils import merge_cart_cookie_to_redis


# Create your views here.
logger = logging.getLogger('django')


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


class UserView(CreateAPIView):
    """
    用户注册
    """
    serializer_class = serializers.CreateUserSerializer


class ChangePasswordView(UpdateAPIView):
    """
    用户密码
    """
    queryset = User.objects.all()
    permission_classes = [IsOwner]
    serializer_class = serializers.ChangePasswordSerializer


class UserDetailView(RetrieveAPIView):
    """
    用户详情
    """
    serializer_class = serializers.UserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class EmailView(CreateAPIView):
    """
    保存用户邮箱
    """
    permission_classes = [IsAuthenticated]

    # 为了让视图的create方法在对序列化器进行save操作时执行序列化器的update方法，更新user的email属性
    # 所以重写get_serializer方法，在构造序列化器时将请求的user对象传入
    # 注意：在视图中，可以通过视图对象self中的request属性获取请求对象
    def get_serializer(self, *args, **kwargs):
        return serializers.EmailSerializer(self.request.user, data=self.request.data)


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


class AddressViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, GenericViewSet):
    """
    用户地址新增与修改
    """
    serializer_class = serializers.UserAddressSerializer
    permissions = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    def list(self, request, *args, **kwargs):
        """
        用户地址列表数据
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
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

    def destroy(self, request, *args, **kwargs):
        """
        处理删除
        """
        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['put'], detail=True)
    def status(self, request, pk=None, address_id=None):
        """
        设置默认地址
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    @action(methods=['put'], detail=True)
    def title(self, request, pk=None, address_id=None):
        """
        修改标题
        """
        address = self.get_object()
        serializer = serializers.AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserBrowsingHistoryView(mixins.CreateModelMixin, GenericAPIView):
    """
    用户浏览历史记录
    """
    serializer_class = serializers.AddUserBrowsingHistorySerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        保存
        """
        return self.create(request)

    def get(self, request):
        """
        获取
        """
        user_id = request.user.id

        redis_conn = get_redis_connection("history")
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
        # 调用父类的方法，获取drf jwt扩展默认的认证用户处理结果
        response = super().post(request, *args, **kwargs)

        # 仿照drf jwt扩展对于用户登录的认证方式，判断用户是否认证登录成功
        # 如果用户登录认证成功，则合并购物车
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data.get('user')
            response = merge_cart_cookie_to_redis(request, user, response)

        return response
