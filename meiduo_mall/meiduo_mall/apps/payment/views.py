from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from alipay import AliPay
import time
import os

from orders.models import OrderInfo
from .models import Payment

# Create your views here.


class PaymentView(APIView):
    """
    支付
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, order_id):
        """
        创建支付
        """
        # 判断订单信息是否正确
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=request.user,
                                          pay_method=OrderInfo.PAY_METHODS_ENUM["ALIPAY"],
                                          status=OrderInfo.ORDER_STATUS_ENUM["UNPAID"])
        except OrderInfo.DoesNotExist:
            return Response({'message': '订单信息有误'}, status=status.HTTP_400_BAD_REQUEST)

        # 构造支付宝支付链接地址
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/alipay_public_key.pem"),  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )

        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject="美多商城%s" % order_id,
            return_url="http://www.meiduo.site:8080/pay_success.html",
        )
        alipay_url = settings.ALIPAY_URL + "?" + order_string
        return Response({'alipay_url': alipay_url}, status=status.HTTP_201_CREATED)

    # def get(self, request, order_id):
    #     """
    #     查询支付结果
    #     """
    #     # 判断订单信息是否正确
    #     try:
    #         order = OrderInfo.objects.get(order_id=order_id, user=request.user,
    #                                       pay_method=OrderInfo.PAY_METHODS_ENUM["ALIPAY"],
    #                                       status=OrderInfo.ORDER_STATUS_ENUM["UNPAID"])
    #     except OrderInfo.DoesNotExist:
    #         return Response({'message': '订单信息有误'}, status=status.HTTP_400_BAD_REQUEST)
    #
    #     # 构造支付宝支付链接地址
    #     alipay = AliPay(
    #         appid=settings.ALIPAY_APPID,
    #         app_notify_url=None,  # 默认回调url
    #         app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
    #                                           "keys/app_private_key.pem"),
    #         alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
    #                                             "keys/alipay_public_key.pem"),  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
    #         sign_type="RSA2",  # RSA 或者 RSA2
    #         debug=settings.ALIPAY_DEBUG  # 默认False
    #     )
    #
    #     # 查询支付结果
    #     while True:
    #         result = alipay.api_alipay_trade_query(order_id)
    #         print(result)
    #         trade_status = result.get("trade_status")
    #         if result.get("code") != "10000" or trade_status == "WAIT_BUYER_PAY":
    #             time.sleep(10)
    #             continue
    #         elif trade_status == "TRADE_SUCCESS":
    #             order.status = OrderInfo.ORDER_STATUS_ENUM["UNCOMMENT"]
    #             order.save()
    #             trade_no = result.get('trade_no')
    #             Payment.objects.create(
    #                 order=order,
    #                 trade_id=trade_no
    #             )
    #             return Response({'message': 'success', 'trade_no': trade_no})
    #         else:
    #             return Response({'message': 'fail'})


class PaymentStatusView(APIView):
    """
    支付结果
    """
    def put(self, request):
        data = request.query_params.dict()
        signature = data.pop("sign")

        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "keys/alipay_public_key.pem"),  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )

        success = alipay.verify(data, signature)
        if success:
            # 订单编号
            order_id = data.get('out_trade_no')
            # 支付宝支付流水号
            trade_id = data.get('trade_no')
            Payment.objects.create(
                order_id=order_id,
                trade_id=trade_id
            )
            OrderInfo.objects.filter(order_id=order_id).update(status=OrderInfo.ORDER_STATUS_ENUM["UNCOMMENT"])
            return Response({'trade_id': trade_id})
        else:
            return Response({'message': '参数错误'}, status=status.HTTP_400_BAD_REQUEST)