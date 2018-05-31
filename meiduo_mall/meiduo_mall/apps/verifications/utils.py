from rest_framework.response import Response
from django_redis import get_redis_connection
from rest_framework import status
from redis.exceptions import RedisError
import logging


logger = logging.getLogger('django')


def check_image_code(request):
    """检验图片验证码"""
    # 检验图片验证码
    image_code_id = request.query_params.get('codeId')
    image_code_text = request.query_params.get('text')
    if not all([image_code_id, image_code_text]):
        return Response({"message": "缺少图片验证码"}, status=status.HTTP_400_BAD_REQUEST)

    redis_conn = get_redis_connection("verify_codes")
    try:
        real_image_code_text = redis_conn.get("img_%s" % image_code_id)
    except RedisError as e:
        logger.error(e)
        return Response({"message": "服务器内部错误"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 图片验证码不存在或者已过期
    if not real_image_code_text:
        return Response({"message": "无效的图片验证码"}, status=status.HTTP_400_BAD_REQUEST)

    # 删除图片验证码
    try:
        redis_conn.delete("img_%s" % image_code_id)
    except RedisError as e:
        logger.error(e)

    # 比较图片验证码是否正确
    real_image_code_text = real_image_code_text.decode()
    if real_image_code_text.lower() != image_code_text.lower():
        return Response({"message": "图片验证码错误"}, status=status.HTTP_400_BAD_REQUEST)