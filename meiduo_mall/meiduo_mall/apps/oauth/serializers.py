from rest_framework import serializers
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings

from .utils import OAuthQQ
from users.models import User
from .models import OAuthQQUser


# 课件老版本
# class OAuthQQUserSerializer(serializers.Serializer):
#     """
#     QQ登录创建用户序列化器
#     """
#     access_token = serializers.CharField(label='操作凭证')
#     mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')
#     password = serializers.CharField(label='密码', max_length=20, min_length=8)
#     sms_code = serializers.CharField(label='短信验证码')
#
#     def validate(self, data):
#         # 检验access_token
#         access_token = data['access_token']
#         openid = OAuthQQ.check_save_user_token(access_token)
#         if not openid:
#             raise serializers.ValidationError('无效的access_token')
#
#         data['openid'] = openid
#
#         # 检验短信验证码
#         mobile = data['mobile']
#         sms_code = data['sms_code']
#         redis_conn = get_redis_connection('verify_codes')
#         real_sms_code = redis_conn.get('sms_%s' % mobile)
#         if real_sms_code.decode() != sms_code:
#             raise serializers.ValidationError('短信验证码错误')
#
#         # 如果用户存在，检查用户密码
#         try:
#             user = User.objects.get(mobile=mobile)
#         except User.DoesNotExist:
#             pass
#         else:
#             password = data['password']
#             if not user.check_password(password):
#                 raise serializers.ValidationError('密码错误')
#             data['user'] = user
#         return data
#
#     def create(self, validated_data):
#         user = validated_data.get('user')
#         if not user:
#             # 用户不存在
#             user = User.objects.create_user(
#                 username=validated_data['mobile'],
#                 password=validated_data['password'],
#                 mobile=validated_data['mobile'],
#             )
#
#         OAuthQQUser.objects.create(
#             openid=validated_data['openid'],
#             user=user
#         )
#         return user

class OAuthQQUserSerializer(serializers.ModelSerializer):
    sms_code = serializers.CharField(label='短信验证码', write_only=True)
    access_token = serializers.CharField(label='操作凭证', write_only=True)
    token = serializers.CharField(read_only=True)
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')

    class Meta:
        model = User
        fields = ('mobile', 'password', 'sms_code', 'access_token', 'id', 'username', 'token')
        extra_kwargs = {
            'username': {
                'read_only': True
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }

    def validate(self, attrs):
        # 检验access_token
        access_token = attrs['access_token']

        openid = OAuthQQ.check_save_user_token(access_token)
        if not openid:
            raise serializers.ValidationError('无效的access_token')

        attrs['openid'] = openid

        # 检验短信验证码
        mobile = attrs['mobile']
        sms_code = attrs['sms_code']
        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code.decode() != sms_code:
            raise serializers.ValidationError('短信验证码错误')

        # 如果用户存在，检查用户密码
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            pass
        else:
            password = attrs['password']
            if not user.check_password(password):
                raise serializers.ValidationError('密码错误')
            attrs['user'] = user
        return attrs

    def create(self, validated_data):
        openid = validated_data['openid']
        user = validated_data.get('user')
        mobile = validated_data['mobile']
        password = validated_data['password']

        if not user:
            # 如果用户不存在，创建用户，绑定openid（创建了OAuthQQUser数据）
            user = User.objects.create_user(username=mobile, mobile=mobile, password=password)

        OAuthQQUser.objects.create(user=user, openid=openid)

        # 签发jwt token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        user.token = token

        # 向视图对象中补充user对象属性，以便在视图中使用user
        self.context['view'].user = user

        return user