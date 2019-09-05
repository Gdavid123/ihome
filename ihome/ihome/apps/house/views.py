import datetime
import json

from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View
from pymysql import DatabaseError

from house.models import House, Facility, HouseImage
from ihome.utils.fastdfs.fastdfs_storage import FastDFSStorage
from ihome.utils.response_code import RET
from ihome.utils.views import LoginRequiredMixin


class Search(View):
    def get(self,request):
        aid = request.GET.get('aid')
        sd = request.GET.get('sd')
        ed = request.GET.get('ed')
        sk = request.GET.get('sk')
        p = request.GET.get('p',1)

        t_sd = datetime.datetime.strptime(sd,"%Y-%m-%d")
        t_ed = datetime.datetime.strptime(ed,"%Y-%m-%d")
        days = t_ed - t_sd
        int_days = int(str(days)[0:1])
        houses = []

        if sk == 'booking':
            area_houses = House.objects.filter(area_id=aid,min_days__lte=int_days,max_days__gte=int_days).order_by('-order_count')

        if sk == 'new':
            area_houses = House.objects.filter(area_id=aid, min_days__lte=int_days, max_days__gte=int_days).order_by('-create_time')

        if sk == 'price-inc':
            area_houses = House.objects.filter(area_id=aid, min_days__lte=int_days, max_days__gte=int_days).order_by('price')

        if sk == 'price-des':
            area_houses = House.objects.filter(area_id=aid, min_days__lte=int_days, max_days__gte=int_days).order_by('-price')

        for house in area_houses:
            house_dict = {
                'address':house.address,
                'area_name':house.area.name,
                'ctime':house.create_time,
                'house_id':house.id,
                'img_url':house.index_image_url,
                'order_count':house.order_count,
                'price':house.price,
                'room_count':house.room_count,
                'title':house.title,
                'user_avatar':house.user.avatar_url
            }
            houses.append(house_dict)


        page_num = int(p)
        try:
            paginator = Paginator(houses,1)
            page_house = paginator.page(page_num)
            total_page = paginator.num_pages
        except Exception as e:
            return HttpResponseForbidden('分页失败')

        return JsonResponse({
            'data':{
                'houses':houses,
                'total_page':total_page
            },
            'errmsg':'请求成功',
            'errno': 0
        })



class Index(View):
    def get(self,request):
        houses = House.objects.all().order_by('?')[:5]

        data = []
        for house in houses:
            house_dict = {
                'house_id':house.id,
                'img_url':house.index_image_url,
                'title':house.title
            }
            data.append(house_dict)


        return JsonResponse({
            'data':data,
            'errmsg':'OK',
            'errno': 0
        })


