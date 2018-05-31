from django.conf.urls import url
from rest_framework import routers
from rest_framework_jwt.views import obtain_jwt_token

from . import views


router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet, base_name='user')
router.register(r'users/(?P<pk>\d+)/addresses', views.UserAddressViewSet, base_name='user_address')


urlpatterns = [
    url(r'usernames/(?P<username>\w{5,20})/count/', views.UsernameCountView.as_view(), name='username_count'),
    url(r'mobiles/(?P<mobile>1[345789]\d{9})/count/', views.MobileCountView.as_view(), name='mobile_count'),
    # url(r'authorizations/', obtain_jwt_token, name='authorizations'),
    url(r'authorizations/', views.UserAuthorizeView.as_view(), name='authorizations'),
    url(r'accounts/(?P<account>\w{5,20})/sms/token/', views.SMSTokenView.as_view(), name='sms_token'),
    url(r'accounts/(?P<account>\w{5,20})/password/token/', views.PasswordTokenView.as_view(), name='password_token'),
    url(r'users/(?P<pk>\d+)/password/', views.PasswordViewSet.as_view({'post': 'create', 'put': 'update'}), name='password'),
    url(r'emails/verification/', views.VerifyEmailView.as_view(), name='verify_email'),
    url(r'users/(?P<user_id>\d+)/histories/', views.UserBrowsingHistoryView.as_view(), name='browsing_history'),
]

urlpatterns += router.urls
