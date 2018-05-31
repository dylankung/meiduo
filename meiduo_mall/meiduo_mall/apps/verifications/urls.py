from django.conf.urls import url
from . import views


urlpatterns = [
    url('^images/(?P<code_id>[\w-]+).jpg$', views.ImageCodeView.as_view(), name='image_code'),
    url('^sms/(?P<mobile>1[345789]\d{9})/$', views.SMSCodeView.as_view(), name='sms_code'),
    url('^sms/$', views.SMSCodeByTokenView.as_view(), name='token_sms_code'),
]