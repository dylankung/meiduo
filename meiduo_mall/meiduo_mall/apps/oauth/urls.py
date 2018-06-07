from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^qq/authorization/$', views.QQAuthURLView.as_view()),  # 获取QQ登录链接url
    url(r'^qq/user/$', views.QQAuthUserView.as_view())  # 获取QQ登录的用户
]