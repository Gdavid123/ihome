from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View

from address.models import Area
from ihome.utils.response_code import RET


class AreaView(View):

    def get(self,request):
        try:
            areas = Area.objects.all()
        except Exception as e:
            return JsonResponse({
                'errno':RET.DBERR,
                'errmsg':'获取参数失败'
            })

        data = []
        for area in areas:
            data_dict = {
                'aid':area.id,
                'aname':area.name
            }

            data.append(data_dict)

        return JsonResponse({
            'data':data,
            'errno':RET.OK,
            'errmsg':'OK'
        })