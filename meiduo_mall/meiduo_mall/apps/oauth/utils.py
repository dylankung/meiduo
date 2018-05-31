from urllib.parse import urlencode, parse_qs
from urllib.request import urlopen
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from django.conf import settings
import json
import logging

from . import constants
from .exceptions import QQAPIError


logger = logging.getLogger('django')


class OAuthQQ(object):
    """
    QQ认证辅助工具类
    """
    def __init__(self, app_id=None, app_key=None, redirect_uri=None, state=None):
        self.app_id = app_id or settings.QQ_APP_ID
        self.app_key = app_key or settings.QQ_APP_KEY
        self.redirect_url = redirect_uri or settings.QQ_REDIRECT_URL
        self.state = state or '/'  # 用于保存登录成功后的跳转页面路径

    def get_auth_url(self):
        """
        获取qq登录的网址
        :return: url网址
        """
        params = {
            'response_type': 'code',
            'client_id': self.app_id,
            'redirect_uri': self.redirect_url,
            'state': self.state,
            'scope': 'get_user_info',
        }
        url = 'https://graph.qq.com/oauth2.0/authorize?' + urlencode(params)
        return url

    def get_access_token(self, code):
        """
        获取access_token
        :param code: qq提供的code
        :return: access_token
        """
        params = {
            'grant_type': 'authorization_code',
            'client_id': self.app_id,
            'client_secret': self.app_key,
            'code': code,
            'redirect_uri': self.redirect_url
        }
        url = 'https://graph.qq.com/oauth2.0/token?' + urlencode(params)
        response = urlopen(url)
        response_data = response.read().decode()
        data = parse_qs(response_data)
        access_token = data.get('access_token', None)
        if not access_token:
            logger.error('code=%s msg=%s' % (data.get('code'), data.get('msg')))
            raise QQAPIError

        return access_token[0]

    def get_openid(self, access_token):
        """
        获取用户的openid
        :param access_token: qq提供的access_token
        :return: open_id
        """
        url = 'https://graph.qq.com/oauth2.0/me?access_token=' + access_token
        response = urlopen(url)
        response_data = response.read().decode()
        try:
            # 返回的数据 callback( {"client_id":"YOUR_APPID","openid":"YOUR_OPENID"} )\n;
            data = json.loads(response_data[10:-4])
        except Exception:
            data = parse_qs(response_data)
            logger.error('code=%s msg=%s' % (data.get('code'), data.get('msg')))
            raise QQAPIError
        openid = data.get('openid', None)
        return openid

    @staticmethod
    def generate_save_user_token(openid):
        """
        生成保存用户数据的token
        :param openid: 用户的openid
        :return: token
        """
        serializer = Serializer(settings.SECRET_KEY, expires_in=constants.SAVE_QQ_USER_TOKEN_EXPIRES)
        data = {'openid': openid}
        token = serializer.dumps(data)
        return token.decode()

    @staticmethod
    def check_save_user_token(token):
        """
        检验保存用户数据的token
        :param token: token
        :return: openid or None
        """
        serializer = Serializer(settings.SECRET_KEY, expires_in=constants.SAVE_QQ_USER_TOKEN_EXPIRES)
        try:
            data = serializer.loads(token)
        except BadData:
            return None
        else:
            return data.get('openid')

