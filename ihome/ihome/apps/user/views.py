import json
import random
import re

from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.views import View
from django_redis import get_redis_connection
from pymysql import DatabaseError

from ihome.libs.captcha.captcha import captcha
from ihome.utils.fastdfs.fastdfs_storage import FastDFSStorage
from ihome.utils.response_code import RET
from ihome.utils.views import LoginRequiredMixin
from user.models import User
import logging
from django.conf import settings
logger = logging.getLogger('django')


class RegisterView(View):
    """用户注册"""

    def get(self, request):
        """
        提供注册界面
        :param request: 请求对象
        :return: 注册界面
        """
        return render(request, 'register.html')

    def post(self, request):
        """注册"""
        json_dict = json.loads(request.body)
        mobile = json_dict.get('mobile')
        phonecode = json_dict.get('phonecode')
        password = json_dict.get('password')
        password2 = json_dict.get('password2')


        if not all([mobile, phonecode, password, password2]):
            return JsonResponse({
            'errno': RET.DATAERR,
            'errmsg': "缺少必传参数"
        })

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({
            'errno': RET.DATAERR,
            'errmsg': "请输入正确手机号"
        })


        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_code_%s' % mobile)
        if sms_code_server is None:
            return render(request, 'register.html', {'sms_code_errmsg': '无效的短信验证码'})

        if phonecode != sms_code_server.decode():
            return render(request, 'register.html', {'sms_code_errmsg': '输入短信验证码有误'})

        if not re.match(r'[0-9A-Za-z]{6,20}$', password):
            return JsonResponse({
            'errno': RET.DATAERR,
            'errmsg': "请输入6-20位密码"
        })


        if password != password2:
            return JsonResponse({
            'errno': RET.DATAERR,
            'errmsg': "两次密码输入不一致"
        })


        try:
            user = User.objects.create_user(username=mobile, password=password,mobile=mobile)
        except DatabaseError:
            return JsonResponse({
            'errno': RET.DATAERR,
            'errmsg': "注册失败"
        })


        login(request, user)

        return JsonResponse({
            'errno': RET.OK,
            'errmsg': "注册成功"
        })


class ImageCodeView(View):
    """图片验证码"""

    def get(self, request):
        cur = request.GET.get('cur')
        pre = request.GET.get('pre')

        text, image = captcha.generate_captcha()

        redis_conn = get_redis_connection('verify_code')

        redis_conn.setex('img_%s' % cur, 300, text)

        return HttpResponse(image, content_type='image/jpg')


class SMSCodeView(View):
    """手机验证码"""

    def post(self, request):
        json_dict = json.loads(request.body)
        mobile = json_dict.get('mobile')
        image_code = json_dict.get('image_code')
        image_code_id = json_dict.get('image_code_id')

        redis_conn = get_redis_connection('verify_code')

        flag = redis_conn.get('send_flag_%s' % mobile)
        if flag:
            return JsonResponse({
                'code': 0,
                'errmsg': '发送短信过于频繁'
            })

        if not all([mobile, image_code, image_code_id]):
            return JsonResponse({
                'code': RET.NODATA,
                'errmsg': '缺少必传参数'
            })

        image_code_server = redis_conn.get('img_%s' % image_code_id)

        if image_code_server is None:
            return JsonResponse({
                'code': RET.DATAERR,
                'errmsg': '图形验证码失效'
            })

        try:
            redis_conn.delete('img_%s' % image_code_id)
        except Exception as e:
            logger.error(e)

        image_code_server = image_code_server.decode()

        if image_code.lower() != image_code_server.lower():
            return JsonResponse({
                'code': RET.DATAERR,
                'errmsg': '输入图形验证码有误'
            })

        sms_code = '%06d' % random.randint(0, 999999)
        logger.info(sms_code)

        pl = redis_conn.pipeline()

        pl.setex('sms_code_%s' % mobile, 300, sms_code)
        pl.setex('send_flag_%s' % mobile, 60, 1)

        pl.execute()

        return JsonResponse({
            'code': RET.OK,
            'errmsg': '发送短信成功'
        })


