from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from . import views

urlpatterns = [
    url(r'^orders/settlement/$', views.OrderSettlementView.as_view(), name='settlement'),
    url(r'^orders/(?P<order_id>\d+)/uncommentgoods/$', views.UncommentOrderGoodsView.as_view(), name='uncomment_goods'),
    url(r'^orders/(?P<order_id>\d+)/comments/$', views.OrderCommentView.as_view(), name='save_comment'),
]

router = DefaultRouter()
router.register(r'orders', views.OrderViewSet, base_name='orders')

urlpatterns += router.urls
