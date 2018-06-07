from django.conf.urls import url
from rest_framework import routers
from rest_framework_jwt.views import obtain_jwt_token

from . import views


urlpatterns = [
    url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),  # 用户名数量
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),  # 手机号数量
    url(r'^users/$', views.UserView.as_view()),  # 注册
    # url(r'^authorizations/$', obtain_jwt_token),  # 登录
    url(r'^authorizations/$', views.UserAuthorizeView.as_view()),  # 登录
    url(r'^accounts/(?P<account>\w{5,20})/sms/token/$', views.SMSTokenView.as_view()),  # 获取发送短信的token
    url(r'^accounts/(?P<account>\w{5,20})/password/token/$', views.PasswordTokenView.as_view()),  # 获取修改密码的token
    url(r'^users/(?P<pk>\d+)/password/$', views.PasswordViewSet.as_view({'post': 'create', 'put': 'update'})),  # 修改密码
    url(r'^user/$', views.UserDetailView.as_view()),  # 用户基本信息
    url(r'^emails/$', views.EmailView.as_view()),  # 设置邮箱
    url(r'^emails/verification/$', views.VerifyEmailView.as_view()),  # 邮箱验证
    url(r'^browse_histories/$', views.UserBrowsingHistoryView.as_view()),  # 浏览历史记录
]

router = routers.DefaultRouter()
router.register(r'addresses', views.AddressViewSet, base_name='addresses')

urlpatterns += router.urls
