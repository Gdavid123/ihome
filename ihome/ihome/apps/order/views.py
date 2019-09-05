import datetime

from django.shortcuts import render

# Create your views here.
import json

from django import http
from django.shortcuts import render

# Create your views here.
from django.utils import timezone
from django.views.generic.base import View

from house.models import House
from order.models import Order
from ihome.utils.views import LoginRequiredMixin
from user.models import User


class OrderReservationView(LoginRequiredMixin, View):
    """客户预定订单"""

    def post(self, request):
        """
        用户添加订单
        :param request:
        :return:
        """
        # 1.获取前端传入的参数
        json_dict = json.loads(request.body.decode())
        house_id = json_dict.get('house_id')
        sd = json_dict.get('start_date')
        ed = json_dict.get('end_date')
        # 2. 校验参数
        if not all([json_dict, house_id, sd, ed]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 2. 创建订单
        user = request.user
        # 创建时间 : 年月日时分秒
        # ctime = timezone.localtime().strftime('%Y%m%d%H%M%S')
        # 获取房屋信息
        house = House.objects.get(id=house_id)
        t_sd = datetime.datetime.strptime(sd, "%Y-%m-%d")
        t_ed = datetime.datetime.strptime(ed, "%Y-%m-%d")
        days = t_ed - t_sd
        int_days = int(str(days)[0:1])
        order = Order.objects.create(
            user=user,
            house=house,
            begin_date=sd,
            end_date=ed,
            days=int_days,
            house_price=house.price,
            amount=house.price * int_days,
            house_id=house.id,
        )
        order.order_id = order.id
        # 3. 更新房屋数据
        house.room_count -= 1
        house.save()

        if house.room_count == 0:
            return http.HttpResponseForbidden('房源不足')

        # 18. 返回(json)
        return http.JsonResponse({'code': "0",
                                  'errmsg': 'ok',
                                  'data': {'order_id': order.order_id}})

    def get(self, request):
        """
        根据角色类型, 返回对应的结果
        :param request:
        :return:
        """
        role = request.GET.get("role")
        user = request.user
        if role == "custom":

            try:
                # 获取该用户的所有订单
                orders = Order.objects.filter(user_id=user.id).order_by('-id')
                # orders = user.order_set.all()
            except Exception as e:
                return http.JsonResponse({"errmsg": "fail",
                                          "errno": 4101})
            # 拼接返回
            orders_res = []

            # 遍历, 获取每个订单, 拼接参数
            for order in orders:
                house = order.house
                order_dict = {
                    "amount": order.amount,
                    "comment": order.comment,
                    "ctime": order.create_time,
                    "start_date": order.begin_date,
                    "end_date": order.end_date,
                    "days": order.days,
                    "img_url": house.index_image_url,
                    "order_id": order.id,
                    "status": order.status,
                    "title": house.title
                }

                orders_res.append(order_dict)
            return http.JsonResponse({"data": {"orders": orders_res},
                                      "errmsg": "ok",
                                      "errno": "0"})

        if role == "landlord":
            user_houses = user.house_set.all()
            orders = Order.objects.filter(house_id__in=user_houses)

            # 拼接返回
            orders_res = []

            # 遍历, 获取每个订单, 拼接参数
            for order in orders:
                house = order.house
                order_dict = {
                    "amount": order.amount,
                    "comment": order.comment,
                    "ctime": order.create_time,
                    "start_date": order.begin_date,
                    "end_date": order.end_date,
                    "days": order.days,
                    "img_url": house.index_image_url,
                    "order_id": order.id,
                    "status": order.status,
                    "title": house.title
                }

                orders_res.append(order_dict)
            return http.JsonResponse({"data": {"orders": orders_res},
                                      "errmsg": "ok",
                                      "errno": "0"})

    def put(self, request):
        """房东接单操作"""
        json_dict = json.loads(request.body.decode())

        action = json_dict.get("action")
        order_id = json_dict.get("order_id")
        reason = json_dict.get("reason")

        # 保存信息到数据库
        order = Order.objects.get(id=order_id)
        house = order.house
        # 判断action类型
        if action == "accept":
            order.status = Order.ORDER_STATUS_CHOICES[3][0]
            order.save()
            order_res = {
                "comment": order.comment,
                "ctime": order.create_time,
                "days": order.days,
                "start_date": order.begin_date,
                "end_date": order.end_date,
                "img_url": house.index_image_url,
                "order_id": order.id,
                "amount": order.amount,
                "status": order.status,
                "title": house.title
            }
            return http.JsonResponse({"errno": "0",
                                      "errmsg": "ok",
                                      "order_res": order_res})

        elif action == "reject":
            order.status = Order.ORDER_STATUS_CHOICES[6][0]
            order.comment = reason
            order.save()
            order_res = {
                "comment": reason,
                "ctime": order.create_time,
                "days": order.days,
                "start_date": order.begin_date,
                "end_date": order.end_date,
                "img_url": house.index_image_url,
                "order_id": order.id,
                "amount": order.amount,
                "status": order.status,
                "title": house.title
            }
            return http.JsonResponse({"errno": "0",
                                      "errmsg": "ok",
                                      "order_res": order_res})


class OrderCommentView(LoginRequiredMixin, View):
    """评价订单"""

    def put(self, request):
        json_dict = json.loads(request.body.decode())
        comment = json_dict.get("comment")
        order_id = json_dict.get("order_id")
        # 根据order_id获取id
        order = Order.objects.get(id=order_id)
        # house = order.house.get(id=order.house_id)
        order.comment = comment
        order.status = Order.ORDER_STATUS_CHOICES[4][0]
        order.save()
        # order_res = {
        #     "comment": order.comment,
        #     "ctime": order.create_time,
        #     "days": order.days,
        #     "start_date": order.begin_date,
        #     "end_date": order.end_date,
        #     "img_url": house.index_image_url,
        #     "order_id": order.id,
        #     "amount": order.amount,
        #     "status": order.status,
        #     "title": house.title
        # }

        return http.JsonResponse({
            'errno':0,
            'errmsg':'OK'
        })