class HousesView(LoginRequiredMixin, View):

    def get(self,request,house_id):
        try:
            house_detail = House.objects.get(id=house_id)
            # 房屋所有的图片对象
            house_imgs = house_detail.houseimage_set.filter(house_id=house_id)
            owner = house_detail.user
            orders = house_detail.order_set.filter(house_id=house_id)
            facilities = house_detail.facilities.all()
            acreage = int(house_detail.acreage)
            address = str(house_detail.address)
            beds = str(house_detail.beds)
            capacity = house_detail.capacity
            deposit = house_detail.deposit
            max_days = int(house_detail.max_days)
            min_days = int(house_detail.min_days)
            price = int(house_detail.price)
            room_count = int(house_detail.room_count)
            title = str(house_detail.title)
            unit = str(house_detail.unit)

        except:
            return JsonResponse({'errno': RET.DBERR, "errmsg": '数据库错误'})
        house_img_list = []
        comments_list = []
        facility_list = []
        for house_img in house_imgs:
            house_img_list.append(house_img.url)
        for order in orders:
            comments_dict = {
                "comment": order.comment,
                "ctime": order.create_time,
                "user_name": order.user.username,
            }

            comments_list.append(comments_dict)

        for facility in facilities:
            facility_list.append(int(facility.id))


        house = {
            "acreage": acreage,
            "address": address,
            "beds": beds,
            "capacity": capacity,
            "comments": comments_list,
            "deposit": deposit,
            "facilities": facility_list,
            "hid": house_id,
            "img_urls": house_img_list,
            "max_days": max_days,
            "min_days": min_days,
            "price": price,
            "room_count": room_count,
            "title": title,
            "unit": unit,
            "user_avatar": owner.avatar_url,
            "user_id": owner.id,
            "user_name": owner.username
        }
        data = {
            "house": house,
            'user_id': request.user.id
        }

        return JsonResponse({'errno': RET.OK, "errmsg": "OK", 'data': data})

    def post(self, request):
        '''
        发布新房源API
        :param request:
        :return: json
        '''
        json_dict = json.loads(request.body)
        title = json_dict.get('title')
        price = json_dict.get('price')
        area_id = json_dict.get('area_id')
        address = json_dict.get('address')
        room_count = json_dict.get('room_count')
        acreage = json_dict.get('acreage')
        unit = json_dict.get('unit')
        capacity = json_dict.get('capacity')
        beds = json_dict.get('beds')
        deposit = json_dict.get('deposit')
        min_days = json_dict.get('min_days')
        max_days = json_dict.get('max_days')
        if not all([title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days,
                    max_days]):
            return JsonResponse({'errno': RET.PARAMERR, 'errmsg': '参数缺失'})
        # 获取登录用户

        user = request.user
        # 写入数据
        try:
            house = House.objects.create(
                title=title,
                price=price,
                area_id=area_id,
                address=address,
                room_count=room_count,
                acreage=acreage,
                unit=unit,
                capacity=capacity,
                beds=beds,
                deposit=deposit,
                min_days=min_days,
                max_days=max_days,
                user_id=user.id,
            )
        except Exception as e:
            return JsonResponse({'errno': RET.DBERR, 'errmsg': '插入数据时出错'})

        facilities = json_dict.get('facility')
        facilities = Facility.objects.filter(id__in=facilities)
        house.facilities.add(*facilities)

        try:
            house.save()
        except Exception as e:
            return JsonResponse({'errno': RET.DBERR, 'errmsg': '数据保存时出错'})
        return JsonResponse({'errno': RET.OK, 'errmsg': "Ok", 'data': {"house_id": house.id}})



class HousesImageView(LoginRequiredMixin, View):
    def post(self, request, house_id):
        house_image = request.FILES.get('house_image')
        file_id = FastDFSStorage.save(self, name='', content=house_image)
        house_image_url = settings.FDFS_URL + file_id

        user = request.user

        try:
            index_image_url = House.objects.filter(id=house_id).update(index_image_url=house_image_url)
            HouseImage.objects.create(house_id=house_id,
                                      url=house_image_url)
        except DatabaseError:
            return JsonResponse({
                'errno': RET.DATAERR,
                'errmsg': "上传失败",
            })

        return JsonResponse({'errno': RET.OK, 'errmsg': "OK", 'data': {"url": house_image_url}})



class MyHouses(View):

    def get(self, request):
        # 获取user
        user = request.user
        # 获取我发布的房源
        user_house_info = user.house_set.all().order_by('-create_time')


        # 创建data列表
        data = []
        # 迭代数据对象获取数据
        for house in user_house_info:
            image_list = list(house.houseimage_set.all().order_by('-id'))
            img_url = image_list[0].url

            data_dict = {
                'address': house.address,
                'area_name': house.area.name,
                'ctime': house.create_time.strftime('%Y-%m-%d'),
                'house_id': house.id,
                'img_url': img_url,
                'order_count': house.order_count,
                'price': house.price,
                'room_count': house.room_count,
                'title': house.title,
                'user_avatar': user.avatar_url,
            }
            data.append(data_dict)
        return JsonResponse({'errno': RET.OK, 'errmsg': 'OK', 'data': data})