class Login(View):
    """登录"""

    def post(self, request):
        json_dict = json.loads(request.body)
        mobile = json_dict.get('mobile')
        password = json_dict.get('password')

        if not all([mobile, password]):
            return JsonResponse({
            'errno': RET.DATAERR,
            'errmsg': "缺少必传参数"
        })



        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({
            'errno': RET.DATAERR,
            'errmsg': "请输入正确手机号"
        })


            # 判断密码是否是6-20个数字
        if not re.match(r'^[0-9A-Za-z]{6,20}$', password):
            return JsonResponse({
            'errno': RET.DATAERR,
            'errmsg': "请输入6-20位密码"
        })


            # 认证登录用户
        user = authenticate(username=mobile, password=password)
        if user is None:
            return JsonResponse({
            'errno': RET.DATAERR,
            'errmsg': "用户名或密码不正确"
        })



        # 实现状态保持
        login(request, user)

        return JsonResponse({
            'errno': RET.OK,
            'errmsg': "登录成功"
        })



class Session(View):

    def get(self,request):
        user = request.user

        if not user:
            return JsonResponse({
                'errno': 4101,
                'errmsg': "未登录"
            })

        return JsonResponse({
                'errno': 0,
                'errmsg': "OK",
                'data':{"user_id": user.id, "name": user.username}
            })


class Logout(View):

    def delete(self,request):
        user = request.user

        if not user:
            return JsonResponse({
                'errno': RET.SESSIONERR,
                'errmsg': "用户未登录"
            })


        logout(request)

        return JsonResponse({
            'errno': RET.OK,
            'errmsg': "用户已退出",
        })


class user_profile(LoginRequiredMixin,View):
    def get(self,request):
        user = request.user

        return JsonResponse({
            'errno': RET.OK,
            'errmsg': "OK",
            'data':{
                'name':user.username,
                'avatar_url':user.avatar_url,
                'mobile':user.mobile
            }
        })

    def post(self,request):
        json_dict = json.loads(request.body)
        name = json_dict.get('name')

        user = request.user

        if not name:
            return JsonResponse({
                'errno': RET.DATAERR,
                'errmsg': "参数校验失败",
            })

        try:
            new_name_user = User.objects.filter(id=user.id).update(username=name)
        except DatabaseError:
            return JsonResponse({
                'errno': RET.DATAERR,
                'errmsg': "修改失败",
            })


        return JsonResponse({
            'errno': 0,
            'errmsg': "保存成功",
        })



class avatar(LoginRequiredMixin,View):
    def post(self,request):
        avatar = request.FILES.get('avatar')
        file_id = FastDFSStorage.save(self,name='',content=avatar)
        avatar_url = settings.FDFS_URL + file_id

        user = request.user

        try:
            new_user = User.objects.filter(id=user.id).update(avatar_url=avatar_url)
        except DatabaseError:
            return JsonResponse({
                'errno': RET.DATAERR,
                'errmsg': "上传失败",
            })

        return JsonResponse({
            'errno': RET.OK,
            'errmsg': "OK",
            'data': {
                'avatar_url': user.avatar_url,
            }
        })


class Auth(LoginRequiredMixin,View):
    def post(self,request):
        user = request.user
        json_dict = json.loads(request.body)
        real_name = json_dict.get('real_name')
        id_card = json_dict.get('id_card')

        try:
            new_user = User.objects.filter(id=user.id).update(real_name=real_name,id_card=id_card)
        except DatabaseError:
            return JsonResponse({
                'errno': RET.DATAERR,
                'errmsg': "修改失败",
            })

        return JsonResponse({
            'errno': RET.OK,
            'errmsg': "OK"
        })

    def get(self,request):
        user = request.user

        return JsonResponse({
            'errno':0,
            'errmsg':'success',
            'data':{
                'real_name':user.real_name,
                'id_card':user.id_card
            }
        })